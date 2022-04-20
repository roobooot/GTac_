from data_gen import raw_data_byts_checkout_2
from data_collect_fingers_five import COLUMNS_RAW_FINGER_DATA, MAG_NUM, COL_INDEX
from Handover import collect_DataPoints, find_location, find_mat_value
import serial
import time
import pandas as pd
import numpy as np
import argparse

def find_mat_sum_sec(data_frame_array,mat_th=50,verbose=False):
    # calculate the sum of resistive signals in each finger section
    # mat_th: the threshold to start to calculate the sum
    mat_index = np.where(data_frame_array[MAG_NUM:-2] > mat_th)[0]  # resistive sensing index above threshold [0,229]
    # print(mat_index)
    mat_sum_sec = np.zeros((5, 3))
    if len(mat_index) != 0:
        for i in mat_index:
            # find_location(i)
            finger, sec, r, c = find_location(i)
            # print([finger, sec, r, c])
            mat_sum_sec[finger, sec] = mat_sum_sec[finger, sec] + \
                                       find_mat_value(data_frame_array,
                                                      finger=finger, sec=sec,
                                                      r=r, c=c)[1]
    if verbose:
        print(mat_sum_sec)
    return mat_sum_sec

def reactive_pinch(data_frame_array,ser,
                   pinch,last_time_02,last_time_12,last_time_12_inv):

    mat_sum_sec = find_mat_sum_sec(data_frame_array,
                                   mat_th=50,
                                   verbose=False)
    if mat_sum_sec[1, 0] > 50 and not pinch:
        pinch = True

    if pinch and mat_sum_sec[0, 2] < 300 and time.time() - last_time_02 > 0.05:
        ser.write(b'<20>')
        last_time_02 = time.time()

    if pinch and mat_sum_sec[1, 2] < 50 and time.time() - last_time_12 > 0.05:
        ser.write(b'<41>')
        ser.write(b'<31>')
        ser.write(b'<51>')
        ser.write(b'<61>')
        last_time_12 = time.time()

    if pinch and mat_sum_sec[1, 2] > 100 and time.time() - last_time_12_inv > 0.05:
        ser.write(b'<4-1>')
        ser.write(b'<3-1>')
        ser.write(b'<5-1>')
        ser.write(b'<6-1>')
        last_time_12_inv = time.time()
    return pinch,last_time_02,last_time_12,last_time_12_inv


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

    THUMB_TO_GRASP = True
    INDEX_TO_GRASP = False
    # init position
    ser.write(b'<>')
    time.sleep(1)

    start = time.time()
    n = 0
    last_time_02 = 0
    last_time_12 = 0
    last_time_12_inv = 0
    handover_index = 0
    handover_index_th = 50
    pinch = False
    init_values = collect_DataPoints(ser, DataPoints=100, starttime=start)
    avg = np.array(init_values).mean(axis=0,dtype=int)
    while(n<DataPoints):
        print('{}/{}'.format(n, DataPoints))
        # collect init values for average
        s = time.time()
        data = raw_data_byts_checkout_2(ser, verbose=False)
        ms = int(round((time.time() - start) * 1000))
        data.append(ms)
        # dt_list.append(data)
        data_frame_array = data - avg # average by the initial data
        mat_sum_sec = find_mat_sum_sec(data_frame_array,
                                       mat_th=50,
                                       verbose=True)
        # find channels of tri-axis signals that are above threshold.
        tri_axis = np.where(abs(data_frame_array[:MAG_NUM]) > 100)[0]
        print(tri_axis)

        if mat_sum_sec[1,0] > 50 and not pinch:
            pinch = True

        if pinch and mat_sum_sec[0,2] < 300 and time.time()-last_time_02 > 0.02:
            ser.write(b'<20>')
            last_time_02 = time.time()

        if pinch and mat_sum_sec[1,2] < 50 and time.time()-last_time_12 > 0.01:
            ser.write(b'<41>')
            ser.write(b'<31>')
            ser.write(b'<51>')
            ser.write(b'<61>')
            last_time_12 = time.time()

        if pinch and mat_sum_sec[1,2] > 100 and time.time()-last_time_12_inv > 0.01:
            ser.write(b'<4-1>')
            ser.write(b'<3-1>')
            ser.write(b'<5-1>')
            ser.write(b'<6-1>')
            last_time_12_inv = time.time()

        # if n > 2000:
        #     if 9 in tri_axis or 0 in tri_axis:
        #         handover_index = handover_index + 1
        #     if handover_index > handover_index_th :
        #         ser.write(b'0')
        #         # TO_INIT = False
        #         break
        n = n +1
    ser.write(b'<>')
    print('Time Spent: {}'.format(time.time()-start))