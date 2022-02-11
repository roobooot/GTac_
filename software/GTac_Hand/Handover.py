from GTac_Data import gtac_data
from GTac_Hand import gtac_hand
from data_gen import raw_data_byts_checkout_2
from data_collect_fingers_five import COLUMNS_RAW_FINGER_DATA, MAG_NUM, COL_INDEX
# import matplotlib.pyplot as plt
import serial
import time
import pandas as pd
import numpy as np
import seaborn as sns
import argparse

# RF: the conductive cables are from the Right
# LF: the conductive cables are from the Left
# UP: the conductive cables are from the Up
RF_MAT_ROW = np.array([[0, 0, 0, 0], [1, 1, 1, 1], [3, 3, 3, 3], [2, 2, 2, 2]])
RF_MAT_COL = np.array([[2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0]])

LF_MAT_ROW = np.array([[0, 0, 0, 0], [1, 1, 1, 1], [3, 3, 3, 3], [2, 2, 2, 2]])
LF_MAT_COL = np.array([[0, 1, 3, 2], [0, 1, 3, 2], [0, 1, 3, 2], [0, 1, 3, 2]])

UP_MAT_ROW = np.array([[2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0]])
UP_MAT_COL = np.array([[2, 2, 2, 2], [3, 3, 3, 3], [1, 1, 1, 1], [0, 0, 0, 0]])

MAT_ORIENT_ROW = np.array([[UP_MAT_ROW, UP_MAT_ROW, LF_MAT_ROW],
                           [LF_MAT_ROW, RF_MAT_ROW, RF_MAT_ROW],
                           [RF_MAT_ROW, RF_MAT_ROW, RF_MAT_ROW],
                           [LF_MAT_ROW, RF_MAT_ROW, RF_MAT_ROW],
                           [RF_MAT_ROW, RF_MAT_ROW, RF_MAT_ROW]])
MAT_ORIENT_COL = np.array([[UP_MAT_COL, UP_MAT_COL, LF_MAT_COL],
                           [LF_MAT_COL, RF_MAT_COL, RF_MAT_COL],
                           [RF_MAT_COL, RF_MAT_COL, RF_MAT_COL],
                           [LF_MAT_COL, RF_MAT_COL, RF_MAT_COL],
                           [RF_MAT_COL, RF_MAT_COL, RF_MAT_COL]])


def collect_DataPoints(ser, DataPoints, starttime):
    dt_list = []
    i = 0
    while (i < DataPoints):
        data = raw_data_byts_checkout_2(ser, verbose=False)
        ms = int(round((time.time() - starttime) * 1000))
        data.append(ms)
        data = gtac_data.preprocess_(data)
        dt_list.append(data)
        i = i + 1
    return dt_list[-100:]


def find_mat_value(data_frame_array, finger, sec, r, c):
    index = sec * 4 * 20 + finger * 4 + \
            MAT_ORIENT_COL[finger, sec, r, c] * 20 + \
            MAT_ORIENT_ROW[finger, sec, r, c]
    return index, data_frame_array[index + MAG_NUM]


def find_location(index):
    h_line = index // 20  # horizontal lines
    sec = h_line // 4
    v_line = index % 20  # vertical lines
    finger = v_line // 4
    ro = h_line % 4
    co = v_line % 4
    if finger == 0 and sec in [0, 1]:
        c = np.where(UP_MAT_ROW == co)[1][0]
        r = np.where(UP_MAT_COL == ro)[0][0]
    else:
        mat_row = MAT_ORIENT_ROW[finger, sec]
        mat_col = MAT_ORIENT_COL[finger, sec]
        r = np.where(mat_row == co)[0][0]
        c = np.where(mat_col == ro)[1][0]
    return finger, sec, r, c


if __name__ == '__main__':
    # current time
    timestr = time.strftime("%Y%m%d_%H%M%S")
    # parse the argumments
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--serialport", default='COM6',
                        help="set serial port (default: COM6)")
    parser.add_argument("-l", "--locname", default='test',
                        help="set location name where probe pressing, L1-L9, (default: L5)")
    parser.add_argument("-p", "--datapoints", default=100, type=int,
                        help="set number of data points to collect (default: 100)")
    # Read arguments from command line
    args = parser.parse_args()
    SerialPort, locname, DataPoints = args.serialport, \
                                      args.locname, \
                                      args.datapoints
    # creat a pandas DataFrame to store the data
    df_RAW = pd.DataFrame(columns=COLUMNS_RAW_FINGER_DATA)
    dt_list = []

    ser = serial.Serial(SerialPort, 115200)
    time.sleep(0.5)
    if ser.is_open:
        print('Serial Port Opened:\n', ser)
        ser.flushInput()
    start = time.time()
    THUMB_TO_GRASP = True
    INDEX_TO_GRASP = False
    # init position
    ser.write(b'0')
    time.sleep(1)

    n = 0
    handover_index = 0
    handover_index_th = 100
    init_values = collect_DataPoints(ser, DataPoints=100, starttime=start)
    avg = np.array(init_values).mean(axis=0, dtype=int)
    while (n < DataPoints):
        print('{}/{}'.format(i, DataPoints))
        # collect init values for average
        s = time.time()
        data = raw_data_byts_checkout_2(ser, verbose=False)
        ms = int(round((time.time() - start) * 1000))
        data.append(ms)
        # dt_list.append(data)
        data_frame_array = data - avg  # average by the initial data
        # test index finding
        MAT_index, value = find_mat_value(data_frame_array,
                                          finger=4, sec=1,
                                          r=3, c=3)
        print('INDEX: {}, Matrix Value:{}'.format(MAT_index, value))

        # print resistive sensing above threshold
        index = np.where(data_frame_array[MAG_NUM:-2] > 50)[0]
        print(index)
        if len(index) != 0:
            for i in index:
                # find_location(i)
                print(find_location(i))
        # find channels of tri-axis signals that are above threshold.
        tri_axis = np.where(abs(data_frame_array[:MAG_NUM]) > 150)[0]
        print(tri_axis)
        if 9 in tri_axis or 15 in tri_axis:
            handover_index = handover_index + 1
        n = n + 1
        if time.time() - start > 1 and THUMB_TO_GRASP:
            ser.write(b'220')
            # print('pinch')
            THUMB_TO_GRASP = False
            INDEX_TO_GRASP = True
        if time.time() - start > 4 and INDEX_TO_GRASP:
            ser.write(b'450')
            time.sleep(0.1)
            ser.write(b'350')
            time.sleep(0.1)
            ser.write(b'560')
            time.sleep(0.1)
            ser.write(b'660')
            time.sleep(0.1)
            # print('release')
            INDEX_TO_GRASP = False
            TO_INIT = True
        if handover_index > handover_index_th:
            ser.write(b'0')
            TO_INIT = False
            break
        if time.time() - start > 20 and TO_INIT:
            ser.write(b'0')
            # print('release')
            TO_INIT = False
    # initiate position
    ser.write(b'0')
