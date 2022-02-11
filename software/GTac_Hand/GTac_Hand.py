import argparse
import copy
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
from gtac_config import COLUMNS_RAW_FINGER_DATA
from GTac_Data import gtac_data, gtac_data_analysis
from data_gen import raw_data_byts_checkout_2
from gtac_config import fname_img
from ur10_robot import main_ur10_thread


class gtac_hand:

    def __init__(self, SerialPort, init_mt=False, BaudRate=115200, buffer_size=8):
        # init_motor: whether initialize the motors ar the beginning
        # buffer_size: the buffer size of reading data flow. this can reduce the sharpness of response curve.
        self.SerialPort = SerialPort
        self.BaudRate = BaudRate
        self.ser = self.connect_hand(self.SerialPort, self.BaudRate)
        self.init_mt = init_mt
        if init_mt:
            self.init_motors()
        self.avg = self._init_GTac(DataPoints=300)
        self.FINGERS = gtac_config.FINGER_MOTOR
        self.motors_init = self.avg[-7:-1]
        self.motors_angle = self.motors_init
        self.buffer = deque(maxlen=buffer_size)
        self.contacted_previous_map = np.zeros((gtac_config.FINGER_NUM, gtac_config.SEC_NUM), dtype=bool)
        self.SA_II_ref = np.zeros((gtac_config.MAG_NUM))

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
            data = gtac_data.preprocess_(data)
            data[gtac_data.find_SAII_index(0, 1)[2]] = 0
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
        time.sleep(0.5)

    def move_finger(self, angle, motor):
        # motor(str): see in FINGERS
        # motor(int): 1,2,3,4,5,6
        # print('to move-> MOVE ID:{} DEG:{}'.format(motor, angle))
        if isinstance(motor, str):
            motor_ID = self.FINGERS.index(motor) + 1
        else:
            motor_ID = motor

        command = '<' + str(motor_ID) + str(angle) + '>'
        command = bytes(command.encode('UTF-8'))
        self.ser.write(command)

    def move_all_fingers(self, motors_deg):
        if len(motors_deg) == 6:
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
        data_raw = gtac_data.preprocess_(data_raw)

        # buffer window to de-noise
        gtac_d__ = copy.copy(data_raw)
        gtac_d__[gtac_data.find_SAII_index(0, 1)[2]] = 0
        self.buffer.append(gtac_d__[:gtac_config.ALL_GTAC_NUM])
        data_raw[:gtac_config.ALL_GTAC_NUM] = np.mean(self.buffer, axis=0, dtype=int)  # only buffer the data zone
        # frequency = data_raw[-1]

        if to_avg:
            data_raw[:gtac_config.ALL_GTAC_NUM] = data_raw[:gtac_config.ALL_GTAC_NUM] - self.avg[
                                                                                        :gtac_config.ALL_GTAC_NUM]
        # reduce the FA-I noise from average, below zero.
        data_raw[gtac_config.MAG_NUM:gtac_config.ALL_GTAC_NUM][data_raw[
                                                               gtac_config.MAG_NUM:gtac_config.ALL_GTAC_NUM] < 0] = 0
        if sens_aft_ct:
            # Post-process: sensing after contact.
            data_raw, contacted_map, new_SA_II_ref = gtac_data.sensing_after_contact_post_process_data_frame(
                data_raw,
                self.contacted_previous_map,
                self.SA_II_ref,
                f_sum_th=30)
            self.SA_II_ref = copy.copy(new_SA_II_ref)
            self.contacted_previous_map = copy.copy(contacted_map)

        if len(data_raw) == 292:
            self.motors_angle = data_raw[-7:-1]
        self.data_gtac = copy.copy(data_raw)

        if time_stamp:
            self.data_gtac = np.append(self.data_gtac, time_stamp)
        if verbose:
            print('time of reading:{} ms'.format(round(time.time() - s)))
            print('GTac Hand Data After Pre-process'.format(self.data_gtac))
            print('length:{}'.format(len(self.data_gtac)))

    def find_motors_rotate(self):
        # find how much each motors have rotated
        return self.motors_angle - self.motors_init

    def find_motors_current(self):
        return self.motors_angle

    def disconnect(self):
        if self.init_mt:
            self.init_motors()
        self.ser.close()
        print('GTac-Hand is Disconnected')

    def run(self, q_gtac, q_motors_todo, q_motors_todo2, datapoints=5000, avg_gtac=True, sens_aft_ct=True):
        i = 0
        while i < datapoints:
            i = i + 1
            previous_time = time.time()
            self.read_GTac(to_avg=avg_gtac, verbose=False, sens_aft_ct=sens_aft_ct)
            # print('main thread: read a frame: {}'.format(self.data_gtac))
            ms = int(round((time.time() - previous_time) * 1000))
            # print('main thread - > generated: {} GTac Data; {} ms'.format(i, ms))
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


def _wiping_gesture(q_gtac, q_motors):
    print('start to execute gesture of wiping')
    # hand.pinch()
    # hand.save_GTac()
    # hand.disconnect()
    start_time1 = time.time()
    # hand.init_motors()
    move_thumb = True
    move_fingers = True
    save_data = False
    i = 0
    while True:
        # hand.move_finger(angle=1,motor_ID=5)
        # hand.read_GTac(verbose=True)
        # print('to move')
        i = i + 1
        print('thread 1 - > {}:{}'.format(i, q_gtac.get()))
        q_gtac.task_done()
        delta_time = time.time() - start_time1
        if delta_time > 2 and move_thumb:
            # self.move_finger(45, 1)
            q_motors.put([45, 0, 0, 0, 0, 0])
            move_thumb = False
        if delta_time > 3 and move_fingers:
            # self.move_finger(45, 'Middle')
            # self.move_finger(55, 'Index')
            # hand.move_finger(40,'Little')
            # self.move_finger(45, 'Ring')
            q_motors.put([0, 0, 45, 55, 0, 45])
            move_fingers = False
        if delta_time > 10:
            # self.init_motors()
            # self.disconnect()
            break
    #     # hand.init_GTac(DataPoints=500)
    #     print('Start to save data')
    #     self._save_GTac(period=20, remarks='wiping_clear')
    #     # hand.init_motors()
    #     self.disconnect()


def controller(q_gtac, q_motors, q_ur10_tool_move, data_points=1000):
    data_points_avg = 50

    finger = 0
    sec = 0
    finger_ur = 0
    sec_ur = 1

    dt_list = []
    i = 0
    while i < data_points_avg:
        i = i + 1
        data_gtac__c = q_gtac.get(timeout=1)
        q_gtac.task_done()
        dt_list.append(data_gtac__c)
    avg = np.array(dt_list).mean(axis=0, dtype=int)

    print('Start to control by GTac Finger --> {} Sec --> {}'.format(finger, sec))
    while i < data_points:
        i = i + 1
        data_gtac__c = q_gtac.get(timeout=1)
        q_gtac.task_done()
        data_gtac__c[:gtac_config.ALL_GTAC_NUM] = data_gtac__c[:gtac_config.ALL_GTAC_NUM] - avg[
                                                                                            :gtac_config.ALL_GTAC_NUM]
        # print('thread controller - > {}: got a gtac_data'.format(i))
        motors = [0, 0, 0, 0, 0, 0]
        ur_tool = [0, 0, 0, 0, 0, 0]
        sum, _, _ = gtac_data.find_FAI_sum_press_loc(data_gtac__c, finger, sec)
        sum_ur, _, _ = gtac_data.find_FAI_sum_press_loc(data_gtac__c, finger_ur, sec_ur)
        SAII_vec, SAII_scale = gtac_data.find_SAII(data_gtac__c, finger, sec)
        SAII_vec_ur, SAII_scale_ur = gtac_data.find_SAII(data_gtac__c, finger_ur, sec_ur)
        # print('sum: {}'.format(sum))
        if sum > 500:
            motors[0] = -1
        if sum > 1000:
            motors[0] = 1
        if SAII_vec[0] < -300:
            motors[3] = 1
            motors[2] = 1
        if SAII_vec[0] > 300:
            motors[3] = -1
            motors[2] = -1
        if SAII_vec[1] < -300:
            motors[5] = -1
            motors[4] = -1
            # motors[5] = -1
        if SAII_vec[1] > 300:
            motors[5] = 1
            motors[4] = 1
            # motors[5] = 1
        # if SAII_vec_ur[0] < -300:
        #     Handover = True
        if SAII_vec_ur[0] > 300:
            ur_tool[1] = -0.001
        if SAII_vec_ur[0] < -300:
            ur_tool[1] = 0.001
        if SAII_vec_ur[1] > 300:
            ur_tool[2] = 0.001
        if SAII_vec_ur[1] < -300:
            ur_tool[2] = -0.001
        if sum_ur > 300:
            ur_tool[0] = -0.001
        if sum_ur > 1000:
            ur_tool[0] = 0.001
        # if Handover:
        #     motors = [-5, -5, -5, -5, -5, -5]
        if not q_motors.full():
            q_motors.put(motors)
        if not q_ur10_tool_move.full():
            q_ur10_tool_move.put(ur_tool)


def controller_gtac_tele_grasping(q_gtac, q_motors, q_ur10_tool_move, data_points=1000):
    i = 0

    finger_tele = 0
    sec_tele = 1

    gtac_tele_FAI_max = 0
    gtac_tele_SAII_max = 0
    grasp_coe = 1

    while i < data_points:
        time.sleep(0.02)
        i = i + 1
        data_gtac = q_gtac.get(timeout=1)
        q_gtac.task_done()
        # print('thread controller - > {}: got a gtac_data {}'.format(i, data_gtac))
        motors = [0, 0, 0, 0, 0, 0]
        ur_tool = [0, 0, 0, 0, 0, 0]

        FAI_sum_palm_f1s0, _, _ = gtac_data.find_FAI_sum_press_loc(data_gtac, 1, 0)
        SAII_vec_palm_f1s0, SAII_scale_palm_f1s0 = gtac_data.find_SAII(data_gtac, 1, 0)

        FAI_sum_palm_f2s0, _, _ = gtac_data.find_FAI_sum_press_loc(data_gtac, 2, 0)
        SAII_vec_palm_f2s0, SAII_scale_palm_f2s0 = gtac_data.find_SAII(data_gtac, 2, 0)

        FAI_sum_f0_s2, _, _ = gtac_data.find_FAI_sum_press_loc(data_gtac, 0, 2)
        SAII_vec_f0_s2, SAII_scale_f0_s2 = gtac_data.find_SAII(data_gtac, 0, 2)

        FAI_sum_f1_s1, _, _ = gtac_data.find_FAI_sum_press_loc(data_gtac, 1, 1)
        SAII_vec_f1_s1, SAII_scale_f1_s1 = gtac_data.find_SAII(data_gtac, 1, 1)

        FAI_sum_f1_s2, _, _ = gtac_data.find_FAI_sum_press_loc(data_gtac, 1, 2)
        SAII_vec_f1_s2, SAII_scale_f1_s2 = gtac_data.find_SAII(data_gtac, 1, 2)

        FAI_sum_tele, _, _ = gtac_data.find_FAI_sum_press_loc(data_gtac, finger_tele, sec_tele)
        SAII_vec_tele, SAII_scale_tele = gtac_data.find_SAII(data_gtac, finger_tele, sec_tele)

        if SAII_scale_tele > gtac_tele_SAII_max:
            gtac_tele_SAII_max = SAII_scale_tele
        if FAI_sum_tele > gtac_tele_FAI_max:
            gtac_tele_FAI_max = FAI_sum_tele

        SAII_scale_sum_related = SAII_scale_palm_f1s0 + SAII_scale_f1_s1 + SAII_scale_f1_s2 + SAII_scale_f0_s2 + SAII_scale_palm_f2s0
        FAI_sum_related = FAI_sum_palm_f1s0 + FAI_sum_f1_s1 + FAI_sum_f1_s2 + FAI_sum_f0_s2 + FAI_sum_palm_f2s0

        if gtac_tele_FAI_max > 20 and gtac_tele_SAII_max > 50:  # having this threshold to avoid noise
            print('FAI ratio: {}%; SAII ratio: {}%;FAI MAX: {}; SAII: {}'.format(
                round(FAI_sum_related / gtac_tele_FAI_max, 2) * 100,
                round(SAII_scale_sum_related / gtac_tele_SAII_max, 2) * 100, gtac_tele_FAI_max, gtac_tele_SAII_max))

            if FAI_sum_related < gtac_tele_FAI_max * grasp_coe / 2 and SAII_scale_sum_related < gtac_tele_SAII_max * grasp_coe / 2:
                print('first half')
                motors = [0, 0, 1, 1, 0, 0]
            else:
                print('second half')
                motors = [1, 0, 0, 0, 0, 0]
            if FAI_sum_related > gtac_tele_FAI_max * grasp_coe or SAII_scale_sum_related > gtac_tele_SAII_max * grasp_coe:
                motors = [0, 0, 0, 0, 0, 0]
                print('{}:reach the maximum of tactile feedback for tele-operation '.format(i))

        # execution of the motors command
        if not q_motors.full():
            q_motors.put(motors)
        if not q_ur10_tool_move.full():
            q_ur10_tool_move.put(ur_tool)


def controller_egg_grasping(q_gtac, q_motors, data_points=1000, dq_gsp_state=None, dq_gsp_cmd=None):
    i = 0
    finger_sec_related = [[0, 2],
                          [1, 0],
                          [1, 1],
                          [1, 2],
                          [2, 0],
                          [2, 1],
                          [2, 2],
                          [3, 0],
                          # [3, 1],
                          [3, 2],
                          # [4, 0],
                          # [4, 2],
                          ]
    g_th = 100
    grasp_coe = 1

    while i < data_points:
        # time.sleep(0.01)  # adjust the grasping speed
        print('{}/{}: grasping controller; dq_gsp_cmd: {}'.format(i, data_points, dq_gsp_cmd))
        i = i + 1
        data_gtac = q_gtac.get(timeout=1)
        q_gtac.task_done()
        # print('thread controller - > {}: got a gtac_data {}'.format(i, data_gtac))
        motors = [0, 0, 0, 0, 0, 0]

        g_sum = 0
        for f_c_related in finger_sec_related:
            _, g_fc = gtac_data.find_sec_data(data_gtac, f_c_related[0], f_c_related[1], a=0.6)
            g_sum += g_fc
        g_sum = int(g_sum)
        g_avg = round(g_sum / len(finger_sec_related), 1)
        # print('g ratio: {}%; g sum: {}; g avg: {}'.format(round(g_avg / g_th, 2) * 100, g_sum, g_avg))

        if g_avg < g_th * grasp_coe / 3:
            # print('{}/{}: first half'.format(i, data_points))
            motors = [0, 0, 1, 1, 0, 1]
            if dq_gsp_state is not None:
                dq_gsp_state.append(False)

        elif g_avg < g_th * grasp_coe:
            # print('{}/{}: second half'.format(i, data_points))
            motors = [1, 0, 0, 0, 0, 0]
            if dq_gsp_state is not None:
                dq_gsp_state.append(False)
        else:
            # print('{}/{}: grasped '.format(i, data_points))
            motors = [0, 0, 0, 0, 0, 0]
            if dq_gsp_state is not None:
                dq_gsp_state.append(True)
        # print('dq_gsp_state: {}'.format(dq_gsp_state))
        # execution of the motors command
        if dq_gsp_cmd is None:  # the grasping command is not in arguments
            if not q_motors.full():
                q_motors.put(motors)
        else:
            if len(dq_gsp_cmd) != 0 and dq_gsp_cmd[
                -1] == True:  # the grasping command is in the args, and there is a true command in the deque.
                if not q_motors.full():
                    q_motors.put(motors)

def ctrl_fg_gsp(q_gtac, q_motors, data_points=1000, dq_gsp_state=None, dq_gsp_cmd=None):
    # controller of GTac-Hand, which can achieve force-closed for each finger
    i = 0
    g_th = 100
    gsp_state_count_th = 50
    gsp_state_count = 0
    num_fingers_closed = 0
    finger_to_close_first = [1, 2]
    while i < data_points:
        # time.sleep(0.02)  # adjust the grasping speed
        # print('{}/{}: grasping controller; dq_gsp_cmd: {}'.format(i, data_points, dq_gsp_cmd))
        i = i + 1
        data_gtac = q_gtac.get(timeout=1)
        q_gtac.task_done()
        # print('thread controller - > {}: got a gtac_data {}'.format(i, data_gtac))
        motors = [0, 0, 0, 0, 0, 0]
        gsp_state = [0, 0, 0, 0, 0]
        g_sum = 0
        g_sum_f_list = [0, 0, 0, 0, 0]
        g_fc_array = np.zeros([5, 3])
        for f in range(5):
            g_sum_f = 0
            for s in range(3):
                _, g_fc = gtac_data.find_sec_data(data_gtac, f, s, a=0.3)
                g_fc_array[f, s] = g_fc
                g_sum_f += g_fc
            g_sum_f_list[f] = g_sum_f
            # print('f: {} g_sum: {}'.format(f, g_sum))
            if f == 0 and num_fingers_closed >= len(finger_to_close_first):
                print('Thumb g_sum: {}'.format(g_sum_f))
                if g_sum_f < g_th/2:
                    gsp_state[f] = 0  # the finger is not force-closed
                    motors[gtac_config.FINGER_FLEX_MOTOR_IND[f]] = 1
                    if data_gtac[-6] > 179:
                        motors[1] = 2
                else:
                    gsp_state[f] = 1  # the finger is force-closed

            elif f in finger_to_close_first:
                if g_sum_f < g_th:
                    gsp_state[f] = 0  # the finger is not force-closed
                    motors[gtac_config.FINGER_FLEX_MOTOR_IND[f]] = 1
                else:
                    gsp_state[f] = 1  # the finger is force-closed
        print('gsp_state: {} gsp_state.count(1): {}'.format(gsp_state, gsp_state.count(1)))
        num_fingers_closed = gsp_state.count(1)
        if num_fingers_closed >= len(finger_to_close_first) + 1:  # number of finger in contact reaching the limit
            gsp_state_count += 1
        if gsp_state_count >= gsp_state_count_th:  # wait for several cycles to stop give gsp command
            dq_gsp_state.append(True)
            dq_gsp_cmd.append(False)
        else:
            dq_gsp_state.append(False)
        print('Motors command: {}'.format(motors))
        # print('{}/{}: current g_sum_f_list: {}: g_fc_array:{}'.format(i, data_points, g_sum_f_list, g_fc_array))
        # print('{}/{}: current motor angle:{}'.format(i, data_points, data_gtac[-7:-1]))

        # print('g ratio: {}%; g sum: {}; g avg: {}'.format(round(g_avg / g_th, 2) * 100, g_sum, g_avg))

        # print('dq_gsp_state: {}'.format(dq_gsp_state))
        # execution of the motors command
        if dq_gsp_cmd is None:  # the grasping command is not in arguments
            if not q_motors.full():
                q_motors.put(motors)
        else:
            if len(dq_gsp_cmd) != 0 and dq_gsp_cmd[
                -1] == True:  # the grasping command is in the args, and there is a true command in the deque.
                if not q_motors.full():
                    q_motors.put(motors)



def _save_GTac(q_gtac_save, q_ECS_result_save=None, data_points=5000, save_path='data/', remarks='test'):
    timestr = time.strftime("%Y%m%d_%H%M%S")
    start = time.time()
    dt_list = []
    ECS_result_list = []
    filename = save_path + remarks + '_' + \
               str(data_points) + '_GTAC_' + \
               timestr + '.csv'
    filename_ECS = save_path + remarks + '_' + \
               str(data_points) + '_ECS_results_' + \
               timestr + '.csv'
    wrong_reading = 0
    i = 0
    while i < data_points-10:
        i = i + 1
        ms = int(round((time.time() - start) * 1000))
        print('{}/{} to read a frame, time:{} ms'.format(i, data_points, ms))
        data_gtac = q_gtac_save.get(timeout=1)
        q_gtac_save.task_done()
        # data_gtac.append(ms)
        data_gtac = np.append(data_gtac, ms)

        if q_ECS_result_save is not None:
            ECS_result = q_ECS_result_save.get(timeout=1)
            q_ECS_result_save.task_done()
            ECS_result_list.append(ECS_result)

        # print('save thread: read a frame: {}'.format(data_gtac))
        if len(data_gtac) == len(COLUMNS_RAW_FINGER_DATA):
            # print('read a frame: {}'.format(data_gtac))
            dt_list.append(list(data_gtac))
        else:
            print('Wrong reading: length: {}'.format(len(data_gtac)))
        # print('appended:{},length:{}'.format(list(self.data_gtac),len(list(self.data_gtac))))
    print('Colleted GTac data in {} s of {} frames \n Saving the data into {}'.format(data_points,
                                                                                      len(dt_list),
                                                                                      filename))

    df_RAW = pd.DataFrame(columns=COLUMNS_RAW_FINGER_DATA)
    for i, d in enumerate(dt_list):
        # dummy = q_gtac_save.get(timeout=1)
        # q_gtac_save.task_done()
        # print('length of frame to save: {}'.format(len(d)))
        # print(d)
        if len(d) == len(COLUMNS_RAW_FINGER_DATA):
            df_RAW.loc[len(df_RAW)] = d
            # print('{}/{}'.format(i, len(dt_list) - 1))
            # print('length:{}'.format(len(d)))s
        else:
            wrong_reading = wrong_reading + 1
            # print('Wrong reading: length: {}'.format(len(d)))
    df_RAW.to_csv(filename)
    print('Saved: {}'.format(filename))
    print('Num of wrong reading frames: {}'.format(wrong_reading))
    np_ECS = np.array(ECS_result_list)
    pd.DataFrame(np_ECS).to_csv(filename_ECS)
    print('Saved: {}'.format(filename_ECS))



def switch_img(img, img_handle, fig, title, pause=0.001):
    img_handle.set_data(img)
    plt.title(title, size=36)
    fig.canvas.draw_idle()
    plt.pause(pause)

def multi_clf_predict(clf, data_gtac_285):
    time_start = time.time()
    ML_model_type = (sklearn.discriminant_analysis.QuadraticDiscriminantAnalysis,
                     sklearn.svm._classes.SVC,
                     sklearn.discriminant_analysis.LinearDiscriminantAnalysis,
                     sklearn.linear_model._logistic.LogisticRegression)
    if isinstance(clf, ML_model_type):
        result = clf.predict([data_gtac_285])[0]
    else:
        data = gtac_data_analysis.reshape_for_CNN(data_gtac_285)
        result = gtac_config.CNN_classes[np.argmax(clf.predict(data), axis=-1)[0]]
    time_spent = round((time.time()-time_start)*1000)
    print('Time on classification: {} ms'.format(time_spent))
    return result

def ECS_recognition(q_gtac, q_ECS_result, q_ECS_result_handover, q_ECS_result_save, data_points=5000, dq_gsp_state=None, ECS_clf=None):
    # start to find new average (avg_size) when the state is 'grasped'. Meanthile, put 'none' in the q_ECS_results
    # do ECS recognition on (data - avg) and put the results in.
    i = 0
    dt_list = []
    avg_size = 500
    to_avg_ = True
    result_buffer = deque(maxlen=5)
    if dq_gsp_state is not None:
        while i < data_points:
            i = i + 1
            data_gtac = q_gtac.get(timeout=1)
            q_gtac.task_done()
            data_gtac_285 = data_gtac[:gtac_config.ALL_GTAC_NUM]

            if dq_gsp_state[-2] == False and dq_gsp_state[
                -1] == True:  # the grasp state changed and need refresh the average values
                dt_list = []
                to_avg_ = True
                print('State change to !grasped!')
            if dq_gsp_state[-1] == True and len(dt_list) < avg_size:  # it is yet full to have average value,
                dt_list.append(data_gtac_285)
                print('{}/{}: add data to avg list'.format(len(dt_list), avg_size))
            if len(dt_list) == avg_size and to_avg_:
                gtac_avg = np.mean(dt_list[-int(avg_size/3):], axis=0, dtype=int)  # calculate avg value by the second half
                to_avg_ = False  # the average has been completed
                print('average completed')
            if not to_avg_ and dq_gsp_state[-1] == True:
                data_gtac_285_avg_ed = data_gtac_285 - gtac_avg
                # print('data used to ECS before average: {}'.format(data_gtac_285))
                # print('average data used to ECS: {}'.format(gtac_avg))
                # print('data used to ECS: {}\n'.format(data_gtac_285_avg_ed))
                # result = ECS_clf.predict([data_gtac_285_avg_ed])[0]
                result = multi_clf_predict(clf=ECS_clf, data_gtac_285=data_gtac_285_avg_ed)
                # result_buffer.append(result)
                # result = max(result_buffer, key=result_buffer.count)
                # result_prob = ECS_clf.predict_proba([data_gtac_285_avg_ed])[0]
                print('{}/{}: ECS recognition result: {}\n'.format(i, data_points, result))
                # print('ECS recognition result-probability: {}\n'.format(round(max(result_prob), 2)))
                # data_analysis.LABEL[result]
                ecs_result_save = [result, 1]  # to mark te timing of starting ECS recognition when object being grasped.
            else:
                result = 'none'
                ecs_result_save = [result, 0]  # # to mark te timing of starting ECS recognition when object being grasped.
                # print('The grasping has not been completed')
            if not q_ECS_result.full():
                q_ECS_result.put(result, timeout=1)
            if not q_ECS_result_handover.full():
                q_ECS_result_handover.put(result, timeout=1)
            if not q_ECS_result_save.full():
                q_ECS_result_save.put(ecs_result_save, timeout=1)

    if dq_gsp_state is None:
        while i < data_points:
            i = i + 1
            data_gtac = q_gtac.get(timeout=1)
            q_gtac.task_done()
            data_gtac_285 = data_gtac[:gtac_config.ALL_GTAC_NUM]
            # result = ECS_clf.predict([data_gtac_285])[0]
            result = multi_clf_predict(clf=ECS_clf, data_gtac_285=data_gtac_285)
            print('{}/{}: ECS recognition result: {}\n'.format(i, data_points,result))
            # data_analysis.LABEL[result]
            if not q_ECS_result.full():
                q_ECS_result.put(result, timeout=1)
            if not q_ECS_result_handover.full():
                q_ECS_result_handover.put(result, timeout=1)


def queue_publisher(q_gtac_main, q_gtac_tosave, q_gtac_mornitor, q_gtac_ECS, data_points, dq_stop_sign=None):
    i = 0
    while i < data_points:
        i = i + 1
        # print('publisher thread - > i: {}'.format(i))
        data_gtac = q_gtac_main.get(timeout=1)
        q_gtac_main.task_done()
        # print('publisher thread - > Queue Size of q_gtac: {}'.format(q_gtac_main.qsize()))
        if not q_gtac_tosave.full():
            q_gtac_tosave.put(copy.copy(data_gtac), timeout=1)
            # print('publisher thread - > Queue Size of q_gtac_tosave: {}'.format(q_gtac_tosave.qsize()))
        if not q_gtac_mornitor.full():
            q_gtac_mornitor.put(copy.copy(data_gtac), timeout=1)
            # print('publisher thread - > Queue Size of q_gtac_mornitor: {}'.format(q_gtac_mornitor.qsize()))
        if not q_gtac_ECS.full():
            q_gtac_ECS.put(copy.copy(data_gtac), timeout=1)
    if dq_stop_sign is not None and len(dq_stop_sign) == 0:
        dq_stop_sign.append(True)
        print('Gave a STOP SIGN')

def Handover(q_ECS_result, q_motors, Data_points):
    i = 0
    pull_count = 0
    handover_count_th = 10
    interested_ECS = ['pull', ]
    while i < Data_points:
        i = i + 1
        ECS_result = q_ECS_result.get(timeout=1)
        q_ECS_result.task_done()
        if ECS_result in interested_ECS:
            pull_count += 1
        if pull_count > handover_count_th:
            print('Handover Activated!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            if not q_motors.full():
                q_motors.put('<>')
            pull_count = 0


def grasping_and_handover(q_ur10, dq_ur10_cmd_exc, data_points=5000, dq_g_state=None, dq_gsp_cmd=None, dq_stop_sign=None):
    # this is a finite machine
    phase = 0
    i = 0
    n_decent = 0
    d_decent = 0.001
    d_lift = 0.02
    d_move = 0.1
    goal_tool_phase0_0 = [-d_move, 0, 0, 0, 0, 0]
    goal_tool_phase0_1 = [0, -d_lift, 0, 0, 0, 0]
    goal_tool_phase1 = [0, 0, 0, 0, 0, 0]
    goal_tool_phase2_0 = [0, d_lift, 0, 0, 0, 0]
    goal_tool_phase2_1 = [d_move, 0, 0, 0, 0, 0]
    goal_tool_phase3_ = [0, -d_decent, 0, 0, 0, 0]
    goal_tool_phase4 = [0, n_decent * d_decent + d_lift, 0, 0, 0, 0]
    phase_done = [False, False, False, False, False, False]
    ur_send_exc = 0
    last_ur_send_exc = 0
    num_cycle = 0
    while i < data_points:
        if dq_stop_sign is not None and len(dq_stop_sign) > 0 and dq_stop_sign[-1] == True:
            break
        time.sleep(0.01)
        i += 1
        # print('grasping_and_handover: {}/{}, dq_g_state: {}, dq_gsp_cmd: {}'.format(i, data_points, dq_g_state[-1],
        #                                                                             dq_gsp_cmd))
        # print('phase: {}, phase_done: {}'.format(phase, phase_done))
        if phase == 0 and phase_done[0] == False and dq_g_state[
            -1] == False and ur_send_exc == 0 + last_ur_send_exc:  # approach
            print('phase 0-0')
            print('dq_ur10_cmd_exc[-1]: {}; ur_send_exc: {}'.format(dq_ur10_cmd_exc[-1], ur_send_exc))
            if not q_ur10.full() and dq_ur10_cmd_exc[-1] == ur_send_exc:
                q_ur10.put(copy.copy(goal_tool_phase0_0), timeout=1)
                print('put {} in q_ur10, ur_send_exc: {}'.format(goal_tool_phase0_0, ur_send_exc))
                ur_send_exc += 1
                # time.sleep(5)
        if phase == 0 and phase_done[0] == False and dq_g_state[
            -1] == False and ur_send_exc == 1 + last_ur_send_exc:  # approach
            print('phase 0-1')
            print('dq_ur10_cmd_exc[-1]: {}; ur_send_exc: {}'.format(dq_ur10_cmd_exc[-1], ur_send_exc))
            if not q_ur10.full() and dq_ur10_cmd_exc[-1] == ur_send_exc:
                q_ur10.put(copy.copy(goal_tool_phase0_1), timeout=1)
                ur_send_exc += 1
                phase_done[0] = True  # after sending the last command of phase-0
                phase = 1

        if phase == 1 and phase_done[1] == False and dq_g_state[-1] == False and dq_ur10_cmd_exc[-1] == ur_send_exc:  # start to grasp
            print('phase 1-0')
            time.sleep(3)
            dq_gsp_cmd.append(True)
        if phase == 1 and phase_done[1] == False and dq_g_state[-1] == True:  # The object has been grasped
            print('phase 1-1')
            dq_gsp_cmd.append(False)
            phase_done[1] = True
            phase = 2
        if phase == 2 and phase_done[2] == False and dq_g_state[
            -1] == True and ur_send_exc == 2 + last_ur_send_exc:  # lift and moving
            print('phase 2-1')
            print('dq_ur10_cmd_exc[-1]: {}; ur_send_exc: {}'.format(dq_ur10_cmd_exc[-1], ur_send_exc))
            if not q_ur10.full() and dq_ur10_cmd_exc[-1] == ur_send_exc:
                q_ur10.put(copy.copy(goal_tool_phase2_0), timeout=1)
                ur_send_exc += 1
                # time.sleep(3)
        if phase == 2 and phase_done[2] == False and dq_g_state[-1] == True and ur_send_exc == 3 + last_ur_send_exc:  # lift and moving
            print('phase 2-2')
            print('dq_ur10_cmd_exc[-1]: {}; ur_send_exc: {}'.format(dq_ur10_cmd_exc[-1], ur_send_exc))
            if not q_ur10.full() and dq_ur10_cmd_exc[-1] == ur_send_exc:
                q_ur10.put(copy.copy(goal_tool_phase2_1), timeout=1)
                ur_send_exc += 1
                # time.sleep(5)
                phase_done[2] = True  # after sending the last command of phase-0
                phase = 3
        if phase == 3 and phase_done[3] == False and dq_g_state[
            -1] == True and ur_send_exc == 4 + n_decent + last_ur_send_exc:  # placing/ to handover
            print('phase 3-1')
            print('dq_ur10_cmd_exc[-1]: {}; ur_send_exc: {}'.format(dq_ur10_cmd_exc[-1], ur_send_exc))
            if not q_ur10.full() and dq_ur10_cmd_exc[-1] == ur_send_exc:
                q_ur10.put(copy.copy(goal_tool_phase3_), timeout=1)
                ur_send_exc += 1
                time.sleep(1)
                n_decent += 1  # count how many decent tried
        if phase == 3 and phase_done[3] == False and dq_g_state[-1] == False:  # Handover done
            print('phase 3-2')
            phase_done[3] = True
            phase = 4
        if phase == 4 and phase_done[4] == False:
            print('phase 4')
            print('dq_ur10_cmd_exc[-1]: {}; ur_send_exc: {}, n_decent: {}'.format(dq_ur10_cmd_exc[-1], ur_send_exc,
                                                                                  n_decent))
            if not q_ur10.full() and dq_ur10_cmd_exc[
                -1] == ur_send_exc and ur_send_exc == 4 + n_decent + last_ur_send_exc:
                q_ur10.put(copy.copy(goal_tool_phase4), timeout=1)
                ur_send_exc += 1
                # time.sleep(3)
                phase_done[5] = True
        if phase_done[5] == True:
            phase = 0
            phase_done = [False, False, False, False, False, False]
            last_ur_send_exc = ur_send_exc
            num_cycle += 1
            n_decent = 0
            # ur_send_exc = 0
            print('phase 0-4 Done! num of cycle: {}, last ur_send_exc: {} '.format(num_cycle, last_ur_send_exc))


def main(data_points=1000, serial_port='/dev/ttyACM0', to_save=False, remark='test', ECS_plot=0):
    time_start = time.time()
    hand = gtac_hand(SerialPort=serial_port, init_mt=False, buffer_size=6)
    time_init = time.time()

    q_gtac = Queue(maxsize=10)
    q_gtac_tosave = Queue(maxsize=1)
    q_gtac_ECS = Queue(maxsize=1)
    q_ECS_result = Queue(maxsize=1)
    q_ECS_result_handover = Queue(maxsize=1)
    q_ECS_result_save = Queue(maxsize=1)
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

    gtac_main_thread = threading.Thread(target=hand.run,
                                        name='thread-main',
                                        args=(q_gtac, q_motors_todo, q_motors_todo2, data_points, True))
    # gtac_main_thread.setDaemon(True)
    publisher_thread = threading.Thread(target=queue_publisher,
                                        name='thread-publisher',
                                        args=(q_gtac, q_gtac_tosave, q_gtac_mornitor, q_gtac_ECS, data_points, dq_stop_sign))
    controller_thread = threading.Thread(target=ctrl_fg_gsp,
                                         name='thread-controller',
                                         args=(q_gtac_mornitor, q_motors_todo, data_points, dq_g_state, dq_gsp_cmd))
    save_gtac_thread = threading.Thread(target=_save_GTac,
                                        name='thread-save',
                                        args=(q_gtac_tosave, q_ECS_result_save, data_points, 'data/', remark))
    ECS_recognition_thread = threading.Thread(target=ECS_recognition,
                                              name='thread-ECS',
                                              args=(q_gtac_ECS, q_ECS_result, q_ECS_result_handover, q_ECS_result_save, data_points,
                                                  dq_g_state, ECS_clf))
    ECS_handover_thread = threading.Thread(target=Handover,
                                           name='thread-Handover',
                                           args=(q_ECS_result_handover, q_motors_todo2, data_points))
    ur_thread = threading.Thread(target=main_ur10_thread,
                                 name='thread-ur10',
                                 args=(q_ur10_tool_move, dq_ur10_cmd_exc, data_points,
                                       [[0, 0.15], [-1.08, -1.2], [-0.17, 0.1]], 0.05, 0.05, False,
                                       dq_stop_sign))
    grasping_and_handover_thread = threading.Thread(target=grasping_and_handover,
                                                    name='thread-grasping_and_handover_thread',
                                                    args=(q_ur10_tool_move, dq_ur10_cmd_exc, data_points, dq_g_state,
                                                          dq_gsp_cmd, dq_stop_sign))

    gtac_main_thread.start()
    publisher_thread.start()
    controller_thread.start()
    ECS_recognition_thread.start()
    ECS_handover_thread.start()
    # grasping_and_handover_thread.start()
    # ur_thread.start()
    if to_save:
        save_gtac_thread.start()

    # q_gtac_tosave.join()
    if ECS_plot == 1:
        # Display ECS recognition results in real-time image.
        previous_results = 'none'
        dis_img = mpimg.imread(fname_img[previous_results])
        fig, ax = plt.subplots(1, 1)
        show_img_handle = ax.imshow(dis_img)
        plt.title(previous_results, size=36)
        plt.axis('off')
        plt.pause(0.001)
        j = 0
        while j < data_points:
            result = q_ECS_result.get(timeout=2)
            q_ECS_result.task_done()
            # print('{}/{} --> ECS Recognition Result: {}'.format(j,
            #                                                     data_points,
            #                                                     result))
            if previous_results != result:
                dis_img = mpimg.imread(fname_img[result])
                switch_img(dis_img,
                           img_handle=show_img_handle,
                           fig=fig,
                           title=result)
            previous_results = result
            j += 1

    if ECS_plot == 2:
        # Display ball hitting results in real-time image.
        previous_results = 'none'
        dis_img = mpimg.imread(gtac_config.fname_img_ball[previous_results])
        fig, ax = plt.subplots(1, 1, figsize=(5.5, 9))
        show_img_handle = ax.imshow(dis_img)
        plt.title(previous_results, size=36)
        plt.axis('off')
        plt.pause(0.001)
        j = 0
        while j < data_points:
            result = q_ECS_result.get(timeout=2)
            q_ECS_result.task_done()
            # print('{}/{} --> ECS Recognition Result: {}'.format(j,
            #                                                     data_points,
            #                                                     result))
            if previous_results != result:
                dis_img = mpimg.imread(gtac_config.fname_img_ball[result])
                switch_img(dis_img,
                           img_handle=show_img_handle,
                           fig=fig,
                           title=gtac_config.title_ball[result],
                           pause=1)
                # plt.pause(1)
            previous_results = result
            j += 1

    gtac_main_thread.join()
    publisher_thread.join()
    # save_gtac_thread.join() # not to wait for completion of saving data
    controller_thread.join()
    ECS_recognition_thread.join()
    # ECS_handover_thread.join()
    # grasping_and_handover_thread.join()
    # ur_thread.join()

    hand.disconnect()
    time_finish = time.time()
    print('time_init: {}\ntime_finish: {}'.format(time_init - time_start, time_finish - time_start))


if __name__ == '__main__':
    # parse the argumments
    # sudo chmod 666 /dev/ttyACM0
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--serialport", default='/dev/ttyACM1',
                        help="set serial port (windows: COM6)")  # ubuntu: /dev/ttyACM0
    parser.add_argument("-d", "--data_points", default=3000, type=int,
                        help="set the finger to visualize")
    parser.add_argument("-s", "--save", default=0, type=int,
                        help="set the section to visualize")
    parser.add_argument("-e", "--ECS_plot", default=0, type=int,
                        help="set the section to visualize")
    parser.add_argument("-r", "--remark", default='test',
                        help="set remarks for saving files")
    # Read arguments from command line
    args = parser.parse_args()
    SerialPort, data_points, save, remark, ECS_p = args.serialport, \
                                                   args.data_points, \
                                                   args.save, args.remark, args.ECS_plot

    model_filename = 'model/ECS_logistic_reg_clf_20210811_220802.sav'
    # model_filename = 'model/ECS_logistic_reg_clf_20210831_162821.sav'
    # model_filename = 'model/ECS_LDA_clf_20210831_201017.sav'
    # model_filename = 'model/ECS_QDA_clf_20210901_133920.sav'
    # model_filename = 'model/ECS_SVM_clf_20210901_151035.sav'
    # model_filename = 'model/ECS_CNN_clf_ECS_recognition_20210904_130621'  # trained on two dataset, ECS_holding_bar_20210715 & ECS_holding_bar_20210831
    # model_filename = 'model/ECS_logistic_reg_clf_ECS_recognition_20210913_205117.sav'  # trained on two dataset, ECS_holding_bar_20210715 & ECS_holding_bar_20210831
    # model_filename = 'model/ECS_logistic_reg_clf_ECS_recognition_20210913_221052.sav'  # trained on two dataset, ECS_holding_bar_20210715 & ECS_holding_bar_20210831
    # model_filename = 'model/ECS_logistic_reg_clf_ECS_recognition_20210904_130602.sav'  # used in the grasping and handover egg

    if model_filename[-4:] == '.sav':
        ECS_clf = pickle.load(open(model_filename, 'rb'))
    else:
        ECS_clf = keras.models.load_model(model_filename)

    main(data_points, SerialPort, to_save=save, remark=remark, ECS_plot=ECS_p)
