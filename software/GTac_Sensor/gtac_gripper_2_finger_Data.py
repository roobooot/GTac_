import argparse
import copy

import numpy as np

from gtac_gripper_2_finger import gripper_2finger
import pandas as pd
from matplotlib import pyplot as plt

import gtac_config_gp2


class gtac_gp_2f_data:
    def __init__(self, filename):
        self.filename = filename
        self.data_pd = pd.read_csv(filename, index_col=0, skiprows=0)
        # # reduce the FA-I noise from average, below zero.
        # self.data_pd.iloc[:, gtac_config_gp2.MAG_NUM:gtac_config_gp2.ALL_GTAC_NUM][
        #     self.data_pd.iloc[:, gtac_config_gp2.MAG_NUM:gtac_config_gp2.ALL_GTAC_NUM] < 0] = 0
        self.data_seq = copy.copy(self.data_pd.to_numpy())
        self.time_stamp_array = self.data_seq[:, -1]
        self.num_frames = self.data_seq.shape[0]
        self.sum_value_list = np.zeros([gtac_config_gp2.FINGER_NUM,
                                        gtac_config_gp2.SEC_NUM,
                                        len(self.data_seq)])
        self.g_value_list = np.zeros([gtac_config_gp2.FINGER_NUM,
                                      gtac_config_gp2.SEC_NUM,
                                      len(self.data_seq)])
        self.press_location_r_list = np.zeros([gtac_config_gp2.FINGER_NUM,
                                               gtac_config_gp2.SEC_NUM,
                                               len(self.data_seq)])
        self.press_location_c_list = np.zeros([gtac_config_gp2.FINGER_NUM,
                                               gtac_config_gp2.SEC_NUM,
                                               len(self.data_seq)])
        self.cal_FAI_sum_press_loc()

    @staticmethod
    def find_FAI_sum_press_loc(data_frame_array, finger, sec, threshold=20):
        sum_r = 0
        sum_c = 0
        sum_value = 0
        press_location_r = 2.5
        press_location_c = 2.5
        for i in range(gtac_config_gp2.MAT_NUM):  # MAT_NUM -> 16: there 4*4 sensing points on FA-I layer
            r = i // 4
            c = i % 4
            index, value = gripper_2finger.find_FAI_value(data_frame_array, finger, sec, r, c)
            if value > threshold:  # threshold to remove noise for obtaining pressing location
                sum_r += (r + 1) * value
                sum_c += (c + 1) * value
                sum_value += value
            # update pressing locations
            if sum_value != 0:
                press_location_r = round(sum_r / sum_value, 1)
                press_location_c = round(sum_c / sum_value, 1)
        return sum_value, press_location_r, press_location_c

    def cal_FAI_sum_press_loc(self):
        for i, data_frame_array in enumerate(self.data_seq):
            for f in range(gtac_config_gp2.FINGER_NUM):
                for s in range(gtac_config_gp2.SEC_NUM):
                    sum_value, press_location_r, \
                    press_location_c = self.find_FAI_sum_press_loc(data_frame_array, f, s)
                    _, g_value = gripper_2finger.find_sec_data(data_frame_array, f, s, a=0.3)
                    self.press_location_r_list[f, s, i] = press_location_r - 1
                    self.press_location_c_list[f, s, i] = press_location_c - 1
                    self.sum_value_list[f, s, i] = sum_value
                    self.g_value_list[f, s, i] = g_value

    def plot_all(self):
        y_lab_ft_sz = 13
        x_lab_ft_sz = 13
        title_2_sz = 16
        fig1, axs1 = plt.subplots(3, 1,
                                  sharex='all',
                                  # sharey='all',
                                  constrained_layout=True,
                                  figsize=(13, 13))
        fig1.suptitle('GTac Data ' \
                      + self.filename, fontsize=16)
        axs1[0].plot(self.time_stamp_array, self.data_seq[:, 0], color='dodgerblue', linestyle='-',
                     label='Finger1-SA_II-x')
        axs1[0].plot(self.time_stamp_array, self.data_seq[:, 1], color='orange', linestyle='-', label='Finger1-SA_II-y')
        axs1[0].plot(self.time_stamp_array, self.data_seq[:, 2], 'g-', label='Finger1-SA_II-z')

        axs1[0].plot(self.time_stamp_array, self.data_seq[:, 3], color='dodgerblue', linestyle='--',
                     label='Finger2-SA_II-x')
        axs1[0].plot(self.time_stamp_array, self.data_seq[:, 4], color='orange', linestyle='--',
                     label='Finger2-SA_II-y')
        axs1[0].plot(self.time_stamp_array, self.data_seq[:, 5], 'g--', label='Finger2-SA_II-z')
        # axs1[0].set_title('SA-II', fontsize=title_2_sz)
        axs1[0].set_ylabel('Raw output (uT)', fontsize=y_lab_ft_sz)
        axs1[0].legend()

        axs1[1].plot(self.time_stamp_array, self.sum_value_list[0, 0, :], 'y-', label='Finger1-FA_I-sum')
        axs1[1].plot(self.time_stamp_array, self.g_value_list[0, 0, :], 'c-', label='Finger1-g')
        axs1[1].plot(self.time_stamp_array, self.sum_value_list[1, 0, :], 'y--', label='Finger2-FA_I-sum')
        axs1[1].plot(self.time_stamp_array, self.g_value_list[1, 0, :], 'c--', label='Finger2-g')
        axs1[1].axhline(y=900, color='grey', linestyle='-.')
        axs1[1].axhline(y=500, color='grey', linestyle='-.')
        # axs1[1].set_title('FA-I and motor trajectory', fontsize=title_2_sz)
        axs1[1].set_ylabel('Raw output', fontsize=y_lab_ft_sz)
        axs1[1].legend()

        axs1[2].plot(self.time_stamp_array, self.data_seq[:, -4], 'k-', label='Finger1-motor trajectory')
        axs1[2].plot(self.time_stamp_array, self.data_seq[:, -3], 'k--', label='Finger2-motor trajectory')
        # axs1[2].set_title('Motor trajectory', fontsize=title_2_sz)
        axs1[2].set_ylabel('Motor position (deg)', fontsize=y_lab_ft_sz)
        axs1[2].set_xlabel('Time (ms)', fontsize=x_lab_ft_sz)
        axs1[2].legend()

    def plot_SA_II_only(self):
        y_lab_ft_sz = 13
        x_lab_ft_sz = 13
        title_2_sz = 16
        fig1, axs1 = plt.subplots(1, 1,
                                  sharex='all',
                                  # sharey='all',
                                  constrained_layout=True,
                                  figsize=(13, 13))
        fig1.suptitle('GTac Data ' \
                      + self.filename, fontsize=16)
        axs1.plot(self.time_stamp_array, self.data_seq[:, 0], color='dodgerblue', linestyle='-',
                     label='Finger1-SA_II-x')
        axs1.plot(self.time_stamp_array, self.data_seq[:, 1], color='orange', linestyle='-', label='Finger1-SA_II-y')
        axs1.plot(self.time_stamp_array, self.data_seq[:, 2], 'g-', label='Finger1-SA_II-z')

        axs1.plot(self.time_stamp_array, self.data_seq[:, 3], color='dodgerblue', linestyle='--',
                     label='Finger2-SA_II-x')
        axs1.plot(self.time_stamp_array, self.data_seq[:, 4], color='orange', linestyle='--',
                     label='Finger2-SA_II-y')
        axs1.plot(self.time_stamp_array, self.data_seq[:, 5], 'g--', label='Finger2-SA_II-z')
        # axs1[0].set_title('SA-II', fontsize=title_2_sz)
        axs1.set_ylabel('Raw output (uT)', fontsize=y_lab_ft_sz)
        axs1.set_xlabel('Time (ms)', fontsize=y_lab_ft_sz)
        axs1.legend()

# Polynomial Regression
def polyfit(x, y, degree):
    results = {}

    coeffs = np.polyfit(x, y, degree)

     # Polynomial Coefficients
    results['polynomial'] = coeffs.tolist()

    # r-squared
    p = np.poly1d(coeffs)
    # fit values, and mean
    yhat = p(x)                         # or [p(z) for z in x]
    ybar = np.sum(y)/len(y)          # or sum(y)/len(y)
    ssreg = np.sum((yhat-ybar)**2)   # or sum([ (yihat - ybar)**2 for yihat in yhat])
    sstot = np.sum((y - ybar)**2)    # or sum([ (yi - ybar)**2 for yi in y])
    results['determination'] = ssreg / sstot

    return results

def plot_tweezer_gap():
    plt.figure()
    finger_gap = np.array([1, 6, 18, 13, 6, 5])
    object_diameter = np.array([0, 3, 9, 7, 3, 2])
    m, b = np.polyfit(finger_gap, object_diameter, 1)
    r_square = polyfit(finger_gap, object_diameter, 1)
    print(r_square)
    object = ['None', 'Rubber-3mm', 'Tube-9mm', 'Screw-7mm', 'Nut-3mm', 'Shaft-2mm']
    obj_marker = ['v', 'x', 'o', '1', '4', 'p']
    for i in range(len(finger_gap)):
        plt.scatter(finger_gap[i], object_diameter[i], label=object[i], marker=obj_marker[i])
    plt.plot(finger_gap, m * finger_gap + b, label='Fitting line', c='k')
    plt.xlabel('Motor position gap (deg)')
    plt.ylabel('Object size (mm)')
    plt.legend()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filename", help="set filename to analyze")
    args = parser.parse_args()
    filename_1 = args.filename
    # filename_1 = 'data/Gripper_two_fingered/egg_grasp_2.csv'

    gtac_data_read = gtac_gp_2f_data(filename=filename_1)
    # gtac_data_read.plot_all()
    gtac_data_read.plot_SA_II_only()
    plot_tweezer_gap()
    plt.show()
