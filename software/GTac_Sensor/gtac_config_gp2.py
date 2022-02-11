# config file for two fingered gripper
import numpy as np
RF_MAT_ROW = np.array([[0, 0, 0, 0], [1, 1, 1, 1], [3, 3, 3, 3], [2, 2, 2, 2]])
RF_MAT_COL = np.array([[2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0]])

LF_MAT_ROW = np.array([[0, 0, 0, 0], [1, 1, 1, 1], [3, 3, 3, 3], [2, 2, 2, 2]])
LF_MAT_COL = np.array([[0, 1, 3, 2], [0, 1, 3, 2], [0, 1, 3, 2], [0, 1, 3, 2]])

UP_MAT_ROW = np.array([[2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0]])
UP_MAT_COL = np.array([[2, 2, 2, 2], [3, 3, 3, 3], [1, 1, 1, 1], [0, 0, 0, 0]])

MAT_ORIENT_ROW = np.array([[RF_MAT_ROW],
                           [RF_MAT_ROW]])
MAT_ORIENT_COL = np.array([[RF_MAT_COL],
                           [RF_MAT_COL]])

MAG_NUM = 6
MAT_NUM = 16
ALL_GTAC_NUM = 38
COL_INDEX = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]])
COL_NUM = 12
FINGER_NUM = 2
SEC_NUM = 1