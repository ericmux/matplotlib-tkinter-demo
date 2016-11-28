#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import Queue
import time
import numpy as np
from threading import Thread

import matplotlib

matplotlib.use('TkAgg')

from numpy import arange
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as pyplot
import matplotlib.animation as animation
import Tkinter as Tk

# ##################################################################################################
# # Data classes
# ##################################################################################################

class SensorStream:
    MAX_MEASURES = 30

    def __init__(self, id):
        self.id = id
        self.times = []
        self.measures = []
        self.avg_measures = []

    def add_measure(self, t, v):
        if len(self.times) == SensorStream.MAX_MEASURES:
            self.times.pop(0)
            self.measures.pop(0)
            self.avg_measures.pop(0)
        self.times.append(t)
        self.measures.append(v)
        self.avg_measures.append(np.average(self.measures))


class DataCollector:
    def __init__(self, q, rate, sample_rates):
        self.q = q
        self.time = 0
        self.rate = rate
        self.sample_rates = sample_rates
        self.sample_now = False

    def poll(self):
        try:
            read_data = self.q.get_nowait()
            # give answer in milliseconds.
            measurements = []
            for i in range(len(read_data)):
                if not self.sample_now:
                    if self.time % self.sample_rates[i] == 0:
                        measurements.append((1000 * self.time, read_data[i]))
                    else:
                        measurements.append(None)
                else:
                    measurements.append((1000 * self.time, read_data[i]))
            self.time += self.rate
            self.sample_now = False
            return measurements
        except Queue.Empty:
            return False


class DataGenerator(Thread):
    def __init__(self, rate):
        super(DataGenerator, self).__init__()
        self.rate = rate
        self.q = Queue.Queue()
        self.time = time.time()

    def run(self):
        self.time = time.time()
        while True:
            elapsed_time = time.time() - self.time
            self.time += elapsed_time
            if elapsed_time > self.rate:
                self.q.put([np.random.random() for i in xrange(3)])
            else:
                time.sleep(self.rate - elapsed_time)


# ##################################################################################################
# UI classes
# ##################################################################################################

# refresh rate in milliseconds.
REFRESH_RATE = 1000


class SensorMonitor:
    def __init__(self, axes, stream, title, ylabel):
        self.axes = axes
        self.stream = stream
        self.title = title
        self.lines, = self.axes.plot(self.stream.times, self.stream.measures, 'blue')
        self.avg_lines, = self.axes.plot(self.stream.times, self.stream.avg_measures, 'red')
        self.refresh_rate = REFRESH_RATE

        self.axes.set_title(self.title)
        self.axes.set_xticklabels([])
        self.axes.set_yticklabels([])
        self.axes.set_ylabel(ylabel)
        self.axes.set_xlabel('Tempo (s)')

        self.axes.spines['bottom'].set_color('white')
        self.axes.spines['top'].set_color('white')
        self.axes.spines['left'].set_color('white')
        self.axes.spines['right'].set_color('white')
        self.axes.set_axis_bgcolor('black')

        self.axes.tick_params(axis='x', colors='white', width=2)
        self.axes.tick_params(axis='y', colors='white', width=2)

        if not len(self.stream.times) > 0:
            return

    def set_ylim(self, y_min, y_max):
        self.axes.set_ylim(y_min, y_max)

    def update_data(self, data):
        self.stream.add_measure(data[0], data[1])
        self.lines.set_data(self.stream.times, self.stream.measures)
        self.avg_lines.set_data(self.stream.times, self.stream.avg_measures)

        if not len(self.stream.times) > 0:
            return

        self.adjust_limits()

    def get_animated_lines(self):
        return [self.lines, self.avg_lines]

    def adjust_limits(self):
        if not len(self.stream.times) > 0:
            return

        new_range = range(self.stream.times[0], self.stream.times[0] + SensorStream.MAX_MEASURES * self.refresh_rate,
                          self.refresh_rate)
        self.axes.set_xlim(new_range[0], new_range[-1])
        ticks = [x for x in new_range if x % self.refresh_rate == 0]
        self.axes.set_xticks(ticks)
        self.axes.set_xticklabels([str(x / 1000) for x in ticks])


class MuxaGet(Tk.Tk):
    def __init__(self, *args, **kwargs):
        Tk.Tk.__init__(self, *args, **kwargs)

        # Air Temperature sensor stream.
        self.air_t_stream = SensorStream(0)

        # Air humidity sensor stream.
        self.air_h_stream = SensorStream(1)

        # Soil humidity sensor stream.
        self.soil_h_stream = SensorStream(2)


        # Set title.
        self.wm_title("Sistema de Monitoramento MuxaGet")

        self.figure = Figure(figsize=(12, 6.5), dpi=100)
        self.figure.subplots_adjust(hspace=0.8)
        self.figure.set_facecolor(color='white')

        # a tk.DrawingArea from the figure.
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

        # Subplot monitors for each sensor.
        self.air_t_monitor = SensorMonitor(self.figure.add_subplot(311), self.air_t_stream,
                                           'Sensor de Temperatura do Ambiente', 'Temperatura (°C)')
        self.air_h_monitor = SensorMonitor(self.figure.add_subplot(312), self.air_h_stream, 'Sensor de Umidade do Ar',
                                           'Umidade (Ω)')
        self.soil_h_monitor = SensorMonitor(self.figure.add_subplot(313), self.soil_h_stream,
                                            'Sensor de Umidade do Solo', 'Umidade (Ω)')

        self.air_t_monitor.set_ylim(0, 1)
        self.air_h_monitor.set_ylim(0, 1)
        self.soil_h_monitor.set_ylim(0, 1)


        # Control dashboard.
        self.dashboard = Tk.LabelFrame(master=self, text='Opções')
        self.dashboard.pack(side=Tk.BOTTOM, fill=Tk.BOTH, padx=5, pady=5, expand=1)

        # Sliders to control each sensor's sampling rate.
        def update_rate_for(monitor):
            def update_rate(rate):
                monitor.refresh_rate = int(rate) * 1000
                data_collector.sample_rates[monitor.stream.id] = int(rate)
                monitor.adjust_limits()

            return update_rate


        self.rate_options_frame = Tk.LabelFrame(master=self.dashboard, text='Períodos de Amostragem (s)')

        self.air_t_scale = Tk.Scale(master=self.rate_options_frame, orient='horizontal', label='Temperatura do Meio:', length=200, from_=1, to=10,
                                    command=update_rate_for(self.air_t_monitor))
        self.air_h_scale = Tk.Scale(master=self.rate_options_frame, orient='horizontal', label='Umidade do Ar:', length=200, from_=1, to=10,
                                    command=update_rate_for(self.air_h_monitor))
        self.soil_h_scale = Tk.Scale(master=self.rate_options_frame, orient='horizontal', label='Umidade do Solo:', length=200, from_=1, to=10,
                                     command=update_rate_for(self.soil_h_monitor))

        self.air_t_scale.pack(side=Tk.LEFT, padx=5, pady=(0, 10), expand=True)
        self.air_h_scale.pack(side=Tk.LEFT, padx=5, pady=(0, 10), expand=True)
        self.soil_h_scale.pack(side=Tk.LEFT, padx=5, pady=(0, 10), expand=True)

        self.rate_options_frame.pack(side=Tk.LEFT, padx=20, pady=10)

        # Sample Now button.
        def _sample():
            data_collector.sample_now = True

        self.sample_button = Tk.Button(master=self.dashboard, text='Amostrar imediatamente', width=30, borderwidth=10, bg='red', fg='white', command=_sample)
        self.sample_button.pack(side=Tk.LEFT, padx=50)

        # Quit button
        def _quit():
            self.quit()  # stops mainloop
            self.destroy()  # this is necessary on Windows to prevent
            # Fatal Python Error: PyEval_RestoreThread: NULL tstate

        self.quit_button = Tk.Button(master=self.dashboard, text='Sair', command=_quit)
        self.quit_button.pack(side=Tk.RIGHT, padx=20)


    def add_measurements(self, measurements):
        if measurements[0]:
            self.air_t_monitor.update_data(measurements[0])
        if measurements[1]:
            self.air_h_monitor.update_data(measurements[1])
        if measurements[2]:
            self.soil_h_monitor.update_data(measurements[2])



# Main window instance.
muxaget = MuxaGet()


# ##################################################################################################
# Animation setup.
# ##################################################################################################

# Interactive mode
pyplot.ion()


# Init function.
def init():
    return muxaget.air_t_monitor.get_animated_lines() +  muxaget.air_h_monitor.get_animated_lines() + muxaget.soil_h_monitor.get_animated_lines()


# Generate data as if it were coming from the board.
data_gen = DataGenerator(rate=REFRESH_RATE / 1000)
data_collector = DataCollector(data_gen.q, data_gen.rate, [REFRESH_RATE/1000, REFRESH_RATE/1000, REFRESH_RATE/1000])
data_gen.start()


# Poll data from serial port.
def poll_data(i):
    result = data_collector.poll()
    if result:
        muxaget.add_measurements(result)

    return muxaget.air_t_monitor.get_animated_lines() + muxaget.air_h_monitor.get_animated_lines() + muxaget.soil_h_monitor.get_animated_lines()

# Animate plots.
ani = animation.FuncAnimation(muxaget.figure, poll_data, init_func=init, interval=REFRESH_RATE, blit=True)


# ##################################################################################################
# Main loop.
# ##################################################################################################

# Start the GUI.
muxaget.mainloop()