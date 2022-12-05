"""The client for a single GTac sensor."""
import logging
import time
import math

import numpy as np

from .serial_reader import GtacSerialReader


logger = logging.getLogger(__name__)


RF_MAT_ROW = np.array([[0, 0, 0, 0], [1, 1, 1, 1], [3, 3, 3, 3], [2, 2, 2, 2]])
RF_MAT_COL = np.array([[2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0]])

LF_MAT_ROW = np.array([[0, 0, 0, 0], [1, 1, 1, 1], [3, 3, 3, 3], [2, 2, 2, 2]])
LF_MAT_COL = np.array([[0, 1, 3, 2], [0, 1, 3, 2], [0, 1, 3, 2], [0, 1, 3, 2]])

UP_MAT_ROW = np.array([[2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0]])
UP_MAT_COL = np.array([[2, 2, 2, 2], [3, 3, 3, 3], [1, 1, 1, 1], [0, 0, 0, 0]])

MAT_ORIENT_ROW = np.array(
    [
        [LF_MAT_ROW, LF_MAT_ROW, LF_MAT_ROW],
        [RF_MAT_ROW, LF_MAT_ROW, LF_MAT_ROW],
        [RF_MAT_ROW, RF_MAT_ROW, RF_MAT_ROW],
        [LF_MAT_ROW, LF_MAT_ROW, LF_MAT_ROW],
        [RF_MAT_ROW, LF_MAT_ROW, LF_MAT_ROW],
    ]
)
MAT_ORIENT_COL = np.array(
    [
        [LF_MAT_COL, LF_MAT_COL, LF_MAT_COL],
        [RF_MAT_COL, LF_MAT_COL, LF_MAT_COL],
        [RF_MAT_COL, RF_MAT_COL, RF_MAT_COL],
        [LF_MAT_COL, LF_MAT_COL, LF_MAT_COL],
        [RF_MAT_COL, LF_MAT_COL, LF_MAT_COL],
    ]
)
MAG_NUM = 45
MAT_NUM = 16


def find_FAI_index(finger, sec, r, c):
    # the FAI index exclude the mag data
    # the overall index is "output"+NUM_MAG
    index = (
        sec * 4 * 20
        + finger * 4
        + MAT_ORIENT_COL[finger, sec, r, c] * 20
        + MAT_ORIENT_ROW[finger, sec, r, c]
    )
    return index + MAG_NUM


def find_FAI(data_frame_array, finger, sec, r, c):
    index = find_FAI_index(finger, sec, r, c)
    return data_frame_array[index]


def find_SAII_index(finger, sec):
    tri_index = finger * 9 + (2 - sec) * 3
    return tri_index, tri_index + 1, tri_index + 2


def find_SAII(data_frame_array, finger, sec):
    # print('SAII_data: finger {}, sec {}'.format(finger, sec))
    tri_index = finger * 9 + (2 - sec) * 3
    mag_x = data_frame_array[tri_index]
    mag_y = data_frame_array[tri_index + 1]
    mag_z = data_frame_array[tri_index + 2]
    SAII_scaler = math.sqrt(mag_x * mag_x + mag_y * mag_y + mag_z * mag_z)
    # print('Find_SAII: {} scalar: {}'.format([mag_x, mag_y, mag_z], SAII_scaler))
    return [mag_x, mag_y, mag_z], SAII_scaler


def find_sec_index(finger, sec):
    # Input: finger, sec
    # Output: the GTac index in one finger section, shape >> 19
    sec_index = []
    for i in range(MAT_NUM):  # MAT_NUM -> 16: there 4*4 sensing points on FA-I layer
        r = i // 4
        c = i % 4
        index = find_FAI_index(finger, sec, r, c)
        sec_index.append(index)
    mag_all = find_SAII_index(finger, sec)
    for m in mag_all:
        sec_index.append(m)
    return sec_index


class GtacInterface:
    """The interface for a single GTac sensor.

    Args:
        serial_port_name: Device name. e.g., /dev/ttyACM0 on Linux and COM3 on Windows.
        data_index: Which of the consecutive 19-number data this sensor corresponds to.
        baud_rate: Serial baud rate.
        frequency: Desired frequency. Warning will be emitted if not satisfied.
    """

    def __init__(
        self,
        serial_port_name: str,
        data_index: int = 0,
        baud_rate: int = 115200,
        frequency=100,
    ):
        self._reader = GtacSerialReader(serial_port_name, baud_rate, frequency)
        self._idx = data_index
        self._finger = data_index // 3
        self._sec = data_index % 3

    def start(self):
        self._reader.start()
        t0 = time.time()
        while self._reader.reading is None:
            time.sleep(0.001)
            if time.time() - t0 > 2:
                raise RuntimeError("GTac sensor reading timeout.")

    def stop(self):
        self._reader.stop()

    @property
    def pressures(self):
        indices = find_sec_index(self._finger, self._sec)
        return self._reader.reading[indices[:16]].reshape([4, 4])

    @property
    def forces(self):
        start = self._finger * 9 + (2 - self._sec) * 3
        return self._reader.reading[start : start + 3]
