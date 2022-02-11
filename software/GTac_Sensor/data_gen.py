import serial
import time
import numpy as np
from GTac_Data import gtac_data
# import pandas as pd

def data_to_list(data_str):
    data_list = [int(idx) for idx in data_str.split(' ')]
    return data_list


def data_checkout(ser, n_trunck):
    # Input:
    # Output: datatype is list
    data = []  # 5*4
    mxl_rows = []

    read_line = 0

    row = []
    flag_continue = False
    while (len(data) < 5):

        data_piece = []  # 3*9
        while (len(data_piece) < n_trunck):
            b = ser.readline()  # read a byte string
            string_n = b.decode()  # decode byte string into Unicode
            string = string_n.strip()  # remove \n and \r
            #             print(string)
            if len(string) > 15:  # filtering the false data string
                data_list = data_to_list(string)
                #                 print(data_list)
                read_line = read_line + 1  # number of validate read lines
                if not data_piece:
                    data_piece.append(data_list)
                    continue
                if data_piece[-1][0] == data_list[0]:
                    data_piece.append(data_list)
                else:
                    data_piece = [data_list]
        #         print(data_piece)

        if not data_piece[0][0] == 0 and not flag_continue:
            continue

        data_piece_avg = np.mean(np.array(data_piece), axis=0, dtype=int)
        if not data:
            matrix_row = [data_piece_avg[1], data_piece_avg[2], data_piece_avg[3], data_piece_avg[4]]
            mxl_row = [data_piece_avg[5], data_piece_avg[6], data_piece_avg[7], data_piece_avg[8]]
            data.append(matrix_row)
            mxl_rows.append(mxl_row)
            flag_continue = True
            continue
        if data_piece_avg[0] == len(data):
            matrix_row = [data_piece_avg[1], data_piece_avg[2], data_piece_avg[3], data_piece_avg[4]]
            mxl_row = [data_piece_avg[5], data_piece_avg[6], data_piece_avg[7], data_piece_avg[8]]
            data.append(matrix_row)
            mxl_rows.append(mxl_row)
        elif len(data) == 4:
            mxl_row_avg = np.mean(np.array(mxl_rows), axis=0, dtype=int)
            data.append(list(mxl_row_avg))
        elif len(data) < 4:
            data = []
    return data


def handle_data(data):
    print(data)


def raw_data_checkout(ser):
    ser.flushInput()
    # time.sleep(0.001)
    # b = ser.read(ser.inWaiting())
    b = ser.readline()  # read a byte string
    string_n = b.decode()  # decode byte string into Unicode
    string = string_n.strip()  # remove \n and \r
    data = string.split(' ')
    # time.sleep(0.01)
    # handle_data(data)
    return data


def raw_data_byts_checkout(ser):
    ser.flushInput()
    b = ser.readline()
    # b = ser.read(1000)
    # while(1):
    #     x = ser.read()
    #     if x == b'0xAA':
    #         y = ser.read()
    #         if y == b'0x55':
    #             b = ser.read(574)
    #             break
    return b


def raw_data_byts_checkout_2(ser, verbose=True):
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


def bytes_data_strip(b):
    string_n = b.decode()  # decode byte string into Unicode
    string = string_n.strip()  # remove \n and \r
    data = string.split(' ')
    return data

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

if __name__ == "__main__":
    while (1):
        # data_to_save = pd.DataFrame([np.zeros(34)])
        data_list = []
        try:
            ser = serial.Serial('COM12', 115200, timeout=.01)
        except:
            print('Serial Connection Failed, Will Try Again in 3 SECONDS')
            time.sleep(3)
        else:
            if ser.is_open:
                print('Serial Port Opened:\n', ser)
                ser.flushInput()
                time.sleep(1)
            # Read and record the data
            # n_trunck = 3 # how many repeated during readout (adjust in Arduino code)
            i = 0
            while (i < 100):
                data = raw_data_byts_checkout(ser)
                if data:
                    print('data_{}:{}'.format(i, data))
                    print('length:{}'.format(len(data)))
                    i = i + 1
                    data_list.append(data)
                    # if len(data)==34:
                    #     data_to_save.loc[len(data_to_save)] = data
            # data_to_save.to_csv('data_dummy.csv')
            print(data_list)
            print(len(data_list))
            ser.close()
            print('Serial Port Closed')
            break
