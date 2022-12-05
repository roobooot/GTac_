"""The interface to read serial data.

The serial data has the format:
- Two bytes beginning: b'<\x00'
- A sequence of data, each data consists of 2 bytes.
- ending: b'>'

The reader processes the reading the stores it as a list of integers, with each
integer corresponding to a 2-byte data.
"""
import time
import logging
import threading
import typing as TP
import numpy as np

import serial


logger = logging.getLogger(__name__)


class _GtacSerialReaderSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        key = tuple(args)
        if key not in cls._instances:
            cls._instances[key] = super(_GtacSerialReaderSingleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[key]


class GtacSerialReader(metaclass=_GtacSerialReaderSingleton):
    def __init__(self, serial_port_name: str, baud_rate: int, frequency: int):
        self._serial = serial.Serial(serial_port_name, baud_rate)
        t0 = time.time()
        self._thread: TP.Optional[threading.Thread] = None
        self._running = False
        while True:
            if self._serial.is_open:
                break
            if time.time() - t0 > 0.5:
                raise serial.SerialException(
                    "Serial connection to %s timeout" % serial_port_name
                )
            time.sleep(0.01)
        self._serial.reset_input_buffer()

        self._dt = 1.0 / frequency

        self._reading = None
        self._last_read = None

    def start(self):
        if self._thread is None:
            self._running = True
            self._serial.reset_input_buffer()
            self._thread = threading.Thread(target=self._read)
            self._thread.start()

    def _read(self):
        self._last_read = time.time()
        violation_counter = 0
        violation_threshold = 5
        while self._running:
            content = self._serial.read_until(b">")
            read_time = time.time()
            logger.debug("Serial reading of length %d: %s" % (len(content), content))
            if content[0:2] != b"<\x00" or len(content) != 292 * 2 + 3:
                logger.debug("Not a proper message. Skip.")
                continue
            duration = read_time - self._last_read
            if duration > self._dt * 0.95:
                if duration > self._dt * 1.05:
                    violation_counter += 1
                else:
                    violation_counter = 0
                if violation_counter >= violation_threshold:
                    logger.warning(
                        "%i consecutive realtime violations. Last violation dt: %s, desired dt: %s"
                        % (violation_threshold, duration, self._dt)
                    )
                logger.debug("Update reading.")
                self._last_read = time.time()
                self._last_read = read_time
                content = content[2:-1]  # remove <\x00 and >
                parsed = [content[i : i + 2] for i in range(0, len(content), 2)]
                assert len(parsed) == 292
                self._reading = np.array(
                    [
                        int.from_bytes(bs[0:1] + bs[1:2], byteorder="big", signed=True)
                        for bs in parsed
                    ]
                )

    def stop(self):
        if self._running:
            self._running = False
            self._thread.join()
            self._thread = None

    @property
    def reading(self):
        return self._reading

    @property
    def last_reading_time(self):
        return self._last_read
