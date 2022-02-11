# -*- coding: utf-8 -*-
"""
Created on Fri Dec  4 11:23:56 2020

@author: Zeyu
"""

# import numpy as np
from data_gen import raw_data_byts_checkout, raw_data_checkout, bytes_data_strip
# import matplotlib.pyplot as plt
import serial
import time
import pandas as pd
import numpy as np
import seaborn as sns
import argparse

COLUMNS_Finger = ['mag_x', 'mag_y', 'mag_z',
                  'mat_x1y1', 'mat_x1y2', 'mat_x1y3', 'mat_x1y4',
                  'mat_x2y1', 'mat_x2y2', 'mat_x2y3', 'mat_x2y4',
                  'mat_x3y1', 'mat_x3y2', 'mat_x3y3', 'mat_x3y4',
                  'mat_x4y1', 'mat_x4y2', 'mat_x4y3', 'mat_x4y4',
                  'finger', 'section', 'milliseconds'
                  ]
# FINGER = ['THUMB','INDEX','MID','RING','LIT']
FINGER = ['THUMB', 'INDEX', 'MID','RING','LIT']
SECTION = ['DISTAL', 'PROXIMAL', 'METACARPAL']
COLUMNS_RAW_FINGER_DATA = ['mag_x1', 'mag_y1', 'mag_z1',
                           'mag_x2', 'mag_y2', 'mag_z2',
                           'mag_x3', 'mag_y3', 'mag_z3',
                           'mag_x4', 'mag_y4', 'mag_z4',
                           'mag_x5', 'mag_y5', 'mag_z5',
                           'mag_x6', 'mag_y6', 'mag_z6',
                           'col', 'mat1', 'mat2', 'mat3','mat4',
                           'mat5', 'mat6', 'mat7','mat8'
                           'Hz', 'milliseconds']
COL_INDEX = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]])
COL_NUM = 12
DATA_LEN = 28 # 28 for two fingers, 68 for five fingers

def find_init(data_seq, n):
    # average the n head data point of data_seq
    sum = data_seq.iloc[0]
    for i in range(1,n):
        sum = sum + data_seq.iloc[i]
    avg = (sum/n).astype('int64')
    return avg

def pre_process(data_df):
    # find initial values from first 100 frames
    init_avg = find_init(data_df, 100)
    # assign finger and section to each frame
    data_assigned = pd.DataFrame(columns=COLUMNS_Finger)
    # get rid of uncomplete readings
    for i in range(len(data_df)):

        d = data_df.iloc[i]
        if d.col == 0:
            zeros_col_index = i
            break
    # looping from index when col==0
    frame_matrix_toappend = np.zeros([len(FINGER), len(SECTION), 4, 4])
    mag_toappend = pd.DataFrame(np.zeros([1, 18], dtype='int64'), columns=['mag_x1', 'mag_y1', 'mag_z1',
                                                                           'mag_x2', 'mag_y2', 'mag_z2',
                                                                           'mag_x3', 'mag_y3', 'mag_z3',
                                                                           'mag_x4', 'mag_y4', 'mag_z4',
                                                                           'mag_x5', 'mag_y5', 'mag_z5',
                                                                           'mag_x6', 'mag_y6', 'mag_z6'])
    data_to_append = []
    for i in range(zeros_col_index, len(data_df)):
        d = data_df.iloc[i]
        sec = np.where(COL_INDEX == d.col)[0][0]  # find the finger section index of current frame, i.e., [0,1,2]

        mag_toappend = mag_toappend + d[:18]

        frame_matrix_toappend[0][sec][d.col % 4][0] = max(d.mat1-init_avg.mat1,0)
        frame_matrix_toappend[0][sec][d.col % 4][1] = max(d.mat2-init_avg.mat2,0)
        frame_matrix_toappend[0][sec][d.col % 4][2] = max(d.mat3-init_avg.mat3,0)
        frame_matrix_toappend[0][sec][d.col % 4][3] = max(d.mat4-init_avg.mat4,0)
        frame_matrix_toappend[1][sec][d.col % 4][0] = max(d.mat5-init_avg.mat5,0)
        frame_matrix_toappend[1][sec][d.col % 4][1] = max(d.mat6-init_avg.mat6,0)
        frame_matrix_toappend[1][sec][d.col % 4][2] = max(d.mat7-init_avg.mat7,0)
        frame_matrix_toappend[1][sec][d.col % 4][3] = max(d.mat8-init_avg.mat8,0)


        if d.col == 11:
            for f, finger in enumerate(frame_matrix_toappend):
                for s, section in enumerate(finger):
                    # append mag data
                    mag_sec_index = 3 * (3 * f + s)
                    data_to_append.append(int(mag_toappend.iloc[0][mag_sec_index] / COL_NUM - init_avg.iloc[mag_sec_index]))
                    data_to_append.append(int(mag_toappend.iloc[0][mag_sec_index + 1] / COL_NUM - init_avg.iloc[mag_sec_index + 1]))
                    data_to_append.append(int(mag_toappend.iloc[0][mag_sec_index + 2] / COL_NUM - init_avg.iloc[mag_sec_index + 2]))
                    # append matrix data
                    data_to_append.extend(section.astype('int64').flatten())
                    data_to_append.append(FINGER[f])
                    data_to_append.append(SECTION[s])
                    data_to_append.append(d.milliseconds)
                    data_assigned.loc[len(data_assigned)] = data_to_append
                    # clear memory
                    data_to_append = []
            mag_toappend = pd.DataFrame(np.zeros([1, 18], dtype='int64'), columns=['mag_x1', 'mag_y1', 'mag_z1',
                                                                                           'mag_x2', 'mag_y2', 'mag_z2',
                                                                                           'mag_x3', 'mag_y3', 'mag_z3',
                                                                                           'mag_x4', 'mag_y4', 'mag_z4',
                                                                                           'mag_x5', 'mag_y5', 'mag_z5',
                                                                                           'mag_x6', 'mag_y6',
                                                                                           'mag_z6'])
    return data_assigned


if __name__ == '__main__':
    # current time
    timestr = time.strftime("%Y%m%d_%H%M%S")
    # parse the argumments
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--serialport", default='COM12',
                        help="set serial port (default: COM12)")
    parser.add_argument("-l", "--locname", default='test',
                        help="set location name where probe pressing, L1-L9, (default: L5)")
    parser.add_argument("-p", "--datapoints", default=100, type=int,
                        help="set number of data points to collect (default: 100)")
    # Read arguments from command line
    args = parser.parse_args()
    SerialPort, locname, DataPoints = args.serialport, args.locname, args.datapoints
    # creat a pandas DataFrame to store the data
    df_FINGERS = pd.DataFrame(columns=COLUMNS_Finger)
    df_RAW = pd.DataFrame(columns=COLUMNS_RAW_FINGER_DATA)
    dt_list = []
    ms_list = []

    # open the serial port
    ser = serial.Serial(SerialPort, 115200)
    time.sleep(1)
    if ser.is_open:
        print('Serial Port Opened:\n', ser)
        ser.flushInput()
    start = time.time()

    # Read and record the data
    i = 0
    filename = 'data/' + locname + '_' + str(DataPoints) + '_points_' + timestr + '.csv'
    while (i < DataPoints):
        data = raw_data_byts_checkout(ser)
        if data:
            print('data_{}:{}'.format(i, data))
            print('length:{}'.format(len(data)))
        dt_list.append(data)
        ms = int(round((time.time() - start) * 1000))
        ms_list.append(ms)
        i = i + 1

    # pre-process the data
    i = 0
    while (i < DataPoints):
        flat_data = bytes_data_strip(dt_list[i])
        if len(flat_data) == DATA_LEN:
            flat_data.append(ms_list[i])
            print('{}/{}:{}'.format(i, DataPoints, flat_data))  # print what data read-out
            print('length:{}'.format(len(flat_data)))
            df_RAW.loc[len(df_RAW)] = flat_data  # append data into dataframe
        i = i + 1
    end = time.time()
    print(end - start, ' seconds')
    ser.close()
    print('Serial Port Closed')
    df_RAW.to_csv(filename)
    print('data saved:' + filename)
    # plotting the data
