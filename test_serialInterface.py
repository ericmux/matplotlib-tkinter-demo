from unittest import TestCase
from muxaserial import SerialInterface
import time
import threading


class TestSerialInterface(TestCase):

    def setUp(self):
        self.port = "/dev/tty.usbserial-AL02BAG3"
        self.baud_rate = 19200

    def test_wait_for_data(self):
        serial_port = SerialInterface(self.port, self.baud_rate)
        while True:
            time.sleep(10)
            if serial_port.is_working:
                serial_port.sample_now()
                time.sleep(10)
                serial_port.update_sample_period(SerialInterface.TEMP, 5)
                serial_port.update_sample_period(SerialInterface.HUM, 6)
                serial_port.update_sample_period(SerialInterface.HUMS, 7)
                time.sleep(30)
                serial_port.stop_serial()
                break

