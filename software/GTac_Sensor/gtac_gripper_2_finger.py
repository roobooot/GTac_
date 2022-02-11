#! /usr/bin/env python
import math
import threading
import time
from math import pi
from queue import Queue

from matplotlib import pyplot as plt
import numpy as np
import serial
import pandas as pd
from software.GTac_Sensor.data_gen_gp2 import raw_data_byts_checkout_2
import collections
from collections import deque
import gtac_config_gp2

# sudo chmod 666 /dev/ttyACM0
# d = mz = 25mm, L = theta* r = 58.9mm,

L = 25 / 2 * 1.5 * pi
resolution = L / (2500 - 500)  # mm/deg
min_pos = 500
dex_pos = 900
home_position = 900
max_pos = 2500
NUM_data = 41
nom = 2
COLUMNS_RAW_GRIPPER_DATA = ['mag_x1', 'mag_y1', 'mag_z1',
                            'mag_x2', 'mag_y2', 'mag_z2',
                            'mat1', 'mat2', 'mat3', 'mat4',
                            'mat5', 'mat6', 'mat7', 'mat8',
                            'mat1', 'mat2', 'mat3', 'mat4',
                            'mat5', 'mat6', 'mat7', 'mat8',
                            'mat1', 'mat2', 'mat3', 'mat4',
                            'mat5', 'mat6', 'mat7', 'mat8',
                            'mat1', 'mat2', 'mat3', 'mat4',
                            'mat5', 'mat6', 'mat7', 'mat8',
                            'servo_1', 'servo_2',
                            'Hz', 'milliseconds']




def distance2deg(x):
    return round(x / resolution)

def inrange(dest, max_p, min_p):
    flag = False
    if max_p >= dest >= min_p:
        flag = True
    return flag

def data_process(data):
    force = [np.sum(data[6:22]), np.sum(data[22:38])]
    return force

def shear_process(data, force, coefficiency=0.2):
    s1 = sum(data[i] ** 2 for i in range(2))
    s2 = sum(data[i + 3] ** 2 for i in range(2))
    s1 = (coefficiency * force[0] + (1 - coefficiency) * data[2]) ** 2 + s1
    s2 = (coefficiency * force[1] + (1 - coefficiency) * data[5]) ** 2 + s2
    shear = [np.sqrt(s1), np.sqrt(s2)]
    return shear

def pid(num, f_d, err, x_n):
    #
    kp = -5.2 / f_d
    ki = 0.0001 / f_d
    kd = 2.8 / f_d  # -3
    a = 0.5
    # condition: shear < 4f_d, namely error = f_d - shear > -3*f_d
    # if error[-1, num - 1] > -3 * f_d:
    proportion = kp * (err[-nom + num - 1] - err[-2 * nom + num - 1])
    integral = ki * err[-nom + num - 1]
    derivative = kd * (err[-nom + num - 1] - 2 * err[-2 * nom + num - 1] + err[-2 * nom + num - 1])
    x_delta = proportion + integral + derivative
    x_n[num - 1] = x_delta + x_n[num - 1]
    print('x_{}: {}, x_delta: {}, error:{}'.format(num, x_n[num - 1], x_delta, err[-nom + num - 1]))
    return num, x_n

class gripper_2finger:
    def __init__(self, SerialPort, init_mt=False, BaudRate=115200, buffer_size=8, verbose=True):  # port name, baudrate, timeout
        self.verbose = verbose # global verbose option, mute it or not.
        self.x_n = np.zeros(2)
        self.SerialPort = SerialPort
        self.BaudRate = BaudRate
        self.ser = self.connect_frame(self.SerialPort, self.BaudRate)
        self.init_mt = init_mt
        self.dt_list = []
        self.force = np.array([0, 0], dtype=int)
        self.shear = np.array([0, 0], dtype=int)
        if init_mt:
            self.init_motors()
        self.avg = self._init_GTac(DataPoints=400)
        self.previoustime = time.time()
        # self.positions = self.avg[-3:-1]
        self.start = time.time()
        # self.error = np.array([0, 0], dtype=int)
        # self.gap = np.array([3140])
        self.buffer = collections.deque(maxlen=buffer_size)
        self.f1_pos = 0
        self.f2_pos = 0
        self.T_pos = 100

    def connect_frame(self, SerialPort='/dev/ttyACM0', BaudRate=115200):
        # s = serial.Serial('/dev/ttyACM0', 115200, timeout=0)    # for ubuntu 16
        s = serial.Serial(SerialPort, BaudRate, timeout=0)  # for windows
        time.sleep(0.5)
        if s.is_open:
            print('Serial Port Opened:\n', s)
            s.flushInput()
        return s

    def _init_GTac(self, DataPoints=300):
        # directly dispose a few data as strike noise happens in the head
        i = 0
        while (i < int(DataPoints / 3)):
            data = raw_data_byts_checkout_2(self.ser, verbose=self.verbose)
            i = i + 1
        dt_list = []
        i = 0
        while i < DataPoints:
            data = raw_data_byts_checkout_2(self.ser, verbose=self.verbose)
            dt_list.append(data)
            i = i + 1
        avg = np.array(dt_list).mean(axis=0, dtype=int)
        if self.verbose:
            print('Initial values of GTac have been found:')
            print(avg)
            print('Length: {}'.format(len(avg)))
        return avg

    @staticmethod
    def find_FAI_index_gp(finger, sec, r, c):
        # the FAI index exclude the mag data
        # the overall index is "output"+NUM_MAG
        index = sec * 4 * 8 + finger * 4 + \
                gtac_config_gp2.MAT_ORIENT_COL[finger, sec, r, c] * 8 + \
                gtac_config_gp2.MAT_ORIENT_ROW[finger, sec, r, c]
        return index + gtac_config_gp2.MAG_NUM

    @staticmethod
    def find_FAI_value(data_frame_array, finger, sec, r, c):
        index = gripper_2finger.find_FAI_index_gp(finger, sec, r, c)
        return index, data_frame_array[index]

    @staticmethod
    def find_SAII_gp(data_frame_array, finger, sec):
        # print('SAII_data: finger {}, sec {}'.format(finger, sec))
        tri_index = finger * 3 + sec * 3
        mag_x = data_frame_array[tri_index]
        mag_y = data_frame_array[tri_index + 1]
        mag_z = data_frame_array[tri_index + 2]
        SAII_scaler = math.sqrt(mag_x * mag_x + mag_y * mag_y + mag_z * mag_z)
        # print('Find_SAII: {} scalar: {}'.format([mag_x, mag_y, mag_z], SAII_scaler))
        return [mag_x, mag_y, mag_z], SAII_scaler

    @staticmethod
    def find_sec_data(data_frame_array, finger, sec, a=0.1):
        # Input: data frame
        # Output: the GTac data in one finger section, shape = 19 [f16,s3]
        sec_data = []
        for i in range(gtac_config_gp2.MAT_NUM):  # MAT_NUM -> 16: there 4*4 sensing points on FA-I layer
            r = i // 4
            c = i % 4
            index, value = gripper_2finger.find_FAI_value(data_frame_array, finger, sec, r, c)
            sec_data.append(value)
        FA_sum = np.sum(sec_data)
        mag_all, _ = gripper_2finger.find_SAII_gp(data_frame_array, finger, sec)
        g = math.sqrt(mag_all[0] * mag_all[0] + mag_all[1] * mag_all[1] + (a * mag_all[2] + (1 - a) * FA_sum) * (
                a * mag_all[2] + (1 - a) * FA_sum))
        g = round(g, 2)
        for m in mag_all:
            sec_data.append(m)
        return sec_data, g

    def load_data(self):
        ms = int(round((time.time() - self.start) * 1000))
        data = raw_data_byts_checkout_2(self.ser, verbose=self.verbose)
        data[:38] = np.subtract(data[:38], self.avg[:38])
        # data[5] = np.negative(data[5])
        # data[6:38] = np.subtract(data[6:38], self.avg[6:38])
        data.append(ms)
        # gtac_d = copy.copy(data)
        self.buffer.append(data[:38])
        data[:38] = np.mean(self.buffer, axis=0, dtype=int)
        self.data_gtac = data
        if self.verbose:
            print('data: {}'.format(self.data_gtac))
        self.dt_list.append(self.data_gtac)
        return data
        # self.gtac_data_process(f_d, data)
        #
        # predict_with_QDA(a[:, :19], remark='Test_A')

    def gtac_data_process(self, f_d, data):
        # self.positions = np.append(self.positions, data[-4:-2])
        self.force = np.append(self.force, np.array(data_process(data)))
        self.shear = np.append(self.shear, shear_process(data, self.force[-2:]))
        # self.error = np.append(self.error, [0.8*f_d - self.force[-2], 0.8*f_d - self.force[-1]])
        self.error = np.append(self.error, [0.9 * f_d - self.shear[-2], 0.9 * f_d - self.shear[-1]])
        # return data
        gap = np.subtract(data[-4], 1840)
        gap = np.add(gap, data[-3])
        self.gap = np.append(self.gap, gap)

    def init_motors(self):
        self.ser.write(b'<>')
        print('Motors have been initialized')
        time.sleep(0.5)

    # def move_frame(self, NOM, dist):
    #     deg = distance2deg(dist)
    #     cmd = '<' + str(NOM) + str(deg) + '>'
    #     print('motion cmd: {}'.format(cmd))
    #     cmd = bytes(cmd.encode('UTF-8'))
    #     self.ser.write(cmd)

    # def check_finger_safety(self):
    #     if self.f1_pos + self.f2_pos < self.T_pos:
    #         return True
    #     else:
    #         print('Fingers reached the limits, current pos: left {}; right {}'.format(self.f1_pos, self.f2_pos))
    #         return False

    # def move_frame_deg(self, NOM, deg):
    #     if NOM == 1:
    #         self.f1_pos = self.f1_pos + deg
    #     if NOM == 2:
    #         self.f2_pos = self.f2_pos + deg
    #     if self.check_finger_safety():
    #         cmd = '<' + str(NOM) + str(np.round(deg)) + '>'
    #         cmd = bytes(cmd.encode('UTF-8'))
    #         self.ser.write(cmd)
    #     else:
    #         self.f1_pos = self.f1_pos - deg
    #         self.f2_pos = self.f2_pos - deg

    def move_finger(self, motor, angle):
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
        if len(motors_deg) == 2:
            for f, d in enumerate(motors_deg):
                self.move_finger(f + 1, d)
        if motors_deg == '<>':
            self.init_motors()

    def sensor_test(self, f_boundry, Data_Points=1500):
        i = 0
        while i < Data_Points:
            self.load_data()
            if self.force[-2] < f_boundry:
                self.move_frame(1, -0.029)
            if self.force[-1] < f_boundry:
                self.move_frame(2, -0.029)
            # else:
            #     self.move_frame(1, 0.029)
            i = i + 1

    def FC_grasp(self, Data_Points=2000):
        i = 0
        while i < Data_Points:
            data = self.load_data()
            ind = gripper_2finger.find_FAI_index_gp(0, 0, 2, 3)
            print(data[ind])
            # self.move_frame_deg(1, 1)
            # self.move_frame_deg(2, 1)
            i = i + 1


    def p_controller(self, fd, Data_Points):
        kp = -0.006
        b = 0
        reach = False
        i = 0

        while i < Data_Points:
            self.load_data()
            x1 = kp * (fd - self.force[0]) + b
            x2 = kp * (fd - self.force[1]) + b
            self.move_frame(1, x1)
            self.move_frame(2, x2)
            i = i + 1
            # if self.force[0] < fd:
            #     x = kp*(fd-self.force[0])+b
            #     self.move_frame(1, x)
            #     # print('x is {}, current position: {}, force is {}'.format(x, self.positions[num-1], self.force[
            #     # num-1]))
            # if self.force[1] < fd:
            #     x = kp*(fd-self.force[1])+b
            #     self.move_frame(2, x)
            # else:
            #     break

    def PID_controller(self, f_d, Data_Points, x_d=0):
        kp = -3 / f_d
        ki = 0.000000 / f_d
        kd = -3 / f_d
        i = 0
        a = 0.5
        self.load_data(0)
        self.load_data(20)
        flag = False
        while i < Data_Points:
            i = i + 1
            self.load_data(f_d)
            if self.shear[-2] < 5 * f_d and i < 2000:
                x1 = kp * (np.array(self.error[-2])) \
                     + ki * np.array(self.error[-2]) \
                     + kd * (np.array(self.error[-2]) - 2 * np.array(self.error[-4])
                             + np.array(self.error[-6]))
                # self.x_n[0] = x_s1 + x1
                self.x_n[0] = a * self.x_n[0] + (1 - a) * x1
                self.move_frame_deg(1, self.x_n[0])
            if self.shear[-1] < 5 * f_d:
                x2 = kp * (np.array(self.error[-1])) \
                     + ki * np.array(self.error[-1]) \
                     + kd * (np.array(self.error[-1]) - 2 * np.array(self.error[-3])
                             + np.array(self.error[-5]))
                # self.x_n[1] = x_s2 + x2
                self.x_n[1] = a * self.x_n[1] + (1 - a) * x2
                self.move_frame_deg(2, self.x_n[1])
            if i > 1500:
                if self.positions[-2] < 2000:
                    self.move_frame_deg(1, 1)
                if self.positions[-2] == 1999:
                    flag = True
                if flag:
                    self.move_frame_deg(1, -1)
            print('{}: p1: {}, p2: {}'.format(i, self.positions[0], self.positions[1]))
            print('   x1: {}, x2: {}'.format(self.x_n[0], self.x_n[1]))

    def closure(self, force, Data_Points=1000):

        # self.p_controller(force, Data_Points)
        self.PID_controller(force, Data_Points)
        # while self.force[0] < f1 - 5:

    def save_to_file(self, save_path='data/data_collection/', remarks='test', save=True):
        timestr = time.strftime("%Y%m%d_%H%M%S")
        # timestr=''
        filename = save_path + remarks + '_' + \
                   str(len(self.dt_list)) + '_GTAC_' + \
                   timestr + '.csv'
        print('Colleted GTac data in {} frames \n Saving the data into {}'.format(len(self.dt_list), filename))
        df_RAW = pd.DataFrame(columns=COLUMNS_RAW_GRIPPER_DATA)
        for i, d in enumerate(self.dt_list):
            df_RAW.loc[len(df_RAW)] = d
        if save:
            df_RAW.to_csv(filename)
        print('Saved: {}'.format(filename))
        return filename, df_RAW

    def plot_gripper_data(self, data_pd):
        if isinstance(data_pd, np.ndarray):
            data_np = data_pd
        else:
            data_np = data_pd.values

        fig, axs = plt.subplots(4, 1, figsize=(5, 4), sharex=True, sharey=False, constrained_layout=True)
        axs[0].plot(data_np[:, 0], label='SAII-X')
        axs[0].plot(data_np[:, 1], label='SAII-Y')
        axs[0].plot(data_np[:, 2], label='SAII-Z')
        # axs[0].plot(self.force[::2], label='F1')
        axs[0].set_title('Finger-1')
        axs[0].legend(loc=1)

        axs[1].plot(data_np[:, 3], label='SAII-X')
        axs[1].plot(data_np[:, 4], label='SAII-Y')
        axs[1].plot(data_np[:, 5], label='SAII-Z')
        # axs[1].plot(self.force[1::2], label='F2')
        axs[1].set_title('Finger-2')
        axs[1].legend(loc=1)

        # axs[2].plot(data_np[:, 6:22].sum(axis=1), label='force1')
        # axs[2].plot(data_np[:, 22:38].sum(axis=1), label='force2')
        axs[2].plot(self.shear[::2], label='g1')
        axs[2].plot(self.shear[1::2], label='g2')
        axs[2].set_title('Force')
        axs[2].legend(loc=1)

        # axs[3].plot(-0.029 * (data_np[:, 38] - 920), label='Pos_1')
        # axs[3].plot(0.029 * (data_np[:, 39] - 920), label='Pos_2')
        # axs[3].plot(0.029 * self.gap, label='gap')
        # axs[3].set_title('Positions')
        # axs[3].legend(loc=1)

    def demo1(self, Data_Points=200):
        self.load_data(f_d=0)
        self.load_data(f_d=0)
        f = 120
        num1, xn = pid(1, f, self.error, np.zeros(nom))
        num2, xn = pid(2, f, self.error, xn)
        for i in range(3000):
            i = i + 1
            if i < 1000:
                self.move_frame_deg(num1, xn[num1 - 1])
                self.move_frame_deg(num2, xn[num2 - 1])
                self.load_data(f_d=f)
            else:
                if i < 1800:
                    self.move_frame_deg(num1, 1)
                    self.move_frame_deg(num2, xn[num2 - 1])
                    self.load_data(f_d=round(1.4 * f))
                else:
                    if i < 3000:
                        self.move_frame_deg(num1, -1)
                        self.move_frame_deg(num2, xn[num2 - 1])
                        self.load_data(f_d=round(0.7 * f))
            num1, xn = pid(1, f, self.error, xn)
            num2, xn = pid(2, f, self.error, xn)

    def demo3(self, Data_Points=2000, f=40):
        self.load_data(f_d=0)
        self.load_data(f_d=0)
        num1, xn = pid(1, f, self.error, np.zeros(nom))
        num2, xn = pid(2, f, self.error, xn)
        for i in range(1500):
            i = i + 1
            print("{}".format(i))
            self.move_frame_deg(num1, xn[num1 - 1])
            self.move_frame_deg(num2, xn[num2 - 1])
            self.load_data(f_d=f)
            num1, xn = pid(1, f, self.error, xn)
            num2, xn = pid(2, f, self.error, xn)
            p1 = self.positions[-2]
        # self.demo2(kf=1, xd=p1)

    def stiffness_control(self, num, f_d, kf: float):
        xd = round(f_d / kf)
        return num, xd

    def demo2(self, Data_Points: int = 200, kf: float = 2, xd: int = 1500):
        f = 100
        self.load_data(f_d=f)

        # self.move_frame_deg(1, xd-home_position)
        # self.move_frame_deg(2, -1000)
        # time.sleep(3)
        num1, x_delta = self.stiffness_control(1, self.shear[-2] - f, kf)
        for i in range(3000):
            i = i + 1
            x = x_delta + xd - self.positions[-2]
            self.move_frame_deg(num1, x)
            self.move_frame_deg(2, -x)
            self.load_data()
            if not inrange(self.shear[-2], self.shear[-4] + 10, self.shear[-4] - 10):
                num1, x_delta = self.stiffness_control(num1, self.shear[-2] - f, kf)
            else:
                x_delta = -xd + self.positions[-2]
            print('{}: X_send = {}, x_delta: {}'.format(i, x_delta + xd - self.positions[-2], x_delta))

    def data_collection(self, f_d=100, Data_Points=1500):
        j = 0
        for i in range(Data_Points):
            self.load_data()
            print("g1: {}, g2: {}".format(self.shear[-2], self.shear[-1]))
            if self.shear[-2] < 0.8*f_d:
                self.move_frame_deg(1, -1)
            if self.shear[-1] < 0.8*f_d:
                self.move_frame_deg(2, -1)

    def disconnect(self):
        if self.init_mt:
            self.init_motors()
        self.ser.close()
        print('GTac-Gripper is Disconnected')

    def run(self, q_gtac, q_motors_todo, q_motors_todo2, datapoints=5000, to_save=True, filename='data/test_gp_2f.csv', avg_gtac=True, sens_aft_ct=True):
        print('--- Main cycle of Gripper is running ---')
        i = 0
        while i < datapoints:
            i = i + 1
            previous_time = time.time()
            self.load_data()
            # self.read_GTac(to_avg=avg_gtac, verbose=False, sens_aft_ct=sens_aft_ct)
            # print('main thread: read a frame: {}'.format(self.data_gtac))
            # ms = int(round((time.time() - previous_time) * 1000))
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
            # time.sleep(0.05)
        if to_save:
            # filename = 'data/Gripper_two_fingered/'+'egg_grasp_2'+'.csv'
            dt_pd = pd.DataFrame(self.dt_list)

            dt_pd.to_csv(filename)
            print('Saved {} data frames to in {}'.format(len(dt_pd), filename))


def ctrl_fg_gsp(q_gtac, q_motors, data_points=1000, dq_gsp_state=None, dq_gsp_cmd=None, t_release=120000):
    # controller of GTac-Hand, which can achieve force-closed for each finger
    i = 0
    g_th = 1700
    motor_speed_inv = 15
    gsp_state_count_th = 50
    gsp_state_count = 0
    num_fingers_closed = 0
    finger_to_close = [0, 1]
    released = False
    while i < data_points:
        # time.sleep(0.02)  # adjust the grasping speed
        print('{}/{}: fc-grasping controller; dq_gsp_cmd: {}'.format(i, data_points, dq_gsp_cmd))
        i = i + 1
        data_gtac = q_gtac.get(timeout=1)
        q_gtac.task_done()
        print('fc-grasping controller - > {}: got a gtac_data {}'.format(i, data_gtac))
        motors = [0, 0]
        gsp_state = [0, 0]
        g_sum = 0
        g_sum_f_list = [0, 0]
        g_fc_array = np.zeros([2, 1])
        for f in range(2):
            g_sum_f = 0
            for s in range(1):
                _, g_fc = gripper_2finger.find_sec_data(data_gtac, f, s, a=0.3)
                g_fc_array[f, s] = g_fc
                g_sum_f += g_fc
            g_sum_f_list[f] = g_sum_f
            # print('f: {} g_sum: {}'.format(f, g_sum))
            if num_fingers_closed < len(finger_to_close):
                print('Finger {} g_sum: {}, threshold: {}'.format(f, g_sum_f, g_th))
                if g_sum_f < g_th:
                    gsp_state[f] = 0  # the finger is not force-closed
                    if i % motor_speed_inv == 0:
                        motors[f] = 1
                else:
                    gsp_state[f] = 1  # the finger is force-closed

            # elif f in finger_to_close_first:
            #     if g_sum_f < g_th:
            #         gsp_state[f] = 0  # the finger is not force-closed
            #         motors[gtac_config.FINGER_FLEX_MOTOR_IND[f]] = 1
            #     else:
            #         gsp_state[f] = 1  # the finger is force-closed
        print('gsp_state: {} gsp_state.count(1): {}'.format(gsp_state, gsp_state.count(1)))
        num_fingers_closed = gsp_state.count(1)
        if num_fingers_closed >= len(finger_to_close):  # number of finger in contact reaching the limit
            gsp_state_count += 1
        if gsp_state_count >= gsp_state_count_th:  # wait for several cycles to stop give gsp command
            dq_gsp_state.append(True)
            dq_gsp_cmd.append(False)
        else:
            dq_gsp_state.append(False)
        if i % motor_speed_inv == 0:
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
            if len(dq_gsp_cmd) != 0 and dq_gsp_cmd[-1] == True:  # the grasping command is in the args, and there is a true command in the deque.
                if not q_motors.full():
                    q_motors.put(motors)
        if not released and data_gtac[-1] > t_release:
            print('!!!!!!!!!!!!!!!!1time to release!!!!!!!!!!!!!')
            if not q_motors.full():
                q_motors.put('<>')  # release
            released = True  # stop the gripper


def gsp_clamp(q_gtac, q_motors, data_points=1000, t_cycle_list=None, t_end=120000):
    # controller of GTac-Hand, which can achieve force-closed for each finger to grasp tweezer
    if t_cycle_list is None:
        t_cycle_list = [6000, 18000, 2000]
    i = 0
    g_th_low = 500  # low boundary for tactile signals (g) to hold the clamp
    g_th_low_list = [500, 500]  # low boundary for tactile signals (g) to hold the clamp
    g_th_high = 1000  # high boundary fro tactile signals (g) to close the clamp
    g_th_high_list = [900, 1799]  # high boundary fro tactile signals (g) to close the clamp

    motor_speed_inv = 15
    gsp_state_count_th = 50
    gsp_state_count = 0
    num_fingers_closed = 0
    finger_to_close = [0, 1]
    ended = False
    clamp_state = 0  # clamp states: 0, to close clamp to th_high; 1, to release to th_low;
    gsp_cmd = None
    t_closed_timed = False
    t_released_timed = False
    t_closed = None
    t_released = None
    cycled_num = 0
    while i < data_points:
        # time.sleep(0.02)  # adjust the grasping speed
        print('{}/{}: fc-grasping controller; dq_gsp_cmd: {}'.format(i, data_points, gsp_cmd))
        i = i + 1
        data_gtac = q_gtac.get(timeout=1)
        q_gtac.task_done()
        print('fc-grasping controller - > {}: got a gtac_data {}'.format(i, data_gtac))
        motors = [0, 0]
        gsp_state = [0, 0]  # the states to grasp in clamp state-0
        release_state = [0, 0]  # the states to release in clamp state-1
        g_sum = 0
        g_sum_f_list = [0, 0]
        t_cycle = t_cycle_list[cycled_num]
        for f in range(2):
            g_sum_f = 0
            for s in range(1):
                _, g_fc = gripper_2finger.find_sec_data(data_gtac, f, s, a=0.3)
                g_sum_f += g_fc
            g_sum_f_list[f] = g_sum_f
            # print('f: {} g_sum: {}'.format(f, g_sum))
            if clamp_state == 0:
                print('clamp_state: {}; Finger {} g_sum: {}; threshold high: {}'.format(clamp_state, f, g_sum_f, g_th_high_list[f]))
                if g_sum_f < g_th_high_list[f]:
                    gsp_state[f] = 0  # the finger has not reach the threshold
                    if i % motor_speed_inv == 0:
                        motors[f] = 1
                else:
                    gsp_state[f] = 1  # the finger has not reach the threshold
            if clamp_state == 1:
                print('clamp_state: {}; Finger {} g_sum: {}; threshold low: {}'.format(clamp_state, f, g_sum_f, g_th_low_list[f]))
                if g_sum_f > g_th_low_list[f]:
                    release_state[f] = 0  # the finger has not reach the threshold
                    if i % motor_speed_inv == 0:
                        motors[f] = -1
                else:
                    release_state[f] = 1  # the finger has not reach the threshold
        print('gsp_state: {} gsp_state.count(1): {}'.format(gsp_state, gsp_state.count(1)))
        if i % motor_speed_inv == 0:
            print('Motors command: {}'.format(motors))
        # print('{}/{}: current g_sum_f_list: {}: g_fc_array:{}'.format(i, data_points, g_sum_f_list, g_fc_array))
        # print('{}/{}: current motor angle:{}'.format(i, data_points, data_gtac[-7:-1]))

        # print('g ratio: {}%; g sum: {}; g avg: {}'.format(round(g_avg / g_th, 2) * 100, g_sum, g_avg))

        # print('dq_gsp_state: {}'.format(dq_gsp_state))
        if clamp_state == 0 and gsp_state == [1, 1]:
            if t_closed is None:
                t_closed = time.time()  # record the moment of closed clamp
            motors = [0, 0]  # not moving before next cycle
        if t_closed is not None and time.time() - t_closed > t_cycle/1000:
            clamp_state = 1  # to release the clamp
            t_closed = None
        if clamp_state == 1 and release_state == [1,1]:
            if t_released is None:
                t_released = time.time()  # record the moment of released clamp
            motors = [0, 0]  # not moving before next cycle
        if t_released is not None and time.time() - t_released> t_cycle/1000:
            clamp_state = 0  # to close the clamp
            t_released = None
            cycled_num = cycled_num + 1

        # execution of the motors command
        if not q_motors.full() and not ended:
            q_motors.put(motors)
        # to fully release the gripper after a preset period
        if not ended and data_gtac[-1] > t_end:
            print('!!!!!!!!!!!!!!!!1time to release!!!!!!!!!!!!!')
            if not q_motors.full():
                q_motors.put('<>')  # release
            ended = True  # stop the gripper

def main(data_points=1000, serial_port='/dev/ttyACM0', to_save=False, filename='data/test_gp_2f.csv', remark='test',):
    time_start = time.time()
    gripper = gripper_2finger(SerialPort=serial_port, init_mt=True, verbose=False)
    time_init = time.time()

    q_gtac = Queue(maxsize=10)
    q_gtac_mornitor = Queue(maxsize=1)
    q_ur10_tool_move = Queue(maxsize=2)
    q_motors_todo = Queue()
    q_motors_todo2 = Queue()

    dq_g_state = deque(maxlen=3)
    dq_gsp_cmd = deque(maxlen=2)
    dq_gsp_cmd.append(True)  # give grasping command,  Handover to human

    gtac_main_thread = threading.Thread(target=gripper.run,
                                        name='thread-main',
                                        args=(q_gtac, q_motors_todo, q_motors_todo2, data_points, to_save, filename))
    fc_grasp_thread = threading.Thread(target=ctrl_fg_gsp,
                                         name='thread-ctrl_fg_gsp',
                                         args=(q_gtac, q_motors_todo, data_points, dq_g_state, dq_gsp_cmd, 1000000))
    gsp_clamp_thread = threading.Thread(target=gsp_clamp,
                                         name='thread-gsp_clamp',
                                         args=(q_gtac, q_motors_todo, data_points, [10000, 21000, 2000], 600000))

    gtac_main_thread.start()
    fc_grasp_thread.start()
    # gsp_clamp_thread.start()

    gtac_main_thread.join()
    fc_grasp_thread.join()
    # gsp_clamp_thread.join()

    gripper.disconnect()
    time_finish = time.time()
    print('time to initialize: {}\ntime to finish: {}'.format(time_init - time_start, time_finish - time_start))


if __name__ == "__main__":
    #  init position
    print('the resolution is {} mm/deg'.format(resolution))
    # ser.set_buffer_size(rx_size=1, tx_size=1)
    print('start move')
    # frame.demo1(-0.9, -0.9)
    # keep_distance(0.5)
    # frame.data_collection(f_d=70, Data_Points=2000)
    # frame.closure(50, 1000)
    # frame.demo3(f=60)
    # print('force: {} positions:{}  error: {}'.format(frame.force, frame.positions, frame.error))

    # filename, df_data_RAW = gripper.save_to_file(remarks='Tele_Operation/test')
    # gripper.move_frame_deg(1, 30)
    # gripper.FC_grasp(2000)
    # time.sleep(2)
    # gripper.ser.write(b'<>')
    # gripper.ser.close()
    # dt_pd = pd.DataFrame(gripper.dt_list)
    # print('dt_pd: {}'.format(dt_pd))
    # gripper.plot_gripper_data(dt_pd)
    # plt.show()
    main(data_points=12000, serial_port='/dev/ttyACM1', to_save=True, filename='data/Gripper_two_fingered/test_gp_2f_cup.csv')
