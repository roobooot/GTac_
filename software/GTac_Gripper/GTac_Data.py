import argparse
import copy
import math
import os
import pickle
import time

import seaborn as sns
import pandas as pd
import matplotlib
from matplotlib.colors import ListedColormap
from mpl_toolkits.mplot3d import Axes3D
# matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
from matplotlib.legend import _get_legend_handles_labels
from matplotlib.animation import FuncAnimation
import gtac_config
import numpy as np
import ntpath
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn import preprocessing, metrics
from sklearn.utils import shuffle
from sklearn.decomposition import PCA
from sklearn.metrics import confusion_matrix
from sklearn import svm
from scipy import signal
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import LabelBinarizer
from sklearn.model_selection import KFold
import GTac_Gripper


class gtac_data:
    def __init__(self, filename, f_sum_th=30, saii_th=100, replace_aft_ct=False, cutting_point=None):
        self.filename = filename
        self.data_pd = pd.read_csv(filename, index_col=0, skiprows=0)
        if cutting_point is not None:
            self.data_pd = self.data_pd.iloc[:cutting_point, :]
            self.cutting_points = cutting_point
        # reduce the FA-I noise from average, below zero.
        self.data_pd.iloc[:, gtac_config.MAG_NUM:gtac_config.ALL_GTAC_NUM][
            self.data_pd.iloc[:, gtac_config.MAG_NUM:gtac_config.ALL_GTAC_NUM] < 0] = 0
        # print(self.data_pd.describe())
        self.data_seq = copy.copy(self.data_pd.to_numpy())
        self.time_stamp_array = self.data_seq[:, -1]
        self.data_seq_post_ = copy.copy(self.data_pd.to_numpy())

        # self.pd_melt()
        # self.all_gtac_data_filtered = gtac_data.low_pass_filter(self.data_seq[:, :gtac_config.ALL_GTAC_NUM],
        #                                                         N=10,
        #                                                         Wn=7)
        # self.data_seq[:, :gtac_config.ALL_GTAC_NUM] = gtac_data.low_pass_filter(self.data_seq[:, :gtac_config.ALL_GTAC_NUM],
        #                                                                         N=10,
        #                                                                         Wn=7)
        self.num_channels = self.data_seq.shape[1]
        self.num_frames = self.data_seq.shape[0]
        print('Read {} channels of data.'.format(self.num_channels))
        self.press_location_r_list = np.zeros([gtac_config.FINGER_NUM,
                                               gtac_config.SEC_NUM,
                                               len(self.data_seq)])
        self.press_location_c_list = np.zeros([gtac_config.FINGER_NUM,
                                               gtac_config.SEC_NUM,
                                               len(self.data_seq)])
        self.sum_value_list = np.zeros([gtac_config.FINGER_NUM,
                                        gtac_config.SEC_NUM,
                                        len(self.data_seq)])
        self.feature_d_FA_sum = np.zeros([gtac_config.FINGER_NUM,
                                          gtac_config.SEC_NUM,
                                          len(self.data_seq)])
        self.feature_SFA = np.zeros([3, gtac_config.FINGER_NUM,
                                     gtac_config.SEC_NUM,
                                     len(self.data_seq)])
        self.feature_dSA = np.zeros([3, gtac_config.FINGER_NUM,
                                     gtac_config.SEC_NUM,
                                     len(self.data_seq)])
        self.feature_SA_event = np.zeros([3, gtac_config.FINGER_NUM,
                                          gtac_config.SEC_NUM,
                                          len(self.data_seq)])
        self.feature_FA_event = np.zeros([gtac_config.FINGER_NUM,
                                          gtac_config.SEC_NUM,
                                          len(self.data_seq)])
        self.f_sum_th = f_sum_th
        self.sensing_after_contact_post_process(f_sum_th=f_sum_th, saii_th=saii_th, replace=replace_aft_ct)
        self.g_finger = np.zeros([gtac_config.FINGER_NUM,
                                  len(self.data_seq)])
        self.g_both_translate = np.zeros([len(self.data_seq)])
        self.g_both_pinch = np.zeros([len(self.data_seq)])
        # Optional: calculate the features
        self.cal_FAI_sum_press_loc()
        # self.cal_feature_sec_mag()
        self.have_sec_wise_feature()
        self.cal_f_sum_both_translation()
        # print(1)

    @staticmethod
    def sensing_after_contact_post_process_data_frame(data_frame_array, contacted_previous_map, SA_II_ref, f_sum_th=30,
                                                      saii_th=100):
        contacted_map = np.zeros((gtac_config.FINGER_NUM, gtac_config.SEC_NUM), dtype=bool)
        for f in range(gtac_config.FINGER_NUM):
            for s in range(gtac_config.SEC_NUM):
                tri_index = gtac_data.get_tri_index(f, s)
                sum_value, _, _ = gtac_data.find_FAI_sum_press_loc(data_frame_array, f, s)
                _, SAII_scaler = gtac_data.find_SAII(data_frame_array, f, s)
                if [f, s] not in gtac_config.PALM_GTAC_INDEX:  # Exempt the GTac on the palm
                    if sum_value > f_sum_th:  # condition of contact
                        # calculate SA_II sensing according to the updated reference.
                        data_frame_array[tri_index + 0] = data_frame_array[tri_index + 0] - SA_II_ref[tri_index + 0]
                        data_frame_array[tri_index + 1] = data_frame_array[tri_index + 1] - SA_II_ref[tri_index + 1]
                        data_frame_array[tri_index + 2] = data_frame_array[tri_index + 2] - SA_II_ref[tri_index + 2]
                        contacted_map[f, s] = True
                    else:
                        data_frame_array[tri_index + 0] = 0
                        data_frame_array[tri_index + 1] = 0
                        data_frame_array[tri_index + 2] = 0
                        contacted_map[f, s] = False
                if [f, s] in gtac_config.PALM_GTAC_INDEX:  # apply rules on the GTac on the palm
                    if sum_value > f_sum_th or SAII_scaler > saii_th:  # condition of contact
                        # calculate SA_II sensing according to the updated reference.
                        data_frame_array[tri_index + 0] = data_frame_array[tri_index + 0] - SA_II_ref[tri_index + 0]
                        data_frame_array[tri_index + 1] = data_frame_array[tri_index + 1] - SA_II_ref[tri_index + 1]
                        data_frame_array[tri_index + 2] = data_frame_array[tri_index + 2] - SA_II_ref[tri_index + 2]
                        contacted_map[f, s] = True
                    else:
                        data_frame_array[tri_index + 0] = 0
                        data_frame_array[tri_index + 1] = 0
                        data_frame_array[tri_index + 2] = 0
                        contacted_map[f, s] = False
                # update the SA_II reference according to the status of finger section.
                if contacted_map[f, s] != contacted_previous_map[f, s] and contacted_map[f, s]:
                    # clear the current frame, otherwise there would be a spike.
                    data_frame_array[tri_index + 0] = 0
                    data_frame_array[tri_index + 1] = 0
                    data_frame_array[tri_index + 2] = 0
                    SA_II_ref[tri_index + 0] = data_frame_array[tri_index + 0]
                    SA_II_ref[tri_index + 1] = data_frame_array[tri_index + 1]
                    SA_II_ref[tri_index + 2] = data_frame_array[tri_index + 2]
        # iterate the contact status
        return data_frame_array, contacted_map, SA_II_ref

    def sensing_after_contact_post_process(self, f_sum_th=30, saii_th=100, replace=False):
        SA_II_ref = np.zeros((gtac_config.MAG_NUM))
        contacted_previous_map = np.zeros((gtac_config.FINGER_NUM, gtac_config.SEC_NUM), dtype=bool)
        for x, data_frame_array in enumerate(self.data_seq_post_):
            st = time.time()
            new_data_frame, contacted_map, new_SA_II_ref = gtac_data.sensing_after_contact_post_process_data_frame(
                data_frame_array,
                contacted_previous_map,
                SA_II_ref,
                f_sum_th, saii_th)
            time_ms = round(time.time() - st, 5) * 1000
            # print('post_processing time: {} ms'.format(time_ms))
            SA_II_ref = new_SA_II_ref
            contacted_previous_map = contacted_map
            self.data_seq_post_[x] = new_data_frame
        if replace:
            self.data_seq = copy.copy(self.data_seq_post_)

    def have_sec_wise_feature(self):
        # self.sec_wise_features: shape --> (1+1+1+1+3+3+1+3, 5, 3, n)
        # details in gtac_config.COLUMNS_Sec_Features
        self.sec_wise_features = np.concatenate([self.press_location_r_list.reshape((1, gtac_config.FINGER_NUM,
                                                                                     gtac_config.SEC_NUM,
                                                                                     self.num_frames)),
                                                 self.press_location_c_list.reshape((1, gtac_config.FINGER_NUM,
                                                                                     gtac_config.SEC_NUM,
                                                                                     self.num_frames)),
                                                 self.sum_value_list.reshape((1, gtac_config.FINGER_NUM,
                                                                              gtac_config.SEC_NUM,
                                                                              self.num_frames)),
                                                 self.feature_d_FA_sum.reshape((1, gtac_config.FINGER_NUM,
                                                                                gtac_config.SEC_NUM,
                                                                                self.num_frames)),
                                                 self.feature_SFA,
                                                 self.feature_dSA,
                                                 self.feature_FA_event.reshape((1, gtac_config.FINGER_NUM,
                                                                                gtac_config.SEC_NUM,
                                                                                self.num_frames)),
                                                 self.feature_SA_event])
        # print(1)

    def cal_FAI_sum_press_loc(self):
        for i, data_frame_array in enumerate(self.data_seq):
            for f in range(gtac_config.FINGER_NUM):
                for s in range(gtac_config.SEC_NUM):
                    sum_value, press_location_r, \
                    press_location_c = self.find_FAI_sum_press_loc(data_frame_array, f, s)
                    self.press_location_r_list[f, s, i] = press_location_r - 1
                    self.press_location_c_list[f, s, i] = press_location_c - 1
                    self.sum_value_list[f, s, i] = sum_value

    def cal_f_sum_both_translation(self):
        # calculate the sum of g of the two fingertips used for translation, a kind of in-hand manipuation
        translate_fingers = [1, 3]
        pinch_fingers = [0, 4]
        for i, data_frame_array in enumerate(self.data_seq):
            f_sum_list, g_fc_array = GTac_Gripper.find_f_sum_exclude_palm(data_frame_array)
            for f in range(gtac_config.FINGER_NUM):
                self.g_finger[f, i] = f_sum_list[f]
            self.g_both_translate[i] = f_sum_list[translate_fingers[0]] + f_sum_list[translate_fingers[1]]
            self.g_both_pinch[i] = f_sum_list[pinch_fingers[0]] + f_sum_list[pinch_fingers[1]]

    def cal_feature_sec_mag(self, SA_event_th=10, FA_event_th=10):
        gradient = 1  # the number of sampling cycles to obtain gradient
        for i, data_frame_array in enumerate(self.data_seq):
            if i < gradient:
                data_frame_array_previous = self.data_seq[i]
            else:
                data_frame_array_previous = self.data_seq[i - gradient]
            for f in range(gtac_config.FINGER_NUM):
                for s in range(gtac_config.SEC_NUM):
                    tri_index = self.get_tri_index(f, s)
                    # SFA
                    if self.sum_value_list[f, s, i] > self.f_sum_th:
                        SFA_x = data_frame_array[tri_index + 0] / self.sum_value_list[f, s, i]
                        SFA_y = data_frame_array[tri_index + 1] / self.sum_value_list[f, s, i]
                        SFA_z = data_frame_array[tri_index + 2] / self.sum_value_list[f, s, i]
                    else:
                        SFA_x = 0
                        SFA_y = 0
                        SFA_z = 0

                    if i < gradient:
                        d_FA_sum = self.sum_value_list[f, s, i] - self.sum_value_list[f, s, i]
                    else:
                        d_FA_sum = self.sum_value_list[f, s, i] - self.sum_value_list[f, s, i - gradient]

                    # dSA
                    dSA_x = data_frame_array[tri_index + 0] - data_frame_array_previous[tri_index + 0]
                    dSA_y = data_frame_array[tri_index + 1] - data_frame_array_previous[tri_index + 1]
                    dSA_z = data_frame_array[tri_index + 2] - data_frame_array_previous[tri_index + 2]

                    self.feature_d_FA_sum[f, s, i] = d_FA_sum
                    self.feature_FA_event[f, s, i] = gtac_data.have_tactile_events(threshold=FA_event_th,
                                                                                   tactile_data=d_FA_sum)

                    self.feature_SFA[0, f, s, i] = SFA_x
                    self.feature_SFA[1, f, s, i] = SFA_y
                    self.feature_SFA[2, f, s, i] = SFA_z

                    self.feature_dSA[0, f, s, i] = dSA_x
                    self.feature_dSA[1, f, s, i] = dSA_y
                    self.feature_dSA[2, f, s, i] = dSA_z
                    self.feature_SA_event[0, f, s, i] = gtac_data.have_tactile_events(threshold=SA_event_th,
                                                                                      tactile_data=dSA_x)
                    self.feature_SA_event[1, f, s, i] = gtac_data.have_tactile_events(threshold=SA_event_th,
                                                                                      tactile_data=dSA_y)
                    self.feature_SA_event[2, f, s, i] = gtac_data.have_tactile_events(threshold=SA_event_th,
                                                                                      tactile_data=dSA_z)

        # self.feature_SA_event = self.feature_dSA > SA_event_th
        # self.feature_FA_event = self.feature_d_FA_sum > FA_event_th

    @staticmethod
    def have_tactile_events(threshold, tactile_data):
        if tactile_data >= threshold:
            return 1
        elif tactile_data <= -threshold:
            return -1
        else:
            return 0

    def find_sec_data_i(self, i, finger, sec):
        data_frame = self.data_pd.iloc[i]
        return gtac_data.find_sec_data(data_frame, finger, sec)

    @staticmethod
    def find_sec_data(data_frame_array, finger, sec, a=0.1):
        # Input: data frame
        # Output: the GTac data in one finger section, shape = 19 [f16,s3]
        sec_data = []
        for i in range(gtac_config.MAT_NUM):  # MAT_NUM -> 16: there 4*4 sensing points on FA-I layer
            r = i // 4
            c = i % 4
            index, value = gtac_data.find_FAI_value(data_frame_array, finger, sec, r, c)
            sec_data.append(value)
        FA_sum = np.sum(sec_data)
        mag_all, _ = gtac_data.find_SAII(data_frame_array, finger, sec)
        g = math.sqrt(mag_all[0] * mag_all[0] + mag_all[1] * mag_all[1] + (a * mag_all[2] + (1 - a) * FA_sum) * (
                a * mag_all[2] + (1 - a) * FA_sum))
        g = round(g, 2)
        for m in mag_all:
            sec_data.append(m)
        return sec_data, g

    @staticmethod
    def find_mat_value(data_frame_array, finger, sec, r, c):
        index = sec * 4 * 20 + finger * 4 + \
                gtac_config.MAT_ORIENT_COL[finger, sec, r, c] * 20 + \
                gtac_config.MAT_ORIENT_ROW[finger, sec, r, c]
        return index, data_frame_array[index + gtac_config.MAG_NUM]

    @staticmethod
    def find_sec_index(finger, sec):
        # Input: finger, sec
        # Output: the GTac index in one finger section, shape >> 19
        sec_index = []
        for i in range(gtac_config.MAT_NUM):  # MAT_NUM -> 16: there 4*4 sensing points on FA-I layer
            r = i // 4
            c = i % 4
            index = gtac_data.find_FAI_index(finger, sec, r, c)
            sec_index.append(index)
        mag_all = gtac_data.find_SAII_index(finger, sec)
        for m in mag_all:
            sec_index.append(m)
        return sec_index

    @staticmethod
    def find_FAI_value(data_frame_array, finger, sec, r, c):
        index = gtac_data.find_FAI_index(finger, sec, r, c)
        return index, data_frame_array[index]

    @staticmethod
    def find_FAI_index(finger, sec, r, c):
        # the FAI index exclude the mag data
        # the overall index is "output"+NUM_MAG
        index = sec * 4 * 20 + finger * 4 + \
                gtac_config.MAT_ORIENT_COL[finger, sec, r, c] * 20 + \
                gtac_config.MAT_ORIENT_ROW[finger, sec, r, c]
        return index + gtac_config.MAG_NUM

    @staticmethod
    def find_location(index):
        h_line = index // 20  # horizontal lines
        sec = h_line // 4
        v_line = index % 20  # vertical lines
        finger = v_line // 4
        ro = h_line % 4
        co = v_line % 4
        if finger == 0 and sec in [0, 1]:
            c = np.where(gtac_config.UP_MAT_ROW == co)[1][0]
            r = np.where(gtac_config.UP_MAT_COL == ro)[0][0]
        else:
            mat_row = gtac_config.MAT_ORIENT_ROW[finger, sec]
            mat_col = gtac_config.MAT_ORIENT_COL[finger, sec]
            r = np.where(mat_row == co)[0][0]
            c = np.where(mat_col == ro)[1][0]
        return finger, sec, r, c

    @staticmethod
    def find_FAI_sum_press_loc(data_frame_array, finger, sec, threshold=20):
        sum_r = 0
        sum_c = 0
        sum_value = 0
        press_location_r = 2.5
        press_location_c = 2.5
        for i in range(gtac_config.MAT_NUM):  # MAT_NUM -> 16: there 4*4 sensing points on FA-I layer
            r = i // 4
            c = i % 4
            index, value = gtac_data.find_FAI_value(data_frame_array, finger, sec, r, c)
            if value > threshold:  # threshold to remove noise for obtaining pressing location
                sum_r += (r + 1) * value
                sum_c += (c + 1) * value
                sum_value += value
            # update pressing locations
            if sum_value != 0:
                press_location_r = round(sum_r / sum_value, 1)
                press_location_c = round(sum_c / sum_value, 1)
        return sum_value, press_location_r, press_location_c

    @staticmethod
    def find_SAII(data_frame_array, finger, sec):
        # print('SAII_data: finger {}, sec {}'.format(finger, sec))
        tri_index = finger * 9 + (2 - sec) * 3
        mag_x = data_frame_array[tri_index]
        mag_y = data_frame_array[tri_index + 1]
        mag_z = data_frame_array[tri_index + 2]
        SAII_scaler = math.sqrt(mag_x * mag_x + mag_y * mag_y + mag_z * mag_z)
        # print('Find_SAII: {} scalar: {}'.format([mag_x, mag_y, mag_z], SAII_scaler))
        return [mag_x, mag_y, mag_z], SAII_scaler

    @staticmethod
    def find_SAII_index(finger, sec):
        tri_index = finger * 9 + (2 - sec) * 3
        return tri_index, tri_index + 1, tri_index + 2

    @staticmethod
    def preprocess_(data_raw_list):
        # input: one frame of GTac data in real-time flow
        # according to current placement of magnets, this pre-process is required to re-orient the direction to meet the right-hand frame.
        data_raw_np = np.array(data_raw_list)
        # re-orient finger 0 sec 0
        saII_f0_s0_x = copy.copy(data_raw_np[6])
        saII_f0_s0_y = copy.copy(data_raw_np[7])
        data_raw_np[6] = saII_f0_s0_y
        data_raw_np[7] = saII_f0_s0_x * -1

        # re-orient finger 0 sec 0
        saII_f0_s1_x = copy.copy(data_raw_np[3])
        saII_f0_s1_y = copy.copy(data_raw_np[4])
        data_raw_np[3] = saII_f0_s1_y
        data_raw_np[4] = saII_f0_s1_x * -1

        # re-orient finger 0 sec 2
        saII_f0_s2_x = copy.copy(data_raw_np[0])
        saII_f0_s2_y = copy.copy(data_raw_np[1])
        data_raw_np[0] = saII_f0_s2_x * -1
        data_raw_np[1] = saII_f0_s2_y * -1

        # flip the sign for all of them
        data_raw_np[:gtac_config.MAG_NUM] = -data_raw_np[:gtac_config.MAG_NUM]

        # # de earth field
        # ref_mag_x, ref_mag_y, ref_mag_z = gtac_data.find_SAII_index(4, 0)
        # f1s0_mag_x, f1s0_mag_y, f1s0_mag_z = gtac_data.find_SAII_index(1, 0)
        # data_raw_np[f1s0_mag_x] = data_raw_np[f1s0_mag_x] - data_raw_np[ref_mag_x]
        # data_raw_np[f1s0_mag_y] = data_raw_np[f1s0_mag_y] - data_raw_np[ref_mag_y]
        # data_raw_np[f1s0_mag_z] = data_raw_np[f1s0_mag_z] - data_raw_np[ref_mag_z]
        return data_raw_np

    @staticmethod
    def low_pass_filter(data_channel, N=10, Wn=20):
        sos = signal.butter(N, Wn, 'lowpass', output='sos', fs=150)
        filtered = signal.sosfilt(sos, data_channel)
        return filtered

    @staticmethod
    def get_tri_index(finger, sec):
        return finger * 9 + (2 - sec) * 3

    def replace_gtac_data_pd(self, new_data_pd):
        self.data_pd = new_data_pd
        self.data_seq = self.data_pd.to_numpy()

    def plot_all(self, save=0, img_name_head='GTac_plot'):
        fig_SA_II, axs_SA_II = plt.subplots(5, 3,
                                            sharex='all',
                                            sharey='all',
                                            constrained_layout=True,
                                            figsize=(13, 13))
        fig_SA_II.suptitle('Shear Force ' \
                           + self.filename, fontsize=16)
        fig_SA_II_aft_ct, axs_SA_II_aft_ct = plt.subplots(5, 3,
                                                          sharex='all',
                                                          sharey='all',
                                                          constrained_layout=True,
                                                          figsize=(15, 15))
        fig_SA_II_aft_ct.suptitle('Shear Force after Contact ' \
                                  + self.filename, fontsize=16)
        fig_FA_I, axs_FA_I = plt.subplots(5, 3,
                                          sharex='all',
                                          sharey='all', constrained_layout=True,
                                          figsize=(15, 15))
        fig_FA_I.suptitle('Normal Force ' \
                          + self.filename,
                          fontsize=16)
        fig_FC, axs_press_loc = plt.subplots(5, 3,
                                             sharex='all',
                                             sharey='all', constrained_layout=True,
                                             figsize=(15, 15))
        fig_FC.suptitle('Normal Force Center ' \
                        + self.filename,
                        fontsize=16)

        for f in range(gtac_config.FINGER_NUM):
            for s in range(gtac_config.SEC_NUM):
                tri_index = self.get_tri_index(f, s)
                plot_title = gtac_config.FINGER_NAME[f] \
                             + ' ' + gtac_config.SEC_NAME[s]
                axs_SA_II[f, s].set_title(plot_title)
                axs_SA_II[f, s].plot(self.data_seq[:, tri_index], label='SA_II x')
                # filtered = self.low_pass_filter(self.data_seq[:, tri_index], N=10, Wn=7)
                # axs_SA_II[f, s].plot(filtered, label='SA_II x-filtered')
                axs_SA_II[f, s].plot(self.data_seq[:, tri_index + 1], label='SA_II y')
                # filtered = self.low_pass_filter(self.data_seq[:, tri_index + 1], N=10, Wn=7)
                # axs_SA_II[f, s].plot(filtered, label='SA_II y-filtered')
                axs_SA_II[f, s].plot(self.data_seq[:, tri_index + 2], label='SA_II z')
                # filtered = self.low_pass_filter(self.data_seq[:, tri_index + 2], N=10, Wn=7)
                # axs_SA_II[f, s].plot(filtered, label='SA_II z-filtered')
                # axs_SA_II[f, s].legend(loc=0)
                # axs_FA_I_ = axs_SA_II[f, s].twinx()
                axs_SA_II[f, s].plot(self.sum_value_list[f, s, :] / 2, label='FA-I Sum', color='purple', ls='--')
                # axs_FA_I_.set_ylim(0, 1000)
                # axs_FA_I_.get_shared_y_axes().join(axs_FA_I_, axs_SA_II[f, s])

                axs_SA_II_aft_ct[f, s].set_title(plot_title)
                axs_SA_II_aft_ct[f, s].plot(self.data_seq_post_[:, tri_index], label='SA_II x')
                axs_SA_II_aft_ct[f, s].plot(self.data_seq_post_[:, tri_index + 1], label='SA_II y')
                axs_SA_II_aft_ct[f, s].plot(self.data_seq_post_[:, tri_index + 2], label='SA_II z')
                axs_SA_II_aft_ct[f, s].plot(self.sum_value_list[f, s, :], label='FA-I Sum', color='purple', ls='--')
                axs_SA_II_aft_ct[f, s].legend(loc=0)

                axs_FA_I[f, s].set_title(plot_title)
                axs_FA_I[f, s].plot(self.sum_value_list[f, s, :], label='FA-I Sum')
                # axs_FA_I[f, s].legend(loc=0)

                axs_press_loc[f, s].set_title(plot_title)
                axs_press_loc[f, s].plot(self.press_location_r_list[f, s, :], label='x')
                axs_press_loc[f, s].plot(self.press_location_c_list[f, s, :], label='y')
                axs_press_loc[f, s].legend(loc=0)

        if save:
            fig_SA_II.savefig(img_name_head + '_SA_II' + '.svg')
            fig_SA_II_aft_ct.savefig(img_name_head + 'aft_conct_SA_II' + '.svg')
            fig_FA_I.savefig(img_name_head + '_FA_I' + '.svg')
            fig_FC.savefig(img_name_head + '_FC' + '.svg')

            fig_SA_II.savefig(img_name_head + '_SA_II' + '.png')
            fig_SA_II_aft_ct.savefig(img_name_head + 'aft_conct_SA_II' + '.png')
            fig_FA_I.savefig(img_name_head + '_FA_I' + '.png')
            fig_FC.savefig(img_name_head + '_FC' + '.png')
            # plt.show()

    def plot_motors(self, save=0, img_name_head='GTac_plot'):
        # draw curves for motors angle
        fig_motors, axs_motors = plt.subplots(2, 3,
                                              sharex=True,
                                              sharey=True, constrained_layout=True)
        fig_motors.suptitle('Motors Angles' \
                            + self.filename,
                            fontsize=16)
        for m in range(6):
            mr = m // 3
            mc = m % 3
            plot_title = 'Motor ' + gtac_config.FINGER_MOTOR[m]

            motor_index = gtac_config.ALL_GTAC_NUM + m
            axs_motors[mr, mc].set_title(plot_title)
            axs_motors[mr, mc].plot(self.data_seq[:, motor_index], label=plot_title)
            axs_motors[mr, mc].legend(loc=0)
        if save:
            fig_motors.savefig(img_name_head + '_motors' + '.svg')
            fig_motors.savefig(img_name_head + '_motors' + '.png')

    def plot_g_translate(self, save=0, img_name_head='GTac_in_hand'):
        fig_g_f_II, axs_g_f_II = plt.subplots(5, 1,
                                              sharex='all',
                                              sharey='all',
                                              constrained_layout=True,
                                              figsize=(6, 6))
        fig_g_f_II.suptitle('g Finger ' \
                            + self.filename, fontsize=16)
        pinch_fingers = [0, 4]
        translate_fingers = [1, 3]
        for f in range(gtac_config.FINGER_NUM):
            plot_title = gtac_config.FINGER_NAME[f]
            axs_g_f_II[f].set_title('F-' + str(f))
            axs_g_f_II[f].plot(self.g_finger[f, :], label='g')

        fig_g_both, axs_g_both = plt.subplots(2, 1, sharex='all',
                                  sharey='all',
                                  constrained_layout=True,
                                  figsize=(6, 6))
        axs_g_both[0].plot(self.g_both_translate, label='g-both translate')
        axs_g_both[1].plot(self.g_both_pinch, label='g-both pinch')

        fig_g_both_single, axs_g_both_single = plt.subplots(1, 1, sharex='all',
                                  sharey='all',
                                  constrained_layout=True,
                                  figsize=(7, 3))
        axs_g_both_single.plot(self.g_both_translate, label='$g_{f2}+g_{f3}$: translation')
        axs_g_both_single.plot(self.g_both_pinch, label='$g_{f0}+g_{f1}$: pinch')
        axs_g_both_single.legend(loc=0)
        if save:
            fig_g_both_single.savefig(img_name_head + '_g_both' + '.svg')
            fig_g_both_single.savefig(img_name_head + '_g_both' + '.png')

    def plot_g_transalte_and_motors(self, save=0, img_name_head='GTac_in_hand'):

        fig_g_both_single, axs_g_both_single = plt.subplots(2, 1, sharex='all',
                                  # sharey='all',
                                  constrained_layout=True,
                                  figsize=(7, 3))
        axs_g_both_single[0].plot(self.g_both_translate, label='$g_{f2}+g_{f3}$: translation')
        axs_g_both_single[0].plot(self.g_both_pinch, label='$g_{f0}+g_{f1}$: pinch')
        axs_g_both_single[0].legend(loc=0)

        # draw curves for motors angle
        axs_g_both_single[1].plot(self.data_seq[:, gtac_config.ALL_GTAC_NUM + 0], label='F0: pinch', color='salmon')
        axs_g_both_single[1].plot(self.data_seq[:, gtac_config.ALL_GTAC_NUM + 1], label='F1: pinch', color='coral')
        axs_g_both_single[1].plot(self.data_seq[:, gtac_config.ALL_GTAC_NUM + 2], label='F2: translate', color='navy')
        axs_g_both_single[1].plot(self.data_seq[:, gtac_config.ALL_GTAC_NUM + 3], label='F3: translate', color='royalblue')
        axs_g_both_single[1].legend(loc=0)
        if save:
            fig_g_both_single.savefig(img_name_head + '_g_both_motor' + '.svg')
            fig_g_both_single.savefig(img_name_head + '_g_both_motor' + '.png')

    @staticmethod
    def assign_sec_wise_data(data_seq, save=False):
        # assign finger and section to each frame
        # find details in gtac_config.COLUMNS_Finger
        print('Assign the dataset in to sec-wise')
        data_assigned = pd.DataFrame(columns=gtac_config.COLUMNS_Finger)
        num_frames = len(data_seq)
        for i, d in enumerate(data_seq):
            print('{}/{}'.format(i, num_frames))
            for f in range(gtac_config.FINGER_NUM):
                for s in range(gtac_config.SEC_NUM):
                    data_to_append = []
                    data_sec, _ = gtac_data.find_sec_data(d, f, s)
                    for n in range(16):
                        if data_sec[n] < 20:
                            data_sec[n] = 0
                    data_to_append.extend(data_sec)
                    data_to_append.append(f)
                    data_to_append.append(s)
                    data_to_append.append(d[-1])
                    data_to_append.append(i)
                    data_assigned.loc[len(data_assigned)] = data_to_append
        return data_assigned

    @staticmethod
    def assign_sec_wise_feature(feature_seq, time_stamp_seq):
        # assign finger and section to each frame
        # find details in gtac_config.COLUMNS_Finger
        print('Assign the features dataset in to sec-wise')
        feature_assigned = pd.DataFrame(columns=gtac_config.COLUMNS_Sec_Features)
        num_frames = feature_seq.shape[-1]
        for i in range(num_frames):
            print('{}/{}'.format(i, num_frames))
            for f in range(gtac_config.FINGER_NUM):
                for s in range(gtac_config.SEC_NUM):
                    feature_to_append = []
                    feature_to_append.extend(feature_seq[:, f, s, i])
                    feature_to_append.append(f)
                    feature_to_append.append(s)
                    feature_to_append.append(time_stamp_seq[i])
                    feature_to_append.append(i)
                    feature_assigned.loc[len(feature_assigned)] = feature_to_append
        return feature_assigned

    def get_assigned_sec_wise(self):
        assigned_data_filename = self.filename[:-4] + '_assigned_sec_wise' + self.filename[-4:]
        assigned_feature_filename = self.filename[:-4] + '_assigned_feature_sec_wise' + self.filename[-4:]
        # gtac data
        if os.path.isfile(assigned_data_filename):
            self.data_assigned_sec_wise_pd = pd.read_csv(assigned_data_filename, index_col=0, skiprows=0)
        else:
            self.data_assigned_sec_wise_pd = self.assign_sec_wise_data(self.data_seq)
            self.data_assigned_sec_wise_pd.to_csv(assigned_data_filename)
            print('Saved: {}'.format(assigned_data_filename))
        # gtac features
        if os.path.isfile(assigned_feature_filename):
            self.feature_assigned_sec_wise_pd = pd.read_csv(assigned_feature_filename, index_col=0, skiprows=0)
        else:
            self.feature_assigned_sec_wise_pd = self.assign_sec_wise_feature(feature_seq=self.sec_wise_features,
                                                                             time_stamp_seq=self.data_seq[:, -1])
            self.feature_assigned_sec_wise_pd.to_csv(assigned_feature_filename)
            print('Saved: {}'.format(assigned_feature_filename))
        if self.cutting_points is not None:
            self.data_assigned_sec_wise_pd = self.data_assigned_sec_wise_pd.loc[
                self.data_assigned_sec_wise_pd['Sample Index'] <= self.cutting_points]
            self.feature_assigned_sec_wise_pd = self.feature_assigned_sec_wise_pd.loc[
                self.feature_assigned_sec_wise_pd['Sample Index'] <= self.cutting_points]

    def plot_all_line_in_one(self, save=0, img_name_head='GTac_plot'):
        self.get_assigned_sec_wise()
        print('plotting: all_lines_in_one_figure')
        FAI_cols = self.data_assigned_sec_wise_pd.columns[:16]
        SAII_cols = self.data_assigned_sec_wise_pd.columns[16:19]
        # data_pd = copy.copy(self.data_pd)
        FAI_melted = pd.melt(self.data_assigned_sec_wise_pd,
                             id_vars=['finger', 'section', 'milliseconds', 'Sample Index'],
                             value_vars=FAI_cols)
        SAII_melted = pd.melt(self.data_assigned_sec_wise_pd,
                              id_vars=['finger', 'section', 'milliseconds', 'Sample Index'],
                              value_vars=SAII_cols)

        FAI_melted = FAI_melted.drop(FAI_melted[FAI_melted.finger == 2].index)
        SAII_melted = SAII_melted.drop(SAII_melted[SAII_melted.finger == 2].index)

        print(FAI_melted)
        print(SAII_melted)
        print(FAI_melted['finger'].unique())
        print(FAI_melted['section'].unique())

        g1 = sns.relplot(x='milliseconds', y='value',
                         row='finger',
                         style='section',
                         hue='variable',
                         data=FAI_melted,
                         # dashes=False,
                         ci=None, height=1.25, aspect=6,
                         kind='line',
                         # legend='brief',
                         palette="flare")
        axes = g1.axes.flatten()
        for ax in axes:
            ax.set_title('')
            ax.set_ylabel('')
            ax.set_xlabel('Milliseconds')
        g1.tight_layout()

        g2 = sns.relplot(x='milliseconds', y='value',
                         row='finger',
                         style='section',
                         hue='variable',
                         data=SAII_melted,
                         # dashes=False,
                         ci=None, height=1.25, aspect=6,
                         kind='line',
                         # legend='brief',
                         facet_kws={'sharey': False, 'sharex': True})
        # plt.tight_layout()
        axes = g2.axes.flatten()
        for ax in axes:
            ax.set_title('')
            ax.set_ylabel('')
            ax.set_xlabel('Milliseconds')
        g2.tight_layout()

        if save:
            # fig_All_melted.savefig(img_name_head + 'fig_All_melted' + '.svg')
            # fig_All_.savefig(img_name_head + 'fig_All_' + '.svg')
            g1.savefig(img_name_head + 'fig_All_FAI' + '.svg')
            g2.savefig(img_name_head + 'fig_All_SAII' + '.svg')

            # fig_All_melted.savefig(img_name_head + 'fig_All_melted' + '.png')
            # fig_All_.savefig(img_name_head + 'fig_All_' + '.png')
            g1.savefig(img_name_head + 'fig_All_FAI' + '.png')
            g2.savefig(img_name_head + 'fig_All_SAII' + '.png')

    def plot_columns_sec_wise_(self, func, data_array, time_stamp):
        d_FA_sum_reshaped_pd = pd.DataFrame(data_array.T)
        d_FA_sum_reshaped_pd['milliseconds'] = time_stamp
        d_FA_sum_reshaped_pd_melt = pd.melt(d_FA_sum_reshaped_pd,
                                            id_vars=['milliseconds'],
                                            value_vars=range(15),
                                            ignore_index=False)

        # pal = sns.cubehelix_palette(10, rot=-.25, light=.7)
        g = sns.FacetGrid(d_FA_sum_reshaped_pd_melt,
                          row="variable",
                          # hue="variable",
                          aspect=1.5,
                          height=2,
                          # palette=pal,
                          sharex=True,
                          sharey=True,
                          # legend_out=True,
                          margin_titles=False)
        g.map(func, 'milliseconds', "value", ci=None)
        axes = g.axes.flatten()
        for ax in axes:
            ax.set_title("")
            ax.set_ylabel("")
        g.set(xticks=[])
        # g.tight_layout()

    def plot_15_row_(self, data_array, time_stamp_array, title='Plot Title'):
        fig_data_event, axes_data_event = plt.subplots(len(data_array), 1,
                                                       sharex='all',
                                                       sharey='all',
                                                       constrained_layout=True,
                                                       figsize=(15, 15))
        for i in range(len(axes_data_event)):
            axes_data_event[i].plot(time_stamp_array, data_array[i], color='b')
        axes_data_event[i].set_xlabel('Time (ms)', fontsize=15)
        fig_data_event.suptitle(title, fontsize=20)
        return fig_data_event

    def plot_events_vlines_(self, ax, num_frames,
                            FA_event_pos_index, FA_event_neg_index,
                            SA_x_event_pos_index, SA_x_event_neg_index,
                            SA_y_event_pos_index, SA_y_event_neg_index,
                            SA_z_event_pos_index, SA_z_event_neg_index,
                            gap=5, length=2, ):
        level1_y = gap
        level2_y = 0
        level3_y = -gap
        ax.hlines(y=level1_y, xmin=0, xmax=num_frames, colors='g', lw=1, )
        ax.hlines(y=level2_y, xmin=0, xmax=num_frames, colors='b', lw=1, )
        ax.hlines(y=level3_y, xmin=0, xmax=num_frames, colors='orange',
                  lw=1, )

        ax.vlines(x=FA_event_pos_index, ymin=level1_y, ymax=level1_y + length,
                  colors='purple', ls='-', lw=2,
                  label='FA_event_pos_index')
        ax.vlines(x=FA_event_neg_index, ymin=level1_y, ymax=level1_y - length,
                  colors='purple', ls='--', lw=2,
                  label='FA_event_pos_index')

        ax.vlines(x=SA_z_event_pos_index, ymin=level1_y, ymax=level1_y + length,
                  colors='g', ls='-', lw=2,
                  label='FA_event_pos_index')
        ax.vlines(x=SA_z_event_neg_index, ymin=level1_y, ymax=level1_y - length,
                  colors='g', ls='--', lw=2,
                  label='FA_event_pos_index')

        ax.vlines(x=SA_x_event_pos_index, ymin=level2_y, ymax=level2_y + length,
                  colors='b', ls='-', lw=2,
                  label='FA_event_pos_index')
        ax.vlines(x=SA_x_event_neg_index, ymin=level2_y, ymax=level2_y - length,
                  colors='b', ls='--', lw=2,
                  label='FA_event_pos_index')

        ax.vlines(x=SA_y_event_pos_index, ymin=level3_y, ymax=level3_y + length,
                  colors='orange', ls='-', lw=2,
                  label='FA_event_pos_index')
        ax.vlines(x=SA_y_event_neg_index, ymin=level3_y, ymax=level3_y - length,
                  colors='orange', ls='--', lw=2,
                  label='FA_event_pos_index')

    def plot_tactile_events_vlines_(self, FA_event_reshaped, SA_event_reshaped, gap=5, length=2):
        fig_SFA_event_2, axes_SFA_event_2 = plt.subplots(5, 3,
                                                         sharex='all',
                                                         sharey='all',
                                                         constrained_layout=True,
                                                         figsize=(15, 7))
        for f in range(gtac_config.FINGER_NUM):
            for s in range(gtac_config.SEC_NUM):
                i = f * 3 + s
                FA_event_pos_index = np.where(FA_event_reshaped[i] == 1)
                # print('Number of FA+ events: {} --> {}'.format(len(FA_event_pos_index[0]), FA_event_pos_index))
                FA_event_neg_index = np.where(FA_event_reshaped[i] == -1)
                # print('Number of FA- events: {}'.format(len(FA_event_neg_index[0])))
                SA_x_event_pos_index = np.where(SA_event_reshaped[0, i] == 1)
                SA_x_event_neg_index = np.where(SA_event_reshaped[0, i] == -1)
                SA_y_event_pos_index = np.where(SA_event_reshaped[1, i] == 1)
                SA_y_event_neg_index = np.where(SA_event_reshaped[1, i] == -1)
                SA_z_event_pos_index = np.where(SA_event_reshaped[2, i] == 1)
                SA_z_event_neg_index = np.where(SA_event_reshaped[2, i] == -1)

                self.plot_events_vlines_(axes_SFA_event_2[f, s], self.num_frames,
                                         FA_event_pos_index, FA_event_neg_index,
                                         SA_x_event_pos_index, SA_x_event_neg_index,
                                         SA_y_event_pos_index, SA_y_event_neg_index,
                                         SA_z_event_pos_index, SA_z_event_neg_index,
                                         gap=gap, length=length)

                handles, labels = axes_SFA_event_2[f, s].get_legend_handles_labels()
        fig_SFA_event_2.legend(handles, labels, bbox_to_anchor=(1.0, 1), loc='upper left')
        return fig_SFA_event_2

    def plot_tactile_events(self, save=0, img_name_head='GTac_plot'):
        self.get_assigned_sec_wise()
        time_stamp_array = self.data_seq[:, -1]
        feature_events_melted = pd.melt(self.feature_assigned_sec_wise_pd,
                                        id_vars=['finger', 'section', 'milliseconds', 'Sample Index'],
                                        value_vars=['feature_FA_event',
                                                    'feature_SA_event_x',
                                                    'feature_SA_event_y',
                                                    'feature_SA_event_z'],
                                        var_name='Events Type',
                                        value_name='Tactile Events')

        g2 = sns.relplot(x='milliseconds', y='Tactile Events',
                         row='finger',
                         col='section',
                         hue='Events Type',
                         data=feature_events_melted,
                         dashes=False,
                         ci=None,
                         s=10,
                         kind='scatter',
                         legend='brief')
        # plt.tight_layout()
        axes = g2.axes.flatten()
        for ax in axes:
            ax.set_title("")
            ax.set_ylabel("")
        g2.set(yticklabels=[])
        g2.tight_layout()
        g2.fig.subplots_adjust(top=0.9)
        g2.fig.suptitle('All Tactile Events')

        FA_event_reshaped = self.feature_FA_event.reshape((15, self.num_frames))
        SA_event_reshaped = self.feature_SA_event.reshape((3, 15, self.num_frames))
        # self.plot_columns_sec_wise_(sns.lineplot, SA_event_reshaped[0])
        # self.plot_columns_sec_wise_(sns.scatterplot, SA_event_reshaped[1])
        # self.plot_columns_sec_wise_(sns.scatterplot, SA_event_reshaped[2])

        d_FA_sum_reshaped = self.feature_d_FA_sum.reshape((15, self.num_frames))
        fig_d_FA_sum_reshaped = self.plot_15_row_(d_FA_sum_reshaped, time_stamp_array, title='dFA-I sum')
        # self.plot_columns_sec_wise_(sns.lineplot, d_FA_sum_reshaped)
        # self.plot_columns_sec_wise_(sns.scatterplot, FA_event_reshaped)
        # d_FA_sum_reshaped -= np.min(d_FA_sum_reshaped)
        # d_FA_sum_reshaped /= (np.max(d_FA_sum_reshaped) - np.min(d_FA_sum_reshaped))

        FA_sum_reshaped = self.sum_value_list.reshape((15, self.num_frames))
        # self.plot_columns_sec_wise_(sns.lineplot, FA_sum_reshaped, time_stamp=time_stamp_array)
        fig_FA_sum_reshaped = self.plot_15_row_(FA_sum_reshaped, time_stamp_array, title='FA-I sum')
        # FA_sum_reshaped -= np.min(FA_sum_reshaped)
        # FA_sum_reshaped /= (np.max(FA_sum_reshaped) - np.min(FA_sum_reshaped))

        SA_reshaped = self.feature_dSA

        fig_FA, axes_FA = plt.subplots(3, 1,
                                       sharex='all',
                                       sharey=False,
                                       constrained_layout=True,
                                       figsize=(15, 15))
        axes_FA[0].imshow(FA_event_reshaped,
                          aspect='auto',
                          # cmap=plt.cm.gray,
                          interpolation='nearest')
        for i in range(len(d_FA_sum_reshaped)):
            axes_FA[1].plot(d_FA_sum_reshaped[i, :], color='b')
            axes_FA[2].plot(FA_sum_reshaped[i, :], color='r')

        # plot FA events in vertical lines
        fig_SFA_event_2 = self.plot_tactile_events_vlines_(FA_event_reshaped, SA_event_reshaped, gap=5, length=2)

        fig_All_events_img, axes_All_events_img = plt.subplots(4, 1,
                                                               sharex='all',
                                                               sharey='all',
                                                               constrained_layout=True,
                                                               figsize=(10, 5))
        axes_All_events_img[0].imshow(FA_event_reshaped, aspect='auto', cmap=plt.cm.Purples, interpolation='nearest')
        axes_All_events_img[0].axis('off')
        axes_All_events_img[1].imshow(SA_event_reshaped[0], aspect='auto', cmap=plt.cm.Blues, interpolation='nearest')
        axes_All_events_img[1].axis('off')
        axes_All_events_img[2].imshow(SA_event_reshaped[1], aspect='auto', cmap=plt.cm.Oranges, interpolation='nearest')
        axes_All_events_img[2].axis('off')
        axes_All_events_img[3].imshow(SA_event_reshaped[2], aspect='auto', cmap=plt.cm.Greens, interpolation='nearest')
        axes_All_events_img[3].axis('off')

        if save:
            g2.savefig(img_name_head + 'fig_all_events_scatter' + '.svg')
            fig_d_FA_sum_reshaped.savefig(img_name_head + 'fig_d_FA_sum_reshaped' + '.svg')
            fig_FA_sum_reshaped.savefig(img_name_head + 'fig_FA_sum_reshaped' + '.svg')
            fig_FA.savefig(img_name_head + 'fig_FA_events' + '.svg')
            fig_All_events_img.savefig(img_name_head + 'fig_All_events_img' + '.svg')
            fig_SFA_event_2.savefig(img_name_head + 'fig_SFA_event' + '.svg')

            g2.savefig(img_name_head + 'fig_all_events_scatter' + '.png')
            fig_d_FA_sum_reshaped.savefig(img_name_head + 'fig_d_FA_sum_reshaped' + '.png')
            fig_FA_sum_reshaped.savefig(img_name_head + 'fig_FA_sum_reshaped' + '.png')
            fig_FA.savefig(img_name_head + 'fig_FA_events' + '.svg')
            fig_All_events_img.savefig(img_name_head + 'fig_All_events_img' + '.png')
            fig_SFA_event_2.savefig(img_name_head + 'fig_SFA_event' + '.png')

    def plot_example(self, save=0, img_name_head='GTac_plot', exmp_finger=1, exmp_sec=2):
        self.get_assigned_sec_wise()
        feature_events_melted = pd.melt(self.feature_assigned_sec_wise_pd,
                                        id_vars=['finger', 'section', 'milliseconds'],
                                        value_vars=['feature_FA_event',
                                                    'feature_SA_event_x',
                                                    'feature_SA_event_y',
                                                    'feature_SA_event_z'],
                                        var_name='Events Type',
                                        value_name='Tactile Events')
        FAI_cols = self.data_assigned_sec_wise_pd.columns[:16]
        SAII_cols = self.data_assigned_sec_wise_pd.columns[16:19]
        # data_pd = copy.copy(self.data_pd)
        FAI_melted = pd.melt(self.data_assigned_sec_wise_pd, id_vars=['finger', 'section', 'milliseconds'],
                             value_vars=FAI_cols)
        SAII_melted = pd.melt(self.data_assigned_sec_wise_pd, id_vars=['finger', 'section', 'milliseconds'],
                              value_vars=SAII_cols)
        d_FA_sum_reshaped = self.feature_d_FA_sum.reshape((15, self.num_frames))
        d_SA_reshaped = self.feature_dSA.reshape((3, 15, self.num_frames))
        FA_event_reshaped = self.feature_FA_event.reshape((15, self.num_frames))
        SA_event_reshaped = self.feature_SA_event.reshape((3, 15, self.num_frames))

        # example plot tp show FA, dFA, FA events, SA, dSA, and SA events
        exmp_sec_index = exmp_finger * 3 + exmp_sec

        FA_event_pos_index = np.where(FA_event_reshaped[exmp_sec_index] == 1)
        # print('Number of FA+ events: {} --> {}'.format(len(FA_event_pos_index[0]), FA_event_pos_index))
        FA_event_neg_index = np.where(FA_event_reshaped[exmp_sec_index] == -1)
        # print('Number of FA- events: {}'.format(len(FA_event_neg_index[0])))
        SA_x_event_pos_index = np.where(SA_event_reshaped[0, exmp_sec_index] == 1)
        SA_x_event_neg_index = np.where(SA_event_reshaped[0, exmp_sec_index] == -1)
        SA_y_event_pos_index = np.where(SA_event_reshaped[1, exmp_sec_index] == 1)
        SA_y_event_neg_index = np.where(SA_event_reshaped[1, exmp_sec_index] == -1)
        SA_z_event_pos_index = np.where(SA_event_reshaped[2, exmp_sec_index] == 1)
        SA_z_event_neg_index = np.where(SA_event_reshaped[2, exmp_sec_index] == -1)

        fig_exmp, axes_exmp = plt.subplots(6, 1,
                                           sharex=False,
                                           sharey=False,
                                           constrained_layout=True,
                                           figsize=(12, 12),
                                           gridspec_kw={'height_ratios': [2, 1, 0.7, 2, 1, 2]})
        g1 = sns.lineplot(data=FAI_melted.loc[(FAI_melted['finger'] == 1) & (FAI_melted['section'] == 2)],
                          x='milliseconds',
                          y='value',
                          hue='variable',
                          ax=axes_exmp[0],
                          ci=None,
                          dashes=False,
                          legend=False,
                          palette="Reds")
        g1.set(xlabel=None)
        g1.set(ylabel=None)

        axes_exmp[1].plot(d_FA_sum_reshaped[exmp_sec_index, :], color='purple', )
        axes_exmp[2].hlines(y=0, xmin=0, xmax=self.num_frames, colors='purple', lw=1)
        axes_exmp[2].vlines(x=FA_event_pos_index, ymin=0, ymax=3,
                            colors='purple', ls='-', lw=2,
                            label='FA_event_pos_index')
        axes_exmp[2].vlines(x=FA_event_neg_index, ymin=0, ymax=-3,
                            colors='purple', ls='--', lw=2,
                            label='FA_event_pos_index')
        axes_exmp[2].set_ylim((-4, 4))
        # axes_exmp[2].set_yticks([])
        # axes_exmp[2].spines['left'].set_visible(False)

        g2 = sns.lineplot(data=SAII_melted.loc[(SAII_melted['finger'] == 1) & (SAII_melted['section'] == 2)],
                          x='milliseconds',
                          y='value',
                          hue='variable',
                          ax=axes_exmp[3],
                          ci=None,
                          dashes=False,
                          legend=False,
                          palette="tab10")
        g2.set(xlabel=None)
        g2.set(ylabel=None)

        axes_exmp[4].plot(d_SA_reshaped[0, exmp_sec_index, :])
        axes_exmp[4].plot(d_SA_reshaped[1, exmp_sec_index, :])
        axes_exmp[4].plot(d_SA_reshaped[2, exmp_sec_index, :])

        gap = 7
        length = 3
        level1_y = gap
        level2_y = 0
        level3_y = -gap

        axes_exmp[5].hlines(y=level1_y, xmin=0, xmax=self.num_frames, colors='g', lw=1)
        axes_exmp[5].hlines(y=level2_y, xmin=0, xmax=self.num_frames, colors='b', lw=1)
        axes_exmp[5].hlines(y=level3_y, xmin=0, xmax=self.num_frames, colors='orange', lw=1)
        axes_exmp[5].vlines(x=SA_z_event_pos_index, ymin=level1_y, ymax=level1_y + length,
                            colors='g', ls='-', lw=2,
                            label='FA_event_pos_indez')
        axes_exmp[5].vlines(x=SA_z_event_neg_index, ymin=level1_y, ymax=level1_y - length,
                            colors='g', ls='--', lw=2,
                            label='FA_event_pos_indez')

        axes_exmp[5].vlines(x=SA_x_event_pos_index, ymin=level2_y, ymax=level2_y + length,
                            colors='b', ls='-', lw=2,
                            label='FA_event_pos_index')
        axes_exmp[5].vlines(x=SA_x_event_neg_index, ymin=level2_y, ymax=level2_y - length,
                            colors='b', ls='--', lw=2,
                            label='FA_event_pos_index')

        axes_exmp[5].vlines(x=SA_y_event_pos_index, ymin=level3_y, ymax=level3_y + length,
                            colors='orange', ls='-', lw=2,
                            label='FA_event_pos_indey')
        axes_exmp[5].vlines(x=SA_y_event_neg_index, ymin=level3_y, ymax=level3_y - length,
                            colors='orange', ls='--', lw=2,
                            label='FA_event_pos_indey')
        axes_exmp[5].set_ylim((-gap - length - 2, gap + length + 2))
        # axes_exmp[5].set_yticks([])
        # axes_exmp[5].spines['left'].set_visible(False)
        for ax in axes_exmp:
            ax.set_xticks([])
            # ax.spines['top'].set_visible(False)
            # ax.spines['right'].set_visible(False)
            # ax.spines['bottom'].set_visible(False)
            # ax.spines['left'].set_visible(False)

        if save:
            fig_exmp.savefig(img_name_head + 'fig_example' + '.svg')
            fig_exmp.savefig(img_name_head + 'fig_example' + '.png')


class gtac_data_analysis(gtac_data):
    def __init__(self, filenames_, task='ECS', skip_head=500,
                 skip_char_fname=0, renew_label=False, load_all=True, add_sec_features=False):
        # filenames: input the filenames of data that belong to one set of experiments
        # skip_head: skip n data head frames for each set of data
        # skip_char_fname: skip n letters in filenames to obtain proper labels
        # renew_label: re-order the labels in the dataset for plotting sometimes
        # load_all: check whether to load from saved dataset file or not, if not exist, save dataset in to csv. (if False, able to read single csv)
        # add_sec_features: whether to add sec wise features to dataset for machine learning
        self.filenames = filenames_
        self.load_all = load_all
        self.add_sec = add_sec_features
        self.foldername = os.path.dirname(filenames_[0])
        self.data_pd_all = pd.DataFrame()
        self.task = task
        self.sec_wise_features_all = np.array([]).reshape((14, 5, 3, 0))
        self.data_pd_all_filename = self.foldername + '/saved/data_pd_all.csv'
        self.sec_wise_features_all_filename = self.foldername + '/saved/sec_wise_features_all.npy'
        self.load_all_data(skip_row=skip_head, skip_filename=skip_char_fname)
        self.renew_label = renew_label
        self.prepare_dataset(task=task, renew_label=renew_label)

    @staticmethod
    def get_label_from_filename(filename, skip=0):
        filename = ntpath.basename(filename)
        filename = filename[skip:]
        label = ''
        for x, c in enumerate(filename):
            if not c == '_':
                label += c
            elif not filename[x + 1].isdigit():
                label += c
            elif filename[x + 1].isdigit():
                break
        return label

    def load_all_data(self, skip_row=0, skip_filename=0):
        if os.path.isfile(self.data_pd_all_filename) and os.path.isfile(
                self.sec_wise_features_all_filename) and self.load_all:
            self.data_pd_all = pd.read_csv(self.data_pd_all_filename, index_col=0, skiprows=0)
            self.sec_wise_features_all = np.load(self.sec_wise_features_all_filename)
        else:
            print('loading the data')
            for f in self.filenames:
                _gtac_data_set = gtac_data(filename=f)
                # discard the head dataframe during the process of execution
                _gtac_data_set_pd = _gtac_data_set.data_pd.iloc[skip_row:]
                _gtac_data_set_sec_wise_features = _gtac_data_set.sec_wise_features[:, :, :, skip_row:]
                # describe a channel of data
                # _, _, f0s0_mag_z = gtac_data.find_SAII_index(0, 0)
                # gtac_data_analysis.describe_channel(_gtac_data_set_pd, f0s0_mag_z)

                # obtain the label from filename
                _label = gtac_data_analysis.get_label_from_filename(filename=f, skip=skip_filename)
                _gtac_data_set_pd = _gtac_data_set_pd.assign(label=_label)
                # _gtac_data_set_pd['label'] = _label
                print('got Label: {}'.format(_label))
                self.data_pd_all = pd.concat([self.data_pd_all, _gtac_data_set_pd])
                self.sec_wise_features_all = np.concatenate(
                    [self.sec_wise_features_all, _gtac_data_set_sec_wise_features],
                    axis=3)
                print('loaded {} shape of data in {}'.format(_gtac_data_set_pd.shape, f))
            if self.load_all:
                self.data_pd_all.to_csv(self.data_pd_all_filename)
                print('Saved: shape {} in {}'.format(self.data_pd_all.shape, self.data_pd_all_filename))
                np.save(self.sec_wise_features_all_filename, self.sec_wise_features_all)
                print('Saved: shape {} in {}'.format(self.sec_wise_features_all.shape,
                                                     self.sec_wise_features_all_filename))
        print(
            'ALL dataframes have been loaded, data_pd_all: {}; sec_wise_features_all: {}'.format(self.data_pd_all.shape,
                                                                                                 self.sec_wise_features_all.shape))
        # print(self.data_pd_all.describe())
        self.sec_wise_features_all = self.sec_wise_features_all.T
        # creat labels and their index
        self.LABEL = self.data_pd_all.label.unique().tolist()
        print('{} labels contained in the dataset:{}'.format(len(self.LABEL), self.LABEL))

    def re_order_label_ECS(self):
        self.LABEL = np.unique(self.dataset[:, -1]).tolist()
        # reorder the label for plotting
        if self.task == 'ECS' and len(self.LABEL) == gtac_config.ECS_LABEL_REORDER:
            if self.renew_label:
                self.LABEL = [self.LABEL[i] for i in gtac_config.ECS_LABEL_REORDER]
            else:
                self.LABEL = [self.LABEL[i] for i in gtac_config.ECS_LABEL_REORDER]
        if self.task == 'sharpness_detection':
            if self.renew_label:
                self.LABEL = [self.LABEL[i] for i in gtac_config.SD_NEW_LABEL_REORDER]
            else:
                self.LABEL = [self.LABEL[i] for i in gtac_config.SD_LABEL_REORDER]
        print('Reordered Label: {}'.format(self.LABEL))

    @staticmethod
    def describe_channel(df, channel):
        print(df.iloc[:, channel].describe())

    def choose_sec_focus(self, f, s):
        # only return the data of interested finger section
        sec_index = self.find_sec_index(finger=f, sec=s)  # 19 index of the section
        return self.choose_channel_focus(sec_index)

    def choose_channel_focus(self, channels):
        # only return the data of channels that are interested in
        # channels: list -> [a,b,c,d,...]
        channels = list(channels)
        return self.data_pd_all.iloc[:, channels]

    def shuffle_dataset(self):
        print('Dataset shuffled')
        self.dataset, self.sec_wise_features_all = shuffle(self.dataset,
                                                           self.sec_wise_features_all)

    @staticmethod
    def print_unique(data_array):
        unique_elements, counts_elements = np.unique(data_array, return_counts=True)
        print("Frequency of unique values of the said array:")
        print(np.asarray((unique_elements, counts_elements)))

    def prepare_dataset(self, task='sharpness_detection', renew_label=False):
        # prepare the dataset for learning-based recognition
        # data: [:, :-1]
        # label: [:, -1]
        # Dataset shape: ECS --> (n, 285+1)
        #                sharpness_detection --> (n, 21+1)
        if task == 'sharpness_detection':
            self.dataset = self.choose_sec_focus(f=0, s=0)
            self.dataset = np.hstack(
                [self.dataset,
                 np.expand_dims(self.sec_wise_features_all[2, 0, 0, :], axis=1)])  # add feature of sum of FA-I
            self.dataset = np.hstack(
                [self.dataset, np.expand_dims(self.sec_wise_features_all[5, 0, 0, :], axis=1)])  # add feature of SFA-z
            self.dataset = np.hstack(
                [self.dataset, np.expand_dims(self.sec_wise_features_all[8, 0, 0, :], axis=1)])  # add feature of dSA-z
            self.dataset = np.hstack(
                [self.dataset, np.expand_dims(self.data_pd_all.label.to_numpy(), axis=1)])  # add label
            # renew label to have less levels
            if renew_label:
                self.dataset[[self.dataset[:, -1] == '1mm'][0], -1] = 'level1'
                self.dataset[[self.dataset[:, -1] == '2mm'][0], -1] = 'level1'
                self.dataset[[self.dataset[:, -1] == '3mm'][0], -1] = 'level2'
                self.dataset[[self.dataset[:, -1] == '4mm'][0], -1] = 'level2'
                self.dataset[[self.dataset[:, -1] == '6mm'][0], -1] = 'level3'

                self.LABEL = np.unique(self.dataset[:, -1]).tolist()

            self.dataset = self.dataset[self.dataset[:, 19] > 150, :]  # fileter the dataset by FA-I sum
        # Extrinsic Contact Sensing Task
        if task == 'ECS':
            self.dataset = self.data_pd_all.iloc[:, :gtac_config.ALL_GTAC_NUM].to_numpy()
            if self.add_sec:
                shape_ = self.sec_wise_features_all.shape
                sec_wise_features_reshaped = self.sec_wise_features_all.reshape(
                    [shape_[0], shape_[1] * shape_[2] * shape_[3]])
                self.dataset = np.concatenate([self.dataset, sec_wise_features_reshaped], axis=-1)
            self.dataset = np.hstack([self.dataset, np.expand_dims(self.data_pd_all.label.to_numpy(), axis=1)])
        print('Dataset has been prepared: {}'.format(self.dataset.shape))

        self.print_unique(self.dataset[:, -1])
        # unique_elements, counts_elements = np.unique(self.dataset[:, -1], return_counts=True)
        # print("Frequency of unique values of the said array:")
        # print(np.asarray((unique_elements, counts_elements)))

    def data_split(self, SPILTRATIO=0.3, SHUFFLE=True):
        # SPILTRATIO: split ratio to partitioning data for test.
        if SHUFFLE:
            self.shuffle_dataset()
        CUTPoint = int(len(self.dataset) * (1 - SPILTRATIO))
        x_train = self.dataset[:CUTPoint, :-1]
        x_val = self.dataset[CUTPoint:, :-1]
        y_train = self.dataset[:CUTPoint, -1]
        y_val = self.dataset[CUTPoint:, -1]
        print('Dataset shape after split: train set: {}, validation set: {}'.format(x_train.shape, x_val.shape))
        return x_train, y_train, x_val, y_val, CUTPoint

    @staticmethod
    def confs_matrix(y_truth, y_predict, plot, title='title'):
        confs_matrix = confusion_matrix(y_truth, y_predict)
        if plot:
            f, ax = plt.subplots(figsize=(6, 6))
            sns.heatmap(confs_matrix, annot=True, fmt="d", linewidths=.5, ax=ax)
            f.suptitle(title)

    def SVM(self, save=False, folder='model', remark='normal'):
        x_train, y_train, x_val, y_val, CUTPoint = self.data_split(SPILTRATIO=0.33, SHUFFLE=True)

        # scaler_train = preprocessing.StandardScaler().fit(x_train)
        # x_train = scaler_train.transform(x_train)
        #
        # x_val = scaler_train.transform(x_val)

        clf = svm.SVC(probability=True).fit(x_train, y_train)
        score_test = clf.score(x_val, y_val)
        y_predict = clf.predict(x_val)
        print('SVM Score: {}'.format(score_test))
        gtac_data_analysis.confs_matrix(y_val, y_predict, plot=True, title='SVM')

        if save:
            timestr = time.strftime("%Y%m%d_%H%M%S")

            filename = folder + '/' + self.task + '_SVM_clf_' + remark + '_' + timestr + '.sav'
            pickle.dump(clf, open(filename, 'wb'))
            print('Saved Classifier: ' + filename)
        return clf

    def LDA(self, save=False, folder='model', remark='normal'):
        x_train, y_train, x_val, y_val, CUTPoint = self.data_split(SPILTRATIO=0.33, SHUFFLE=True)

        # scaler_train = preprocessing.StandardScaler().fit(x_train)
        # x_train = scaler_train.transform(x_train)
        #
        # x_val = scaler_train.transform(x_val)

        clf = LinearDiscriminantAnalysis().fit(x_train, y_train)
        score_test = clf.score(x_val, y_val)
        y_predict = clf.predict(x_val)
        print('LDA Score: {}'.format(score_test))
        gtac_data_analysis.confs_matrix(y_val, y_predict, plot=True, title='LDA')

        if save:
            timestr = time.strftime("%Y%m%d_%H%M%S")

            filename = folder + '/' + self.task + '_LDA_clf_' + remark + '_' + timestr + '.sav'
            pickle.dump(clf, open(filename, 'wb'))
            print('Saved Classifier: ' + filename)
        return clf

    def QDA(self, save=False, folder='model', remark='normal'):
        x_train, y_train, x_val, y_val, CUTPoint = self.data_split(SPILTRATIO=0.33, SHUFFLE=True)

        # scaler_train = preprocessing.StandardScaler().fit(x_train)
        # x_train = scaler_train.transform(x_train)
        #
        # x_val = scaler_train.transform(x_val)
        kf = KFold(n_splits=5)
        # Merge inputs and targets
        inputs = np.concatenate((x_train, x_val), axis=0)
        targets = np.concatenate((y_train, y_val), axis=0)
        scores_fold = []
        precision_fold = []
        precision_weighted_fold = []
        recall_fold = []
        recall_weighted_fold = []
        save_path = 'data/ECS_recognition_offline_results3/'
        for train, test in kf.split(inputs, targets):
            clf = QuadraticDiscriminantAnalysis().fit(inputs[train], targets[train])
            score_test = clf.score(inputs[test], targets[test])
            y_predict = clf.predict(inputs[test])
            print('QDA Score: {}'.format(score_test))
            gtac_data_analysis.confs_matrix(targets[test], y_predict, plot=True, title='QDA')
            scores_fold.append(score_test)
            precision_weighted_fold.append(list(metrics.precision_score(targets[test], y_predict, average=None)))
            recall_weighted_fold.append(list(metrics.recall_score(targets[test], y_predict, average=None)))
            precision_fold.append(metrics.precision_score(targets[test], y_predict, average='weighted'))
            recall_fold.append(metrics.recall_score(targets[test], y_predict, average='weighted'))

        scores_fold_pd = np.array(scores_fold)
        precision_fold_pd = np.array(precision_fold)
        recall_fold_pd = np.array(recall_fold)
        precision_weighted_fold_pd = np.array(precision_weighted_fold)
        recall_weighted_fold_pd = np.array(recall_weighted_fold)

        if save:
            if self.add_sec:
                remark_name = 'QDA_5_fold_with_sec_feature_'
            else:
                remark_name = 'QDA_5_fold_no_sec_feature_'
            np.save(save_path + remark_name + '_score.csv', scores_fold_pd)
            np.save(save_path + remark_name + '_precision.csv', precision_fold_pd)
            np.save(save_path + remark_name + '_recall.csv', recall_fold_pd)
            np.save(save_path + remark_name + '_precision_weighted.csv', precision_weighted_fold_pd)
            np.save(save_path + remark_name + '_recall_weighted.csv', recall_weighted_fold_pd)

            timestr = time.strftime("%Y%m%d_%H%M%S")
            filename = folder + '/' + self.task + '_QDA_clf_' + remark + '_' + timestr + '.sav'
            pickle.dump(clf, open(filename, 'wb'))
            print('Saved Classifier: ' + filename)
        return clf

    def logistic_regression(self, save=False, folder='model', remark='normal'):
        x_train, y_train, x_val, y_val, CUTPoint = self.data_split(SPILTRATIO=0.33, SHUFFLE=True)

        # scaler_train = preprocessing.StandardScaler().fit(x_train)
        # x_train = scaler_train.transform(x_train)
        #
        # x_val = scaler_train.transform(x_val)

        clf = LogisticRegression(random_state=0).fit(x_train, y_train)
        score_test = clf.score(x_val, y_val)
        y_predict = clf.predict(x_val)
        print('Logistic Regression Score: {}'.format(score_test))
        gtac_data_analysis.confs_matrix(y_val, y_predict, plot=True, title='Logistic Regression')

        if save:
            timestr = time.strftime("%Y%m%d_%H%M%S")

            filename = folder + '/' + self.task + '_logistic_reg_clf_' + remark + '_' + timestr + '.sav'
            pickle.dump(clf, open(filename, 'wb'))
            print('Saved Classifier: ' + filename)
        return clf

    @staticmethod
    def reshape_for_CNN(data_train):
        # reshape the dataset for train in CNN
        # input shape: [N, 285]
        # output shape: [N, 15, 19, 1]
        # in each sec (19 signals): [mat1, mat2, ..., mat16, magx, magy, magz]
        if len(data_train.shape) == 2:
            data_train = np.asarray(data_train).astype(np.float32)
        if len(data_train.shape) == 1:
            data_train = np.expand_dims(data_train, axis=0)
            data_train = np.asarray(data_train).astype(np.float32)

        for f in range(gtac_config.FINGER_NUM):
            for s in range(gtac_config.SEC_NUM):
                fai_index_sec = []
                saii_index = f * 9 + (2 - s) * 3
                x_train_saii_sec = data_train[:, saii_index:saii_index + 3]
                for i in range(gtac_config.MAT_NUM):  # MAT_NUM -> 16: there 4*4 sensing points on FA-I layer
                    r = i // 4
                    c = i % 4
                    fai_index = gtac_data.find_FAI_index(f, s, r, c)
                    fai_index_sec.append(fai_index)
                x_train_fai_sec = data_train[:, fai_index_sec]
                x_train_sec = np.concatenate([x_train_fai_sec, x_train_saii_sec], axis=1)
                x_train_sec = np.expand_dims(x_train_sec, axis=1)
                if f == 0 and s == 0:
                    x_train_reshaped = x_train_sec
                else:
                    x_train_reshaped = np.concatenate([x_train_reshaped, x_train_sec], axis=1)
        x_train_reshaped = np.expand_dims(x_train_reshaped, axis=-1)

        #  works, but unable to clarify finger sections
        # x_train_saii = data_train[:, :gtac_config.MAG_NUM]
        # x_train_saii = x_train_saii.reshape([len(x_train_saii), 15, 3, 1])
        # x_train_fai = data_train[:, gtac_config.MAG_NUM:gtac_config.ALL_GTAC_NUM]
        # x_train_fai = x_train_fai.reshape([len(x_train_fai), 15, 16, 1])
        # x_train_reshaped = np.concatenate([x_train_fai, x_train_saii], axis=2)

        return x_train_reshaped

    def pos_norm(self, inputs):
        #  normalize to 0 to 1
        inputs_norm = (inputs - np.min(inputs)) / (np.max(inputs) - np.min(inputs))
        return inputs_norm

    def pos_neg_norm(self, inputs):
        #  normalize to -1 to 1
        inputs_norm = 2 * (inputs - np.min(inputs)) / (
                np.max(inputs) - np.min(inputs)) - 1
        return inputs_norm

    def plot_samples_in_img(self, inputs, to_save=False, path='fig/data_img_sample/'):
        pos_color = 'YlGnBu'
        pos_neg_color = 'PiYG'
        bin_color = 'gray'
        inputs_16 = inputs[:, :, :16, :]
        inputs_16_19 = inputs[:, :, 16:19, :]  # saii
        inputs_19_21 = inputs[:, :, 19:21, :]  # loc row col
        inputs_21_22 = inputs[:, :, 21:22, :]  # fai sum
        inputs_22_23 = inputs[:, :, 22:23, :]  # d fai sum
        inputs_23_26 = inputs[:, :, 23:26, :]  # SFA
        inputs_26_29 = inputs[:, :, 26:29, :]  # dSA
        inputs_29_33 = inputs[:, :, 29:33, :]  # fai, saii events

        counts = np.bincount(np.where(inputs_29_33[:, :, :, 0] != 0)[0])

        for c in np.where(counts == 2)[0]:
            if 1 in inputs_29_33[c, :, :, 0] and -1 in inputs_29_33[c, :, :, 0]:
                i_samp = c
                print(i_samp)
                break

        # norm for only pos
        inputs_16_norm = self.pos_norm(inputs_16)
        plt.figure()
        g = sns.heatmap(inputs_16_norm[i_samp, :, :, 0], cmap=pos_color, square=True,
                        cbar_kws={'format': "%.2f", "orientation": "horizontal", "shrink": .5},
                        # cbar_kws=dict(use_gridspec=True, location="top")
                        )
        if to_save:
            figure = g.get_figure()
            figure.savefig(path + 'inputs_16_norm.svg')
            figure.savefig(path + 'inputs_16_norm.png', dpi=300)
        plt.show()

        inputs_21_22_norm = self.pos_norm(inputs_21_22)
        plt.figure()
        g = sns.heatmap(inputs_21_22_norm[i_samp, :, :, 0], cmap=pos_color, square=True,
                        xticklabels=[21],
                        cbar_kws={'format': "%.2f", "orientation": "horizontal", "shrink": .1},
                        # cbar_kws=dict(use_gridspec=True, location="top"),
                        )
        if to_save:
            figure = g.get_figure()
            figure.savefig(path + 'inputs_21_22_norm.svg')
            figure.savefig(path + 'inputs_21_22_norm.png', dpi=300)
        plt.show()

        # norm for pos and neg
        inputs_16_19_norm = self.pos_neg_norm(inputs_16_19)
        plt.figure()
        g = sns.heatmap(inputs_16_19_norm[i_samp, :, :, 0], cmap=pos_neg_color, square=True,
                        xticklabels=[16, 17, 18], )
        if to_save:
            figure = g.get_figure()
            figure.savefig(path + 'inputs_16_19_norm.svg')
            figure.savefig(path + 'inputs_16_19_norm.png', dpi=300)
        # plt.show()
        inputs_19_21_norm = self.pos_neg_norm(inputs_19_21)
        plt.figure()
        g = sns.heatmap(inputs_19_21_norm[i_samp, :, :, 0], cmap=pos_neg_color, square=True,
                        xticklabels=[19], )
        if to_save:
            figure = g.get_figure()
            figure.savefig(path + 'inputs_19_21_norm.svg')
            figure.savefig(path + 'inputs_19_21_norm.png', dpi=300)
        # plt.show()
        inputs_22_23_norm = self.pos_neg_norm(inputs_22_23)
        plt.figure()
        g = sns.heatmap(inputs_22_23_norm[i_samp, :, :, 0], cmap=pos_neg_color, square=True,
                        xticklabels=[22], )
        if to_save:
            figure = g.get_figure()
            figure.savefig(path + 'inputs_22_23_norm.svg')
            figure.savefig(path + 'inputs_22_23_norm.png', dpi=300)
        # plt.show()
        inputs_23_26_norm = self.pos_neg_norm(inputs_23_26)
        plt.figure()
        g = sns.heatmap(inputs_23_26_norm[i_samp, :, :, 0], cmap=pos_neg_color, square=True,
                        vmin=-1, vmax=1,
                        xticklabels=[23, 24, 25], )
        if to_save:
            figure = g.get_figure()
            figure.savefig(path + 'inputs_23_26_norm.svg')
            figure.savefig(path + 'inputs_23_26_norm.png', dpi=300)
        # plt.show()
        inputs_26_29_norm = self.pos_neg_norm(inputs_26_29)
        plt.figure()
        g = sns.heatmap(inputs_26_29_norm[i_samp, :, :, 0], cmap=pos_neg_color, square=True,
                        xticklabels=[26, 27, 28], )
        if to_save:
            figure = g.get_figure()
            figure.savefig(path + 'inputs_26_29_norm.svg')
            figure.savefig(path + 'inputs_26_29_norm.png', dpi=300)
        # plt.show()

        plt.figure()
        g = sns.heatmap(inputs_29_33[i_samp, :, :, 0], cmap=bin_color, square=True,
                        xticklabels=[29, 30, 31, 32], )
        if to_save:
            figure = g.get_figure()
            figure.savefig(path + 'inputs_29_33.svg')
            figure.savefig(path + 'inputs_29_33.png', dpi=300)
        plt.tight_layout()
        plt.show()

    def CNN(self, save=False, folder='model', remark='normal'):
        x_train, y_train, x_val, y_val, CUTPoint = self.data_split(SPILTRATIO=0.33, SHUFFLE=True)
        # reshape the dataset
        x_train = gtac_data_analysis.reshape_for_CNN(data_train=x_train)
        if self.add_sec:
            # add sec wise features
            sec_wise_features_train = self.sec_wise_features_all[:CUTPoint]
            shape_ = sec_wise_features_train.shape
            sec_wise_features_train = sec_wise_features_train.reshape([shape_[0], 15, shape_[-1]])
            sec_wise_features_train = np.expand_dims(sec_wise_features_train, axis=-1)
            x_train = np.concatenate([x_train, sec_wise_features_train], axis=2)

        x_val = gtac_data_analysis.reshape_for_CNN(data_train=x_val)
        if self.add_sec:
            # add sec wise features
            sec_wise_features_val = self.sec_wise_features_all[CUTPoint:]
            shape_ = sec_wise_features_val.shape
            sec_wise_features_val = sec_wise_features_val.reshape([shape_[0], 15, shape_[-1]])
            sec_wise_features_val = np.expand_dims(sec_wise_features_val, axis=-1)
            x_val = np.concatenate([x_val, sec_wise_features_val], axis=2)

        # Model / data parameters
        num_classes = 9
        assert x_train.shape[-3:] == x_val.shape[-3:]
        input_shape = x_train.shape[-3:]

        kf = KFold(n_splits=5)
        # Merge inputs and targets
        inputs = np.concatenate((x_train, x_val), axis=0)
        targets = np.concatenate((y_train, y_val), axis=0)
        scores_fold = []
        loss_fold = []
        precision_fold = []
        precision_weighted_fold = []
        recall_fold = []
        recall_weighted_fold = []
        save_path = 'data/ECS_recognition_offline_results_final/'
        # if self.add_sec:
        #     self.plot_samples_in_img(inputs, to_save=False)
        for train, test in kf.split(inputs, targets):
            # # convert class vectors to binary class matrices
            encoder = LabelBinarizer()
            y_train_bin = encoder.fit_transform(targets[train])
            y_val_bin = encoder.fit_transform(targets[test])

            model = keras.Sequential(
                [
                    keras.Input(shape=input_shape),
                    layers.Conv2D(8, kernel_size=(3, 3), activation="relu"),
                    layers.MaxPooling2D(pool_size=(2, 2)),
                    layers.Conv2D(16, kernel_size=(3, 3), activation="relu"),
                    layers.MaxPooling2D(pool_size=(2, 2)),
                    layers.Flatten(),
                    layers.Dropout(0.5),
                    layers.Dense(num_classes, activation="softmax"),
                ]
            )
            model.summary()

            batch_size = 128
            epochs = 15

            model.compile(loss="categorical_crossentropy",
                          optimizer="adam", metrics=["accuracy"])
            cnn_history = model.fit(inputs[train], y_train_bin,
                                    batch_size=batch_size,
                                    epochs=epochs,
                                    validation_split=0.1)

            # Evaluate the trained model
            score = model.evaluate(inputs[test], y_val_bin, verbose=0)
            print("Test loss:", score[0])
            print("Test accuracy:", score[1])

            y_predict = encoder.inverse_transform(model.predict(inputs[test]))
            gtac_data_analysis.confs_matrix(targets[test][:9000], y_predict[:9000], plot=True, title='CNN')

            scores_fold.append(score[1])
            loss_fold.append(score[0])
            precision_weighted_fold.append(list(metrics.precision_score(targets[test], y_predict, average=None)))
            recall_weighted_fold.append(list(metrics.recall_score(targets[test], y_predict, average=None)))
            precision_fold.append(metrics.precision_score(targets[test], y_predict, average='weighted'))
            recall_fold.append(metrics.recall_score(targets[test], y_predict, average='weighted'))

            # # Visualize history
            # # Plot history: Loss
            # fig, ax = plt.subplots(1, 1)
            # ax.plot(cnn_history.history['val_loss'], label='Validation')
            # ax.plot(cnn_history.history['loss'], label='Train')
            # ax.set_title('Loss history')
            # ax.set_ylabel('Loss value')
            # ax.set_xlabel('No. epoch')
            # ax.legend()
            # # plt.show()
            #
            # # Plot history: Accuracy
            # fig, ax = plt.subplots(1, 1)
            # ax.plot(cnn_history.history['val_accuracy'], label='Validation')
            # ax.plot(cnn_history.history['accuracy'], label='Train')
            # ax.set_title('Accuracy history')
            # ax.set_ylabel('Accuracy value (%)')
            # ax.set_xlabel('No. epoch')
            # ax.legend()
            # # plt.show()
        scores_fold_pd = np.array(scores_fold)
        loss_fold_pd = np.array(loss_fold)
        precision_fold_pd = np.array(precision_fold)
        recall_fold_pd = np.array(recall_fold)
        precision_weighted_fold_pd = np.array(precision_weighted_fold)
        recall_weighted_fold_pd = np.array(recall_weighted_fold)

        if save:

            if self.add_sec:
                remark_name = 'CNN_5_fold_with_sec_feature_'
            else:
                remark_name = 'CNN_5_fold_no_sec_feature_'
            np.save(save_path + remark_name + '_score.csv', scores_fold_pd)
            np.save(save_path + remark_name + '_loss.csv', loss_fold_pd)
            np.save(save_path + remark_name + '_precision.csv', precision_fold_pd)
            np.save(save_path + remark_name + '_recall.csv', recall_fold_pd)
            np.save(save_path + remark_name + '_precision_weighted.csv', precision_weighted_fold_pd)
            np.save(save_path + remark_name + '_recall_weighted.csv', recall_weighted_fold_pd)

            timestr = time.strftime("%Y%m%d_%H%M%S")

            filename = folder + '/' + self.task + '_CNN_clf_' + remark + '_' + timestr
            model.save(filename)
            print('Saved Classifier: ' + filename)

    def PCA(self, plot=False):
        pca = PCA(n_components=3)
        pca.fit(self.dataset[:, :-1])
        data_all_pca = pca.transform(self.dataset[:, :-1])

        pca10 = PCA(n_components=10)
        pca10.fit(self.dataset[:, :-1])
        print('PCA Variance Ratio: {}'.format(pca10.explained_variance_ratio_))
        # self.re_order_label_ECS()  # reorder the label for plotting
        if plot:
            markers = ['o', ',', '1', '2', '3', '4', '*', 'x', 'v']
            fig = plt.figure(figsize=(6, 6))
            ax = Axes3D(fig)
            # fig.add_axes(ax)
            # get colormap from seaborn
            cmap = ListedColormap(sns.color_palette("husl", 256).as_hex())
            xLabel = ax.set_xlabel('Feature-1', fontsize=10, fontweight='bold', color='k')
            yLabel = ax.set_ylabel('Feature-2', fontsize=10, fontweight='bold', color='k')
            zLabel = ax.set_zlabel('Feature-3', fontsize=10, fontweight='bold', color='k')
            for l_ind, l in enumerate(self.LABEL):
                sc = ax.scatter(data_all_pca[self.dataset[:, -1] == l, 0],
                                data_all_pca[self.dataset[:, -1] == l, 1],
                                data_all_pca[self.dataset[:, -1] == l, 2],
                                label=l,
                                marker='.', cmap=cmap, alpha=0.6)
            plt.legend(loc=2)
            plt.tight_layout()
            # plt.show()

            markers = ['o', ',', '1', '2', '3', '4', '*', 'x', 'v']
            fig2, ax = plt.subplots(1, 1)
            # get colormap from seaborn
            cmap = ListedColormap(sns.color_palette("husl", 256).as_hex())
            xLabel = ax.set_xlabel('Feature-1', fontsize=10, fontweight='bold', color='k')
            yLabel = ax.set_ylabel('Feature-2', fontsize=10, fontweight='bold', color='k')
            for l_ind, l in enumerate(self.LABEL):
                sc = ax.scatter(data_all_pca[self.dataset[:, -1] == l, 0],
                                data_all_pca[self.dataset[:, -1] == l, 1],
                                label=l,
                                marker='.', cmap=cmap, alpha=0.6)
            plt.legend(loc=2)
            plt.tight_layout()
            plt.show()
            return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filename", help="set filename to analyze")
    args = parser.parse_args()
    filename_1 = args.filename
    # filename_1 = 'data/to_draw_and_analysis_grasping_then_handover_700_GTAC_20210822_095834.csv'
    # filename_1 = 'data/test_2500_GTAC_Gripper20220206_125129.csv'
    # filename_1 = 'data/to_draw_and_analysis_grasping_only_700_GTAC_20210822_105214.csv'

    gtac_data_read = gtac_data(filename=filename_1, f_sum_th=20, saii_th=100, replace_aft_ct=True, cutting_point=3000)
    # gtac_data_read.plot_all(save=0, img_name_head='GTac_Gripper')
    gtac_data_read.plot_motors(save=0, img_name_head='GTac_Gripper')
    # gtac_data_read.plot_g_translate(save=1, img_name_head='fig/GTac_Gripper_in_hand')
    gtac_data_read.plot_g_transalte_and_motors(save=1, img_name_head='fig/GTac_Gripper_in_hand')
    # gtac_data_read.plot_tactile_events()
    # gtac_data_read.plot_example()
    # gtac_data_read.plot_all_line_in_one(save=1, img_name_head='fig/')
    plt.show()
    # dataset_path = 'data/ECS_wiping'
    # filenames = os.listdir(dataset_path)
    # for i, _f in enumerate(filenames):
    #     filenames[i] = dataset_path + '/' + _f
    #
    # data_analysis = gtac_data_analysis(filenames_=filenames, task='ECS', skip_head=0,
    #                                    skip_char_fname=7, renew_label=False)
    # # data_analysis.logistic_regression(save=True, folder='model')
    # fig = data_analysis.PCA(plot=True)
