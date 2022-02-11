import copy

from data_gen import raw_data_byts_checkout_2
from data_collect_fingers_five import COLUMNS_RAW_FINGER_DATA, MAG_NUM, COL_INDEX
from draw_bubbles_py_3 import setup_scatter_ax, plot_fingertip_2
import serial
import time
import pandas as pd
import numpy as np
import argparse
import matplotlib
# matplotlib.use('TkAgg')
from matplotlib import pyplot as plt, animation
from matplotlib.animation import FuncAnimation, PillowWriter
from gtac_gripper_2_finger import gripper_2finger

window_length = 600
x = np.linspace(0, window_length-1, window_length)
y = np.zeros(len(x))

mag_x = []
mag_y = []
mag_z = []


mag_x_f_w = {0: [], 1: []}
mag_y_f_w = {0: [], 1: []}
mag_z_f_w = {0: [], 1: []}

mat_x_0 = [4, 4, 4, 4, 3, 3, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1]
mat_y_0 = [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4]

mat_x = [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4]
mat_y = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4]

mat_x_f_w = {0: [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4], 1: [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4]}
mat_y_f_w = {0: [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4], 1: [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4]}

press_location_r = 2.5
press_location_r_f_w = [2.5, 2.5]
press_location_r_list = []
press_location_r_list_f_w = {0: [], 1: []}
press_location_c = 2.5
press_location_c_f_w = [2.5, 2.5]
press_location_c_list = []
press_location_c_list_f_w = {0: [], 1: []}
sum_value = 0
sum_value_f_w = [0, 0]
sum_value_list = []
sum_value_list_f_w = {0: [], 1: []}

mat_sz = np.zeros(16)
mat_sz_f_w = {0: np.zeros(16), 1: np.zeros(16)}
mat_amp_index = 10
pressing_loc_amp_index = 2
mat_loc_index = 0.001

fig_list = {}
ax1_scat_tri_mat_list = {}
ax1_scat_pre_loc_list = {}
ax2_magx_list = {}
ax2_magy_list = {}
ax2_magz_list = {}
ax3_mat_sum_list = {}
ax4_center_x_list = {}
ax4_center_y_list = {}

def update_vals(data_frame_array, finger=0, sec=0, window_len=200):
    global mag_x, mag_y, mag_z, sum_value, press_location_r, press_location_c, \
        sum_value_list, press_location_r_list, press_location_c_list

    tri_index = finger * 3
    sum_r = 0
    sum_c = 0

    sum_value = 0

    # update magnetic and resistive signals for GTac Bubbles
    for i in range(len(mat_x)):
        r = i // 4
        c = i % 4
        index, value = gripper_2finger.find_FAI_value(data_frame_array, finger, sec, r, c)
        if value > 20:  # threshold to remove noise for obtaining pressing location
            sum_r += (r + 1) * value
            sum_c += (c + 1) * value
            sum_value += value
            mat_sz[i] = abs(value * mat_amp_index)
        else:
            mat_sz[i] = 0
        mat_x[i] = c + 1 + data_frame_array[tri_index] * mat_loc_index
        mat_y[i] = r + 1 + data_frame_array[tri_index + 1] * mat_loc_index
    # update pressing locations
    if sum_value != 0:
        press_location_r = round(sum_r / sum_value, 1)
        press_location_c = round(sum_c / sum_value, 1)
    # update magnetic signals
    mag_x.append(data_frame_array[tri_index])
    mag_y.append(data_frame_array[tri_index + 1])
    mag_z.append(abs(data_frame_array[tri_index + 2]))
    sum_value_list.append(sum_value)
    press_location_r_list.append(press_location_r - 1)
    press_location_c_list.append(press_location_c - 1)
    if len(mag_x) > window_len:
        mag_x = mag_x[-window_len:]
        mag_y = mag_y[-window_len:]
        mag_z = mag_z[-window_len:]
        sum_value_list = sum_value_list[-window_len:]
        press_location_r_list = press_location_r_list[-window_len:]
        press_location_c_list = press_location_c_list[-window_len:]
    print('r:{};c:{}'.format(press_location_r, press_location_c))
    # update vals for plot gaussian
    # zarray = gaus2d(x=x_mesh, y=y_mesh,
    #                        mx=press_location_r,
    #                        my=press_location_c,
    #                        sx=1,
    #                        sy=1)
    print('updated valuables for finger-{} sec-{}, data: {}'.format(finger, sec, [mag_x[-1], mag_y[-1], mag_z[-1],
        sum_value_list[-1], press_location_r_list[-1], press_location_c_list[-1]]))

def update_vals_finger_wise(data_frame_array, finger=1, sec=2, window_len=200):
    global mag_x_f_w, mag_y_f_w, mag_z_f_w, sum_value_f_w, press_location_r_f_w, press_location_c_f_w, \
        sum_value_list_f_w, press_location_r_list_f_w, press_location_c_list_f_w

    tri_index = finger * 3
    sum_r = 0
    sum_c = 0
    sum_value_f_w = [0, 0]

    # update magnetic and resistive signals for GTac Bubbles
    for i in range(16):
        r = i // 4
        c = i % 4
        index, value = gripper_2finger.find_FAI_value(data_frame_array, finger, sec, r, c)
        if value > 20:  # threshold to remove noise for obtaining pressing location
            sum_r += (r + 1) * value
            sum_c += (c + 1) * value
            sum_value_f_w[finger] += value
            mat_sz_f_w[finger][i] = abs(value * mat_amp_index)
        else:
            mat_sz_f_w[finger][i] = 0
        mat_x_f_w[finger][i] = c + 1 + data_frame_array[tri_index] * mat_loc_index
        mat_y_f_w[finger][i] = r + 1 + data_frame_array[tri_index + 1] * mat_loc_index
    # update pressing locations
    if sum_value_f_w[finger] != 0:
        press_location_r_f_w[finger] = round(sum_r / sum_value_f_w[finger], 1)
        press_location_c_f_w[finger] = round(sum_c / sum_value_f_w[finger], 1)
    # update magnetic signals
    mag_x_f_w[finger].append(data_frame_array[tri_index])
    mag_y_f_w[finger].append(data_frame_array[tri_index + 1])
    mag_z_f_w[finger].append(abs(data_frame_array[tri_index + 2]))
    sum_value_list_f_w[finger].append(sum_value_f_w[finger])
    print(press_location_r_f_w[finger] - 1)
    press_location_r_list_f_w[finger].append(press_location_r_f_w[finger] - 1)
    press_location_c_list_f_w[finger].append(press_location_c_f_w[finger] - 1)
    if len(mag_x_f_w[finger]) > window_len:
        mag_x_f_w[finger] = mag_x_f_w[finger][-window_len:]
        mag_y_f_w[finger] = mag_y_f_w[finger][-window_len:]
        mag_z_f_w[finger] = mag_z_f_w[finger][-window_len:]
        sum_value_list_f_w[finger] = sum_value_list_f_w[finger][-window_len:]
        press_location_r_list_f_w[finger] = press_location_r_list_f_w[finger][-window_len:]
        press_location_c_list_f_w[finger] = press_location_c_list_f_w[finger][-window_len:]
    print('f:{}; s:{}; r:{}; c:{}'.format(finger, sec, press_location_r_f_w, press_location_c_f_w))

# define normalized 2D gaussian
def gaus2d(x=0, y=0, mx=0, my=0, sx=1, sy=1):
    return 1. / (2. * np.pi * sx * sy) * np.exp(-((x - mx) ** 2. / (2. * sx ** 2.) + (y - my) ** 2. / (2. * sy ** 2.)))


def plot_pressing_loc(scat, press_location_r, press_location_c, sec_sum):
    scat.set_offsets(np.array([press_location_c, press_location_r]))
    scat.set_sizes([sec_sum * pressing_loc_amp_index])


def set_data_sec(f4_ax1_scat_tri_mat, f4_ax1_scat_pre_loc,
                 f4_ax2_magx, f4_ax2_magy, f4_ax3_magz,
                 f4_ax3_mat_sum, f4_ax4_center_x, f4_ax4_center_y):
    plot_fingertip_2(f4_ax1_scat_tri_mat, mat_x, mat_y, mat_sz)
    plot_pressing_loc(f4_ax1_scat_pre_loc,
                      press_location_r,
                      press_location_c,
                      sum_value)
    if len(mag_x) == window_length:
        print(len(mag_x), len(mag_y), len(mag_z), len(sum_value_list), len(press_location_c_list),
              len(press_location_r_list))
        f4_ax2_magx.set_ydata(mag_x)
        f4_ax2_magy.set_ydata(mag_y)
        f4_ax3_magz.set_ydata(mag_z)
        f4_ax3_mat_sum.set_ydata(sum_value_list)
        f4_ax4_center_x.set_ydata(press_location_c_list)
        f4_ax4_center_y.set_ydata(press_location_r_list)

def set_data_sec_finger_wise(f4_ax1_scat_tri_mat, f4_ax1_scat_pre_loc,
                 f4_ax2_magx, f4_ax2_magy, f4_ax3_magz,
                 f4_ax3_mat_sum, f4_ax4_center_x, f4_ax4_center_y, finger):
    plot_fingertip_2(f4_ax1_scat_tri_mat, mat_x_f_w[finger], mat_y_f_w[finger], mat_sz_f_w[finger])
    plot_pressing_loc(f4_ax1_scat_pre_loc,
                      press_location_r_f_w[finger],
                      press_location_c_f_w[finger],
                      sum_value_f_w[finger])
    if len(mag_x_f_w[finger]) == window_length:
        print(len(mag_x_f_w[finger]), len(mag_y_f_w[finger]), len(mag_z_f_w[finger]), len(sum_value_list_f_w[finger]), len(press_location_c_list_f_w[finger]),
              len(press_location_r_list_f_w[finger]))
        f4_ax2_magx.set_ydata(mag_x_f_w[finger])
        f4_ax2_magy.set_ydata(mag_y_f_w[finger])
        f4_ax3_magz.set_ydata(mag_z_f_w[finger])
        f4_ax3_mat_sum.set_ydata(sum_value_list_f_w[finger])
        f4_ax4_center_x.set_ydata(press_location_c_list_f_w[finger])
        f4_ax4_center_y.set_ydata(press_location_r_list_f_w[finger])

def setup_scatter_ax2(ax):
    # rect is the box edge
    rect = plt.Rectangle((-1, -1),
                         5,
                         5,
                         ec='none', lw=2, fc='none')
    ax.add_patch(rect)
    ax.axes.xaxis.set_visible(False)
    ax.axes.yaxis.set_visible(False)
    scat_base = ax.scatter(mat_x_0, mat_y_0, s=1500, alpha=0.4)
    scat_tri_mat = ax.scatter(mat_x, mat_y, s=150, alpha=1)
    scat_pre_loc = ax.scatter(press_location_c, press_location_r, s=150, alpha=1)
    return scat_tri_mat, scat_pre_loc


def setup_figures():
    # prepare the figure
    SA_II_limits = 2000
    fig = plt.figure(figsize=(8, 10), constrained_layout=True)
    gs = fig.add_gridspec(6, 5)
    f1_ax1 = fig.add_subplot(gs[:3, :3],
                             aspect='equal',
                             autoscale_on=False,
                             xlim=(0, 5), ylim=(0, 5))
    f1_ax1.set_title('GTac Bubbles')
    f1_ax1_scat_tri_mat, f1_ax1_scat_pre_loc = setup_scatter_ax2(f1_ax1)

    f1_ax2 = fig.add_subplot(gs[0, 3:5])
    f1_ax2.set_title('Shear Force Signals (uT)')
    f1_ax2.set_ylim([-SA_II_limits, SA_II_limits])
    f1_ax2_magx = f1_ax2.plot(np.zeros(window_length), label='SA-II x')[0]
    f1_ax2_magy = f1_ax2.plot(np.zeros(window_length), label='SA-II y')[0]
    # f4_ax3_magz = f4_ax2.plot(np.zeros(window_length), label='mag-z')[0]
    f1_ax2.legend(loc=0)

    f1_ax3 = fig.add_subplot(gs[1, 3:5])
    f1_ax3.set_title('Normal Force Signals')
    f1_ax3.set_ylim([0, 2000])
    f1_ax3_mat_sum = f1_ax3.plot(np.zeros(window_length),
                                 label='FA-I Sum')[0]
    f1_ax3_magz = f1_ax3.plot(np.zeros(window_length), label='SA-II z')[0]
    # f1_ax3_mag_z = f4_ax3.plot(np.zeros(window_length),
    #                              label='mag-z')[0]
    f1_ax3.legend(loc=0)

    f1_ax4 = fig.add_subplot(gs[2, 3:5])
    f1_ax4.set_title('Normal Force Center')
    f1_ax4.set_ylim([0, 4])
    f1_ax4_center_x = f1_ax4.plot(np.zeros(window_length), label='x')[0]
    f1_ax4_center_y = f1_ax4.plot(np.zeros(window_length), label='y')[0]
    f1_ax4.legend()

    # finger two
    f2_ax1 = fig.add_subplot(gs[3:6, :3],
                             aspect='equal',
                             autoscale_on=False,
                             xlim=(0, 5), ylim=(0, 5))
    f2_ax1.set_title('GTac Bubbles')
    f2_ax1_scat_tri_mat, f2_ax1_scat_pre_loc = setup_scatter_ax2(f2_ax1)

    f2_ax2 = fig.add_subplot(gs[3, 3:5])
    f2_ax2.set_title('Shear Force Signals (uT)')
    f2_ax2.set_ylim([-SA_II_limits, SA_II_limits])
    f2_ax2_magx = f2_ax2.plot(np.zeros(window_length), label='SA-II x')[0]
    f2_ax2_magy = f2_ax2.plot(np.zeros(window_length), label='SA-II y')[0]
    # f2_ax3_magz = f2_ax2.plot(np.zeros(window_length), label='mag-z')[0]
    f2_ax2.legend(loc=0)

    f2_ax3 = fig.add_subplot(gs[4, 3:5])
    f2_ax3.set_title('Normal Force Signals')
    f2_ax3.set_ylim([0, 2000])
    f2_ax3_mat_sum = f2_ax3.plot(np.zeros(window_length),
                                 label='FA-I Sum')[0]
    f2_ax3_magz = f2_ax3.plot(np.zeros(window_length), label='SA-II z')[0]
    # f1_ax3_mag_z = f2_ax3.plot(np.zeros(window_length),
    #                              label='mag-z')[0]
    f2_ax3.legend(loc=0)

    f2_ax4 = fig.add_subplot(gs[5, 3:5])
    f2_ax4.set_title('Normal Force Center')
    f2_ax4.set_ylim([0, 4])
    f2_ax4_center_x = f2_ax4.plot(np.zeros(window_length), label='x')[0]
    f2_ax4_center_y = f2_ax4.plot(np.zeros(window_length), label='y')[0]
    f2_ax4.legend()

    # fig1 = plt.figure()
    # f1_ax1_gaussian = fig1.add_subplot(111, projection='3d')
    # f1_ax1_gaussian.set_title('GTac Super-Resotion')
    # f1_ax1_gaussian_plot = [f1_ax1_gaussian.plot_surface(x_mesh, y_mesh, zarray[:, :], color='0.75', rstride=1, cstride=1)]

    return fig, f1_ax1_scat_tri_mat, f1_ax1_scat_pre_loc, \
           f1_ax2_magx, f1_ax2_magy, f1_ax3_magz, \
           f1_ax3_mat_sum, f1_ax4_center_x, f1_ax4_center_y, f2_ax1_scat_tri_mat, f2_ax1_scat_pre_loc, \
           f2_ax2_magx, f2_ax2_magy, f2_ax3_magz, \
           f2_ax3_mat_sum, f2_ax4_center_x, f2_ax4_center_y


def animate2(i):
    print('{}/{}'.format(i, frames_num))
    # global TO_MOVE, TO_RELEASE, pinch, time_thumb_fle, last_time_12, last_time_12_inv
    start_in = time.time()
    if LIVE:
        data = raw_data_byts_checkout_2(ser, verbose=False)
        ms = int(round((time.time() - start) * 1000))
        data.append(ms)
        data_frame_array = data - avg  # average by the initial data
        print('preprocessed data_frame_array: {}'.format(data_frame_array))
    else:
        data = data_pd.iloc[i, :]
        data = list(data)
        data_frame_array = data

    print('data length: {}; data: {} '.format(len(data), data))

    to_return = []
    for f_ind, f in enumerate(finger_to_plot):
        # for s_ind, s in enumerate(sec_to_plot):
        ind = f
        print('figure index to open: ind {}'.format(ind))
        # update_vals(data_frame_array, finger=f, sec=0, window_len=window_length)
        # set_data_sec(ax1_scat_tri_mat_list[ind],
        #              ax1_scat_pre_loc_list[ind],
        #              ax2_magx_list[ind],
        #              ax2_magy_list[ind],
        #              ax2_magz_list[ind],
        #              ax3_mat_sum_list[ind],
        #              ax4_center_x_list[ind],
        #              ax4_center_y_list[ind])

        update_vals_finger_wise(data_frame_array, finger=f, sec=0, window_len=window_length)
        set_data_sec_finger_wise(ax1_scat_tri_mat_list[ind],
                     ax1_scat_pre_loc_list[ind],
                     ax2_magx_list[ind],
                     ax2_magy_list[ind],
                     ax2_magz_list[ind],
                     ax3_mat_sum_list[ind],
                     ax4_center_x_list[ind],
                     ax4_center_y_list[ind],
                                 finger=f)

        to_return.append(ax1_scat_tri_mat_list[ind])
        to_return.append(ax1_scat_pre_loc_list[ind])
        to_return.append(ax2_magx_list[ind])
        to_return.append(ax2_magy_list[ind])
        to_return.append(ax2_magz_list[ind])
        to_return.append(ax3_mat_sum_list[ind])
        to_return.append(ax4_center_x_list[ind])
        to_return.append(ax4_center_y_list[ind])
        print('returning {} axes instances'.format(len(to_return)))

    # control the fingers to grasp
    # pinch,time_thumb_fle,last_time_12,last_time_12_inv = reactive_pinch(data_frame_array,ser,
    #                pinch,time_thumb_fle,last_time_12,last_time_12_inv)
    # mat_sum_sec = find_mat_sum_sec(data_frame_array,
    #                                mat_th=50,
    #                                verbose=False)
    # if mat_sum_sec[2, 0] > 50 and not pinch:
    #     pinch = True
    # # creat current time stamp
    # time_ctrl = time.time()
    # if pinch and mat_sum_sec[0, 2] < 300 and time_ctrl - time_thumb_fle > 0.05:
    #     ser.write(b'<21>')
    #     time_thumb_fle = time_ctrl
    #
    # if pinch and mat_sum_sec[1, 0] < 600 and time_ctrl - last_time_12 > 0.1:
    #     ser.write(b'<41>')
    #     ser.write(b'<1-1>')
    #     # ser.write(b'<31>')
    #     # ser.write(b'<51>')
    #     # ser.write(b'<61>')
    #     last_time_12 = time_ctrl
    #
    # if pinch and mat_sum_sec[1, 0] > 800 and time_ctrl - last_time_12_inv > 0.1:
    #     ser.write(b'<4-1>')
    #     ser.write(b'<2-1>')
    #     ser.write(b'<11>')
    #     # ser.write(b'<3-1>')
    #     # ser.write(b'<5-1>')
    #     # ser.write(b'<6-1>')
    #     last_time_12_inv = time_ctrl
    # if time.time() - start > 5 and TO_MOVE:
    #     ser.write(b'<220>')
    #     ser.write(b'<450>')
    #     TO_MOVE = False
    #     TO_RELEASE = True
    # if time.time() - start > 15 and TO_RELEASE:
    #     ser.write(b'<>')
    #     TO_RELEASE = False
    print('frames {}, time {}ms'.format(i, round((time.time() - start_in) * 1000)))
    print('returned {} axes instances'.format(len(to_return)))
    return to_return


def collect_Data_to_init(ser, DataPoints, starttime):
    # collect data to initialize signals
    dt_list = []
    i = 0
    while (i < DataPoints):
        data = raw_data_byts_checkout_2(ser, verbose=False)
        ms = int(round((time.time() - starttime) * 1000))
        data.append(ms)
        # data = gtac_data.preprocess_(data)
        dt_list.append(data)
        i = i + 1
    return dt_list[-100:]


if __name__ == '__main__':
    # current time
    # sudo chmod 666 /dev/ttyACM0
    timestr = time.strftime("%Y%m%d_%H%M%S")
    # parse the argumments
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--serialport", default='/dev/ttyACM1',
                        help="set serial port (default: COM6)")  # ubuntu: /dev/ttyACM0
    parser.add_argument("-f", "--finger", default=0, type=int,
                        help="set the finger to visualize")
    parser.add_argument("-s", "--section", default=0, type=int,
                        help="set the section to visualize")
    parser.add_argument("-l", "--LIVE", default=0, type=int,
                        help="LIVE or generate video")
    # Read arguments from command line
    args = parser.parse_args()
    SerialPort, finger, sec, LIVE = args.serialport, \
                              args.finger, \
                              args.section, args.LIVE
    # creat a pandas DataFrame to store the data
    df_RAW = pd.DataFrame(columns=COLUMNS_RAW_FINGER_DATA)
    dt_list = []


    # init position
    # ser.write(b'<>')
    time.sleep(1)
    # ser.write(b'<150>')

    # print(finger)
    # print(sec)
    finger_to_plot = [0, 1]  # there are only two fingers in gp2
    sec_to_plot = [sec]

    # for i, f in enumerate(finger_to_plot):
    #     for j, s in enumerate(sec_to_plot):
    # ind = i * 3 + j
    fig4, f1_ax1_scat_tri_mat, f1_ax1_scat_pre_loc, \
    f1_ax2_magx, f1_ax2_magy, f1_ax3_magz, \
    f1_ax3_mat_sum, f1_ax4_center_x, f1_ax4_center_y, f2_ax1_scat_tri_mat, f2_ax1_scat_pre_loc, \
    f2_ax2_magx, f2_ax2_magy, f2_ax3_magz, \
    f2_ax3_mat_sum, f2_ax4_center_x, f2_ax4_center_y = setup_figures()
    # axes for finger one
    ax1_scat_tri_mat_list[0] = f1_ax1_scat_tri_mat
    ax1_scat_pre_loc_list[0] = f1_ax1_scat_pre_loc
    ax2_magx_list[0] = f1_ax2_magx
    ax2_magy_list[0] = f1_ax2_magy
    ax2_magz_list[0] = f1_ax3_magz
    ax3_mat_sum_list[0] = f1_ax3_mat_sum
    ax4_center_x_list[0] = f1_ax4_center_x
    ax4_center_y_list[0] = f1_ax4_center_y
    # axes for finger two
    ax1_scat_tri_mat_list[1] = f2_ax1_scat_tri_mat
    ax1_scat_pre_loc_list[1] = f2_ax1_scat_pre_loc
    ax2_magx_list[1] = f2_ax2_magx
    ax2_magy_list[1] = f2_ax2_magy
    ax2_magz_list[1] = f2_ax3_magz
    ax3_mat_sum_list[1] = f2_ax3_mat_sum
    ax4_center_x_list[1] = f2_ax4_center_x
    ax4_center_y_list[1] = f2_ax4_center_y
    # styles = ['r-', 'g-', 'y-', 'm-', 'k-', 'c-']
    # styles = ['r-', 'g-']
    # lines = [plot(ax, style) for ax, style in zip(axes, styles)]
    # line = axes[0].plot(mag_x, mag_y,animated=True)
    # fig = plt.figure()
    # line = plt.plot(mag_x,mag_y)
    start = time.time()
    TO_MOVE = True
    TO_RELEASE = True
    pinch = False
    time_thumb_fle = 0
    last_time_12 = 0
    last_time_12_inv = 0
    n = 0
    # LIVE = True

    # print('{}/{}'.format(n, DataPoints))
    # collect init values for average

    # exp_name_list = ['egg_grasp_0', 'egg_grasp_1', 'egg_grasp_2']
    # exp_name_list = ['0_gp_2f_clamp_shaft', '1_gp_2f_clamp_shaft', '2_gp_2f_clamp_shaft', '3_gp_2f_clamp_shaft']
    exp_name_list = ['4_gp_2f_cup']
    for exp_name in exp_name_list:
        # collect init values for average
        # exp_name = 'egg_grasp_0'
        filename_1 = 'data/Gripper_two_fingered/' + exp_name + '.csv'
        video_save_path = 'data/Gripper_two_fingered/'
        if not LIVE:
            data_pd = pd.read_csv(filename_1, index_col=0, skiprows=0)
            frames_num = len(data_pd)
            blit = False
        else:
            ser = serial.Serial(SerialPort, 115200)
            time.sleep(0.5)
            if ser.is_open:
                print('Serial Port Opened:\n', ser)
                ser.flushInput()
            init_values = collect_Data_to_init(ser, DataPoints=300, starttime=start)
            avg = np.array(init_values).mean(axis=0, dtype=int)
            frames_num = 2
            blit = True
        ani = FuncAnimation(fig4, animate2,
                            frames=frames_num,
                            interval=4.03, blit=blit)
        # init position
        # ser.write(b'<>')
        # plt.tight_layout()

        if not LIVE:
            # ani.save('ani_test.gif', writer='pillow')
            # ani.save("TLI.gif", dpi=300, writer=PillowWriter(fps=25))
            # ani.save(filename_1, fps=30, extra_args=['-vcodec', 'libx264'])
            # writervideo = animation.FFMpegWriter(fps=60)
            # ani.save('ani_test.mp4', writer=writervideo)
            ani.save(video_save_path + exp_name + '_GTac_window600.mp4')
        else:
            plt.show()
            ser.close()
