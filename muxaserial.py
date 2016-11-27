import serial
import threading
import Queue
import time
import numpy as np
import struct

"""
Class for the interface between serial port and application. In practice it contains the link and transport layers.
The SerialInterface Class is based on 4 threads:
Writing: Used to write in the serial port.
Reading: Used to read from the serial port.
Concatenating: Used to get the chunks of bytes read from the serial port, concatenate and interpret them.
Manager: Used to manage the queues that are used to send data to the serial port.
"""


class SerialInterface(object):

    ACK = 0x00
    START = 0x06
    INSTANT_SAMPLE = 0x01
    SAMPLE_T = 0x02
    SAMPLE_H = 0x03
    SAMPLE_HS = 0x04
    STOP = 0x05
    MINIMUM_S_T = 10
    MINIMUM_S_H = 10
    MINIMUM_S_HS = 10
    BYTES = 4

    TEMP = 0
    HUM = 1
    HUMS = 2

    COMMAND_DICT = {
        TEMP: SAMPLE_T,
        HUM: SAMPLE_H,
        HUMS: SAMPLE_HS
    }

    MIN_SAMPLE_PERIOD = 5
    MAX_SAMPLE_PERIOD = 255

    def __init__(self, port, baud_rate):
        try:
            self.baud_rate = baud_rate
            self.serial_port = serial.Serial(port, self.baud_rate, timeout=1, writeTimeout=1)
            self.temp_queue = Queue.Queue()
            self.hum_queue = Queue.Queue()
            self.hums_queue = Queue.Queue()
            self.data = bytearray()
            self.data_tracker = 0
            self.counter = 0
            self.stop_everything = threading.Event()
            self.reading = threading.Thread(target=self.read_data)
            # self.tracking = threading.Thread(target=self.track_results)
            self.reading.start()
            self.is_working = False
            # self.tracking.start()

        except serial.SerialException:
            if self.serial_port.isOpen():
                self.serial_port.close()
                self.stop_serial()
            else:
                self.stop_serial()
                raise Exception("Deu Merda")

    def wait_for_data(self, minimum_buffer_size=1, sleep_time=1):
        counter = 0
        while self.serial_port.inWaiting() < minimum_buffer_size and not self.stop_everything.is_set():
            time.sleep(sleep_time)
            counter += 1
            if counter >= 2 and self.serial_port.inWaiting() >= 1:
                break

    def read_data(self):
        time.sleep(2)
        self.serial_port.flushInput()
        self.start_connection()
        self.is_working = True
        while not self.stop_everything.is_set():
            if len(self.data) == 0 or (len(self.data) == 1 and self.data_tracker == 2):
                self.wait_for_data()
            self.receive_data()
        # self.tracking.join()
        if self.serial_port.isOpen():
            self.serial_port.close()

    def stop_serial(self):
        self.serial_port.write(bytearray(struct.pack('B', self.STOP)))
        if not self.stop_everything.is_set():
            self.stop_everything.set()

    def start_connection(self):
        found_start = False
        while not self.stop_everything.is_set():
            self.wait_for_data()
            self.data.extend(self.serial_port.read(self.serial_port.inWaiting()))
            for index, byte in enumerate(self.data):
                if byte == self.START:
                    self.data = self.data[index:]
                    self.serial_port.write(bytearray(struct.pack('B', self.ACK)))
                    found_start = True
                    break
            if found_start:
                found_data = False
                self.wait_for_data()
                self.data.extend(self.serial_port.read(self.serial_port.inWaiting()))
                for index, byte in enumerate(self.data):
                    if byte != self.START:
                        self.data = self.data[index:]
                        found_data = True
                        break
                if found_data:
                    break
            self.data = bytearray()

    def sample_now(self):
        self.serial_port.write(bytearray(struct.pack('B', self.INSTANT_SAMPLE)))

    def update_sample_period(self, measurement, new_sample_period):
        if new_sample_period < self.MIN_SAMPLE_PERIOD:
            new_sample_period = self.MIN_SAMPLE_PERIOD
        elif new_sample_period > self.MAX_SAMPLE_PERIOD:
            new_sample_period = self.MAX_SAMPLE_PERIOD
        self.serial_port.write(bytearray(struct.pack('B', self.COMMAND_DICT[measurement])))
        self.serial_port.write(bytearray(struct.pack('B', new_sample_period)))


    def receive_data(self):
        self.data.extend(self.serial_port.read(self.serial_port.inWaiting()))
        for index, byte in enumerate(self.data):
            if self.data_tracker == 0:
                self.temp_queue.put(byte)
            elif self.data_tracker == 1:
                self.hum_queue.put(byte)
            elif self.data_tracker == 3:
                aux = self.data[index - 1] + byte * 256
                self.hum_queue.put(self.data[index - 1] + byte * 256)
                self.data_tracker = 0
                continue
            self.data_tracker += 1
        if self.data_tracker == 3:
            self.data = self.data[-1:]
            self.data_tracker = 2
        else:
            self.data = bytearray()

    def track_results(self):
        while True:
            if not self.temp_queue.empty():
                print "temp"
                print self.temp_queue.qsize()
            if not self.hum_queue.empty():
                print "hum"
                self.hum_queue.qsize()
            if not self.hums_queue.empty():
                print "hums"
                self.hums_queue.qsize()
            time.sleep(5)