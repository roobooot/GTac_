# -*- coding: utf-8 -*-
"""
Created on Fri Dec  4 11:23:56 2020

@author: Zeyu
"""

# import numpy as np
from data_gen import raw_data_byts_checkout,raw_data_byts_checkout_2, raw_data_checkout, bytes_data_strip
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
                           'mag_x7', 'mag_y7', 'mag_z7',
                           'mag_x8', 'mag_y8', 'mag_z8',
                           'mag_x9', 'mag_y9', 'mag_z9',
                           'mag_x10', 'mag_y10', 'mag_z10',
                           'mag_x11', 'mag_y11', 'mag_z11',
                           'mag_x12', 'mag_y12', 'mag_z12',
                           'mag_x13', 'mag_y13', 'mag_z13',
                           'mag_x14', 'mag_y14', 'mag_z14',
                           'mag_x15', 'mag_y15', 'mag_z15',
                           'mat1', 'mat2', 'mat3','mat4',
                           'mat5', 'mat6', 'mat7','mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                            'mat1', 'mat2', 'mat3','mat4',
                           'mat5', 'mat6', 'mat7','mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                            'mat1', 'mat2', 'mat3','mat4',
                           'mat5', 'mat6', 'mat7','mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                            'mat1', 'mat2', 'mat3','mat4',
                           'mat5', 'mat6', 'mat7','mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                            'mat1', 'mat2', 'mat3','mat4',
                           'mat5', 'mat6', 'mat7','mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                            'mat1', 'mat2', 'mat3','mat4',
                           'mat5', 'mat6', 'mat7','mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                            'mat1', 'mat2', 'mat3','mat4',
                           'mat5', 'mat6', 'mat7','mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                            'mat1', 'mat2', 'mat3','mat4',
                           'mat5', 'mat6', 'mat7','mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                            'mat1', 'mat2', 'mat3','mat4',
                           'mat5', 'mat6', 'mat7','mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                            'mat1', 'mat2', 'mat3','mat4',
                           'mat5', 'mat6', 'mat7','mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                            'mat1', 'mat2', 'mat3','mat4',
                           'mat5', 'mat6', 'mat7','mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                            'mat1', 'mat2', 'mat3','mat4',
                           'mat5', 'mat6', 'mat7','mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                           'Hz', 'milliseconds']
COL_INDEX = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]])
COL_NUM = 12
MAG_NUM = 45
DATA_LEN = 287 # 28 for two fingers, 68 for five fingers

def find_init(data_seq, n):
    # average the n head data point of data_seq
    sum = data_seq.iloc[0]
    for i in range(1,n):
        sum = sum + data_seq.iloc[i]
    avg = (sum/n).astype('int64')
    return avg

def pre_process_five(data_df):
    # find initial values from first 100 frames
    # init_avg = find_init(data_df, 100)
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
    # mag_toappend = pd.DataFrame(np.zeros([1, MAG_NUM], dtype='int64'), columns=COLUMNS_RAW_FINGER_DATA[:MAG_NUM])
    data_to_append = []
    for i in range(zeros_col_index, len(data_df)):
        d = data_df.iloc[i]
        sec = np.where(COL_INDEX == d.col)[0][0]  # find the finger section index of current frame, i.e., [0,1,2]

        # mag_toappend = mag_toappend + d[:MAG_NUM]

        frame_matrix_toappend[0][sec][d.col % 4][0] = d.mat1
        frame_matrix_toappend[0][sec][d.col % 4][1] = d.mat2
        frame_matrix_toappend[0][sec][d.col % 4][2] = d.mat3
        frame_matrix_toappend[0][sec][d.col % 4][3] = d.mat4
        frame_matrix_toappend[1][sec][d.col % 4][0] = d.mat5
        frame_matrix_toappend[1][sec][d.col % 4][1] = d.mat6
        frame_matrix_toappend[1][sec][d.col % 4][2] = d.mat7
        frame_matrix_toappend[1][sec][d.col % 4][3] = d.mat8
        frame_matrix_toappend[2][sec][d.col % 4][0] = d.mat9
        frame_matrix_toappend[2][sec][d.col % 4][1] = d.mat10
        frame_matrix_toappend[2][sec][d.col % 4][2] = d.mat11
        frame_matrix_toappend[2][sec][d.col % 4][3] = d.mat12
        frame_matrix_toappend[3][sec][d.col % 4][0] = d.mat13
        frame_matrix_toappend[3][sec][d.col % 4][1] = d.mat14
        frame_matrix_toappend[3][sec][d.col % 4][2] = d.mat15
        frame_matrix_toappend[3][sec][d.col % 4][3] = d.mat16
        frame_matrix_toappend[4][sec][d.col % 4][0] = d.mat17
        frame_matrix_toappend[4][sec][d.col % 4][1] = d.mat18
        frame_matrix_toappend[4][sec][d.col % 4][2] = d.mat19
        frame_matrix_toappend[4][sec][d.col % 4][3] = d.mat20

        if d.col == 11:
            for f, finger in enumerate(frame_matrix_toappend):
                for s, section in enumerate(finger):
                    # append mag data
                    mag_sec_index = 3 * (3 * f + s)
                    mag_toappend = d[:MAG_NUM]
                    data_to_append.append(mag_toappend[mag_sec_index])
                    data_to_append.append(mag_toappend[mag_sec_index + 1])
                    data_to_append.append(mag_toappend[mag_sec_index + 2])
                    # append matrix data
                    data_to_append.extend(section.astype('int64').flatten())
                    data_to_append.append(FINGER[f])
                    data_to_append.append(SECTION[s])
                    data_to_append.append(d.milliseconds)
                    data_assigned.loc[len(data_assigned)] = data_to_append
                    # clear memory
                    data_to_append = []
            mag_toappend = pd.DataFrame(np.zeros([1, MAG_NUM], dtype='int64'), columns=COLUMNS_RAW_FINGER_DATA[:MAG_NUM])
    return data_assigned


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
    SerialPort, locname, DataPoints = args.serialport, args.locname, args.datapoints
    # creat a pandas DataFrame to store the data
    df_FINGERS = pd.DataFrame(columns=COLUMNS_Finger)
    df_RAW = pd.DataFrame(columns=COLUMNS_RAW_FINGER_DATA)
    dt_list = []
    ms_list = []

    filename = 'data/' + locname + '_' + \
               str(DataPoints) + '_points_' +\
               timestr + '.csv'
    filename_assigned = 'data/' + locname + '_' +\
                        str(DataPoints) + '_points_assigned_' +\
                        timestr + '.csv'

    # open the serial port
    ser = serial.Serial(SerialPort, 115200)
    time.sleep(1)
    if ser.is_open:
        print('Serial Port Opened:\n', ser)
        ser.flushInput()
    start = time.time()

    # init position
    ser.write(b'0')
    time.sleep(1)

    # Read and record the data
    TO_GRASP = True
    TO_RELEASE = False
    i = 0

    while (i < DataPoints):
        s = time.time()
        data = raw_data_byts_checkout_2(ser)
        end1 = time.time()
        print('time of checkout:',end1 - s)

        if data:
            print('data_{}:{}'.format(i, data))
            print('length:{}'.format(len(data)))

        ms = int(round((time.time() - start) * 1000))
        data.append(ms)
        dt_list.append(data)
        i = i + 1
        end2 = time.time()
        print('time of checkout and append:', end2 - start)
        if time.time()-start > 1 and TO_GRASP:
            ser.write(b'230')
            # print('pinch')
            TO_GRASP = False
            TO_RELEASE = True
        if time.time() - start > 4 and TO_RELEASE:
            ser.write(b'480')
            # print('release')
            TO_RELEASE = False
            TO_INIT = True
        if time.time() - start > 10 and TO_INIT:
            ser.write(b'0')
            # print('release')
            TO_INIT = False
    ser.write(b'0')
    end_collect = time.time()
    # pre-process the data
    i = 0
    while (i < DataPoints):
        start = time.time()
        flat_data = dt_list[i]
        end = time.time()
        # print('time of parser:', end - start)

        if len(flat_data) == DATA_LEN:
            print('{}/{}:{}'.format(i, DataPoints, flat_data))  # print what data read-out
            print('length:{}'.format(len(flat_data)))
            df_RAW.loc[len(df_RAW)] = flat_data  # append data into dataframe
        i = i + 1

    # average the data
    sum = df_RAW.iloc[0]
    for i in range(1,100):
        sum = sum + df_RAW.iloc[i]
    avg = (sum / 100).astype('int64')
    df_RAW = df_RAW - avg
    end_processed = time.time()
    print('time to collect:{} seconds.\ntime to processed:{} seconds.'.format(end_collect-start,end_processed-end_collect))
    ser.close()
    print('Serial Port Closed')

    df_RAW.to_csv(filename)
    print('data saved:' + filename)

    # data_seq = pd.read_csv(filename, index_col=0)
    # data_assigned = pre_process_five(data_seq)
    # data_assigned.to_csv(filename_assigned)
    # print('assigned data saved:' + filename_assigned)

    # plotting the data
