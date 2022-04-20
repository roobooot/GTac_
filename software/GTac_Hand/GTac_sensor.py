import argparse
import collections
import copy
import os.path
import pickle
import threading
import time
from queue import Queue
from collections import deque

import numpy as np
import pandas as pd
import pylab as plt
import serial

# from matplotlib import pyplot as plt, image as mpimg
import sklearn
from matplotlib import image as mpimg
from tensorflow import keras

import gtac_config
# from GTac_Data import gtac_data, gtac_data_analysis
import GTac_Data
from data_gen import raw_data_byts_checkout_2
from gtac_config import fname_img
from ur10_robot import main_ur10_thread


class gtac_gripper:
    def __init__(self, SerialPort, init_mt=False, BaudRate=115200, buffer_size=8, init_pos=None, save=False, remarks='test'):
        # init_motor: whether initialize the motors ar the beginning
        # buffer_size: the buffer size of reading data flow. this can reduce the sharpness of response curve.
        self.SerialPort = SerialPort
        self.BaudRate = BaudRate
        self.ser = self.connect_hand(self.SerialPort, self.BaudRate)
        self.init_mt = init_mt
        if init_mt:
            self.init_motors()
            if init_pos:
                self.init_pose(init_pos)
        self.avg = self._init_GTac(DataPoints=300)
        self.motors_init = self.avg[-1 - gtac_config.MOTOR_NUM:-1]
        self.motors_angle = self.motors_init
        self.buffer = deque(maxlen=buffer_size)
        self.contacted_previous_map = np.zeros((gtac_config.FINGER_NUM, gtac_config.SEC_NUM), dtype=bool)
        self.SA_II_ref = np.zeros((gtac_config.MAG_NUM))
        self.dt_list = []  # to save
        self.save = save
        save_path = 'data/'
        timestr = time.strftime("%Y%m%d_%H%M%S")
        self.filename = save_path + remarks + '_' + \
                   str(data_points) + '_GTAC_Gripper' + \
                   timestr + '.csv'


    def connect_hand(self, SerialPort='/dev/ttyACM0', BaudRate=115200):
        ser = serial.Serial(SerialPort, BaudRate)
        time.sleep(0.5)
        if ser.is_open:
            print('Serial Port Opened:\n', ser)
            ser.flushInput()
        return ser

    def _init_GTac(self, DataPoints=300):
        # directly dispose a few data as strike noise happens in the head
        i = 0
        while (i < int(DataPoints / 3)):
            data = raw_data_byts_checkout_2(self.ser, verbose=False)
            i = i + 1
        # start to collect data for initialization
        dt_list = []
        i = 0
        while (i < DataPoints):
            data = raw_data_byts_checkout_2(self.ser, verbose=False)
            # data = gtac_data.preprocess_(data)
            # data[gtac_data.find_SAII_index(0, 1)[2]] = 0
            dt_list.append(data)
            i = i + 1
        avg = np.array(dt_list).mean(axis=0, dtype=int)
        print('Initial values of GTac have been found:')
        print(avg)
        return avg

    def init_GTac(self, DataPoints=300):
        # initialize the GTac data anytime
        self.avg = self._init_GTac(DataPoints)

    def init_motors(self):
        self.ser.write(b'<>')
        print('Motors have been initialized')
        time.sleep(1)

    def init_pose(self, motors_deg):
        self.move_all_fingers(motors_deg)
        time.sleep(1)
        print('Gripper pose has been initialized: {}'.format(motors_deg))

    def move_finger(self, angle, motor):
        # motor(str): see in FINGERS
        # motor(int): 1,2,3,4,5,6
        # print('to move-> MOVE ID:{} DEG:{}'.format(motor, angle))
        if angle != 0:
            command = '<' + str(motor) + str(angle) + '>'
            command = bytes(command.encode('UTF-8'))
            self.ser.write(command)

    def move_all_fingers(self, motors_deg):
        if len(motors_deg) == 8:
            for f, d in enumerate(motors_deg):
                self.move_finger(d, f + 1)
        if motors_deg == '<>':
            self.init_motors()

    def pinch(self):
        self.move_finger(70, 'Thumb Fle')
        self.move_finger(30, 'Index')

    def read_GTac(self, time_stamp=None, verbose=False, to_avg=True, sens_aft_ct=True):
        s = time.time()
        data_raw = raw_data_byts_checkout_2(self.ser, verbose=verbose)
        # data_raw = gtac_data.preprocess_(data_raw)

        # buffer window to de-noise
        gtac_d__ = copy.copy(data_raw)
        # gtac_d__[gtac_data.find_SAII_index(0, 1)[2]] = 0
        self.buffer.append(gtac_d__[:gtac_config.ALL_GTAC_NUM])
        data_raw[:gtac_config.ALL_GTAC_NUM] = np.mean(self.buffer, axis=0, dtype=int)  # only buffer the data zone
        self.frequency = data_raw[-1]

        if to_avg:
            data_raw[:gtac_config.ALL_GTAC_NUM] = data_raw[:gtac_config.ALL_GTAC_NUM] - self.avg[
                                                                                        :gtac_config.ALL_GTAC_NUM]  # init GTac data
        # reduce the FA-I noise from average, below zero.
        data_raw[gtac_config.MAG_NUM:gtac_config.ALL_GTAC_NUM][
            data_raw[gtac_config.MAG_NUM:gtac_config.ALL_GTAC_NUM] < 0] = 0
        if sens_aft_ct:
            # Post-process: sensing after contact.
            data_raw, contacted_map, new_SA_II_ref = GTac_Data.gtac_data.sensing_after_contact_post_process_data_frame(
                data_raw,
                self.contacted_previous_map,
                self.SA_II_ref,
                f_sum_th=30)
            self.SA_II_ref = copy.copy(new_SA_II_ref)
            self.contacted_previous_map = copy.copy(contacted_map)
        self.data_gtac = copy.copy(data_raw)
        if time_stamp:
            self.data_gtac = np.append(self.data_gtac, time_stamp)
        if len(data_raw) == gtac_config.ALL_GTAC_NUM + gtac_config.MOTOR_NUM + 2:
            self.motors_angle = data_raw[-2 - gtac_config.MOTOR_NUM:-2]

        if self.save:
            self.dt_list.append(self.data_gtac)
        if verbose:
            print('time of reading:{} ms'.format(round(time.time() - s)))
            print('GTac Gripper data: {}'.format(self.data_gtac))
            print('length:{}'.format(len(self.data_gtac)))
            # print('GTac data after preprocess: {}'.format(self.data_gtac))

    # def find_motors_rotate(self):
    #     # find how much each motors have rotated
    #     return self.motors_angle - self.motors_init

    def find_motors_current(self):
        return self.motors_angle

    def disconnect(self):
        if self.init_mt:
            self.init_motors()
        self.ser.close()
        print('GTac-Gripper is Disconnected')

    def run(self, q_gtac, q_motors_todo, q_motors_todo2, datapoints=5000, avg_gtac=True, sens_aft_ct=True):
        i = 0
        start_time = time.time()
        while i < datapoints:
            i = i + 1
            previous_time = time.time()
            time_stamp = int(round((previous_time-start_time) * 1000))
            self.read_GTac(to_avg=avg_gtac, verbose=True, sens_aft_ct=sens_aft_ct, time_stamp=time_stamp)
            # print('main thread: {}/{} read a frame: {}'.format(i, data_points,self.data_gtac))
            ms = int(round((time.time() - previous_time) * 1000))
            # print('main thread - > generated: {} GTac data; {} ms'.format(i, ms))
            if not q_gtac.full():
                q_gtac.put(self.data_gtac, timeout=1)
                # print('main thread - > Queue Size of q_gtac: {}'.format(q_gtac.qsize()))
            if not q_motors_todo.empty():
                motors = q_motors_todo.get(timeout=1)
                q_motors_todo.task_done()
                # print('main thread - > read motors:{}'.format(motors))
                self.move_all_fingers(motors)
            if not q_motors_todo2.empty():
                motors = q_motors_todo2.get(timeout=1)
                q_motors_todo2.task_done()
                # print('main thread - > read motors:{}'.format(motors))
                self.move_all_fingers(motors)
        if self.save:
            # filename = 'data/Gripper_two_fingered/'+'egg_grasp_2'+'.csv'
            dt_pd = pd.DataFrame(self.dt_list)
            dt_pd.to_csv(self.filename)
            print('Saved {} data frames to in {}'.format(len(dt_pd), self.filename))





def gp_return_sensor_no(NOF):
    # Num of Finger -> f in sensors
    sensor = gtac_config.SENSOR_MAP[NOF % 4]
    return sensor


def main(data_points=1000, serial_port='/dev/ttyACM0', to_save=False, remark='test', ECS_plot=0, NOF_to_move = [0, 1, 2, 3], init_pos=None, init_mt=None):
    time_start = time.time()
    gripper = gtac_gripper(SerialPort=serial_port, init_mt=init_mt, buffer_size=6, init_pos=init_pos,
                           save=to_save, remarks=remark)
    time_init = time.time()

    q_gtac = Queue(maxsize=10)
    q_gtac_tosave = Queue(maxsize=1)
    q_gtac_ECS = Queue(maxsize=1)
    q_ECS_result = Queue(maxsize=1)
    q_ECS_result_handover = Queue(maxsize=1)
    # q_ECS_result_save = Queue(maxsize=1)
    q_gtac_mornitor = Queue(maxsize=1)
    q_ur10_tool_move = Queue(maxsize=2)
    q_motors_todo = Queue()
    q_motors_todo2 = Queue()

    dq_g_state = deque(maxlen=3)
    dq_gsp_cmd = deque(maxlen=2)
    dq_gsp_cmd.append(True)  # give grasping command,  Handover to human
    # dq_gsp_cmd.append(False)  # give grasping command, Handover to table
    dq_ur10_cmd_exc = deque(maxlen=50)
    dq_ur10_cmd_exc.append(0)
    dq_stop_sign = deque(maxlen=1)
    # initialize the deque with full of False
    for i in range(dq_g_state.maxlen):
        dq_g_state.append(False)

    gtac_main_thread = threading.Thread(target=gripper.run,
                                        name='thread-main',
                                        args=(q_gtac, q_motors_todo, q_motors_todo2, data_points, True))

    gtac_main_thread.start()

    gtac_main_thread.join()

    gripper.disconnect()
    time_finish = time.time()
    print('time_init: {}\ntime_finish: {}'.format(time_init - time_start, time_finish - time_start))


if __name__ == '__main__':
    # parse the argumments
    # sudo chmod 666 /dev/ttyACM0
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--serialport", default='/dev/ttyACM0',
                        help="set serial port (windows: COM6)")  # ubuntu: /dev/ttyACM0
    parser.add_argument("-d", "--data_points", default=3000, type=int,
                        help="set the finger to visualize")
    parser.add_argument("-s", "--save", default=0, type=int,
                        help="set the section to visualize")
    parser.add_argument("-e", "--ECS_plot", default=0, type=int,
                        help="set the section to visualize")
    parser.add_argument("-r", "--remark", default='test',
                        help="set remarks for saving files")
    parser.add_argument("-ip", "--init_pose", default=[0, 0, 0, 0, 0, 0, 0, 0], type=int, nargs='+',
                        help="set initial pose")
    parser.add_argument("-nof", "--NOF_tomove", default=[0, 1, 2, 3], type=int, nargs='+',
                        help="set initial pose")
    parser.add_argument("-im", "--init_mt", default=0, type=int,
                        help="whether to init the motor, if not, the pose would not be init either.")
    # Read arguments from command line
    args = parser.parse_args()
    SerialPort, data_points, save, remark, ECS_p, init_pos, NOF_tomove, init_mt = args.serialport, \
                                                             args.data_points, \
                                                             args.save, args.remark, args.ECS_plot, args.init_pose, args.NOF_tomove, args.init_mt


    main(data_points, SerialPort, to_save=save, remark=remark, ECS_plot=ECS_p, init_pos=init_pos, NOF_to_move=NOF_tomove, init_mt=init_mt)
