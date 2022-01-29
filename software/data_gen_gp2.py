#! /usr/bin/env python

import serial
import time
import numpy as np
# from Data_Analysis import predict_with_LDA
# from Data_Analysis import load_model
import collections
import argparse
RF_MAT_ROW = np.array([[0, 0, 0, 0], [1, 1, 1, 1], [3, 3, 3, 3], [2, 2, 2, 2]])
RF_MAT_COL = np.array([[2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0]])
NoM = 2

# sudo chmod 666 /dev/ttyACM0


def raw_data_byts_checkout_2(ser, verbose=False):
    start = time.time()
    data = []
    END = False
    START = False
    while (1):
        # ser.flushInput()
        b = ser.read()
        # print(b)
        if b == b'<':
            d = ser.read()
            # print(d)
            if d == b'\x00':
                START = True
                continue
        if b == b'>':
            END = True
        if END:
            break
        if START:
            c = ser.read()  # low byte
            # print(c)
            x = int.from_bytes(b + c, byteorder='big', signed=True)
            # if abs(x) > 1000: # add a soft threshold to eliminate the electric shock in signals.
            #     x = 0
            data.append(x)
            # print(ser.read())

    if verbose:
        print('Raw GTac Data:{}'.format(data))
        print('Length:{}'.format(len(data)))
        print('time of checking out'.format(time.time() - start))
    return data


def regulate_data(dt):
    data_n = list(range(len(dt)))
    for j in range(len(dt)):
        if j < 3*NoM:
            data_n[j] = dt[j]
        else:
            if j < 19*NoM:
                finger, sec, r, c = find_location(j - 3*NoM)
                pos = 16*finger + 4*r + c
                data_n[pos+3*NoM] = dt[j]
            else:
                data_n[j] = dt[j]
    return data_n


def find_location(index):
    h_line = index // (4*NoM)  # horizontal lines
    sec = h_line // 4
    v_line = index % 8  # vertical lines
    finger = v_line // 4
    ro = h_line % 4
    co = v_line % 4
    mat_row = RF_MAT_ROW
    mat_col = RF_MAT_COL
    r = np.where(mat_row == co)[0][0]
    c = np.where(mat_col == ro)[1][0]
    return finger, sec, r, c


def _init_GTac(DataPoints=400):
    dt_list = []
    i = 0
    while i < DataPoints:
        data = raw_data_byts_checkout_2(ser, verbose=False)
        dt_list.append(data)
        i = i + 1
    dt_list = np.array(dt_list)
    avg = dt_list[-200:].mean(axis=0, dtype=int)
    print('Initial values of GTac have been found:')
    print(avg)
    return avg


def simple_test():
    i = 0
    avg = _init_GTac(DataPoints=600)
    print('start')
    while i < 10000:
        data = raw_data_byts_checkout_2(ser, verbose=False)
        new = np.subtract(data, avg)
        print(f'{i}: {new[6:22]}')
        i += 1


# def online_predict(ser, Data_points=30000):
#     scl, clf = load_model(model_name='LDA', remark='Test_AC')
#     buffer = collections.deque(maxlen=3)
#     for i in range(Data_points):
#         t = time.time()
#         buffer.append(raw_data_byts_checkout_2(ser))
#         # print(f'time for load data {round(1000*(time.time()-t), 2)} ms')
#         # print(f'{i}: force{self.dt_list[-1]}')
#         # if 1:
#         x_val = np.array(buffer)
#         # x_val = np.mean(self.tele_buffer, axis=0, dtype=int)
#         # print(x_val)
#         if i % 5 == 0:
#             predict_with_LDA(x_val[:, 0:22], scl, clf)
#
#             print(f'{i} and time for whole single loop = {round(1000*(time.time()-t), 2)} ms')


if __name__ == "__main__":
    data_list = []
    ser = serial.Serial('/COM8', 115200, write_timeout=1)
    if ser.isOpen():
        print('Serial Port Opened:\n', ser)
        ser.flushInput()
    else:
        print('open failed')
    # Read and record the data
    # n_trunck = 3 # how many repeated during readout (adjust in Arduino code)
    # online_predict(ser)
    ser.close()
    print('Serial Port Closed')
