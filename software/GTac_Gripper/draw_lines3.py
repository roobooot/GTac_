import copy

from GTac_Data import gtac_data
from data_gen import raw_data_byts_checkout_2, collect_DataPoints
# from data_collect_fingers_five import COLUMNS_RAW_FINGER_DATA, MAG_NUM, COL_INDEX
from gtac_config import COLUMNS_RAW_FINGER_DATA, MAG_NUM, COL_INDEX
# from Handover import collect_DataPoints, find_location, find_mat_value
# from Stably_Gentle_Grasping import find_mat_sum_sec, reactive_pinch
from draw_bubbles_py_3 import setup_scatter_ax, plot_fingertip_2
# from draw_lines2 import update_vals
import serial
import time
import pandas as pd
import numpy as np
import argparse
import matplotlib
# matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
# from GTac_Hand import gtac_hand

window_length = 200
x = np.linspace(0, 199, 200)
y = np.zeros(len(x))
mag_x = []
mag_y = []
mag_z = []

mat_x_0 = [4, 4, 4, 4, 3, 3, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1]
mat_y_0 = [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4]

mat_x = [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4]
mat_y = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4]

press_location_r = 2.5
press_location_r_list = []
press_location_c = 2.5
press_location_c_list = []
sum_value = 0
sum_value_list = []

mat_sz = np.zeros(16)
mat_amp_index = 10
pressing_loc_amp_index = 2
mat_loc_index = 0.001



def update_vals(data_frame_array, finger=1, sec=2, window_len=200):
    tri_index = finger * 9 + (2 - sec) * 3
    sum_r = 0
    sum_c = 0
    global mag_x, mag_y, mag_z, sum_value, press_location_r, press_location_c, \
        sum_value_list, press_location_r_list, press_location_c_list
    sum_value = 0

    # update magnetic and resistive signals for GTac Bubbles
    for i in range(len(mat_x)):
        r = i // 4
        c = i % 4
        index, value = gtac_data.find_mat_value(data_frame_array, finger, sec, r, c)
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


# define normalized 2D gaussian
def gaus2d(x=0, y=0, mx=0, my=0, sx=1, sy=1):
    return 1. / (2. * np.pi * sx * sy) * np.exp(-((x - mx)**2. / (2. * sx**2.) + (y - my)**2. / (2. * sy**2.)))

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
    if len(mag_y) == window_length:
        # print(len(mag_x),len(mag_y),len(mag_z),len(sum_value_list),len(press_location_c_list),len(press_location_r_list))
        f4_ax2_magx.set_ydata(mag_x)
        f4_ax2_magy.set_ydata(mag_y)
        f4_ax3_magz.set_ydata(mag_z)
        f4_ax3_mat_sum.set_ydata(sum_value_list)
        f4_ax4_center_x.set_ydata(press_location_c_list)
        f4_ax4_center_y.set_ydata(press_location_r_list)


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
    fig4 = plt.figure(figsize=(9, 5), constrained_layout=True)
    gs = fig4.add_gridspec(3, 5)
    f4_ax1 = fig4.add_subplot(gs[:, :-2],
                              aspect='equal',
                              autoscale_on=False,
                              xlim=(0, 5), ylim=(0, 5))
    f4_ax1.set_title('GTac Bubbles')
    f4_ax1_scat_tri_mat, f4_ax1_scat_pre_loc = setup_scatter_ax2(f4_ax1)

    f4_ax2 = fig4.add_subplot(gs[0, -2:])
    f4_ax2.set_title('Shear Force Signals (uT)')
    f4_ax2.set_ylim([-500, 500])
    f4_ax2_magx = f4_ax2.plot(np.zeros(window_length), label='SA-II x')[0]
    f4_ax2_magy = f4_ax2.plot(np.zeros(window_length), label='SA-II y')[0]
    # f4_ax3_magz = f4_ax2.plot(np.zeros(window_length), label='mag-z')[0]
    f4_ax2.legend(loc=0)

    f4_ax3 = fig4.add_subplot(gs[1, -2:])
    f4_ax3.set_title('Normal Force Signals')
    f4_ax3.set_ylim([0, 2000])
    f4_ax3_mat_sum = f4_ax3.plot(np.zeros(window_length),
                                 label='FA-I Sum')[0]
    f4_ax3_magz = f4_ax3.plot(np.zeros(window_length), label='SA-II z')[0]
    # f4_ax3_mag_z = f4_ax3.plot(np.zeros(window_length),
    #                              label='mag-z')[0]
    f4_ax3.legend(loc=0)

    f4_ax4 = fig4.add_subplot(gs[2, -2:])
    f4_ax4.set_title('Normal Force Center')
    f4_ax4.set_ylim([0, 4])
    f4_ax4_center_x = f4_ax4.plot(np.zeros(window_length), label='x')[0]
    f4_ax4_center_y = f4_ax4.plot(np.zeros(window_length), label='y')[0]
    f4_ax4.legend()

    # fig1 = plt.figure()
    # f1_ax1_gaussian = fig1.add_subplot(111, projection='3d')
    # f1_ax1_gaussian.set_title('GTac Super-Resotion')
    # f1_ax1_gaussian_plot = [f1_ax1_gaussian.plot_surface(x_mesh, y_mesh, zarray[:, :], color='0.75', rstride=1, cstride=1)]

    return fig4, f4_ax1_scat_tri_mat, f4_ax1_scat_pre_loc, \
           f4_ax2_magx, f4_ax2_magy, f4_ax3_magz, \
           f4_ax3_mat_sum, f4_ax4_center_x, f4_ax4_center_y


def animate2(i):
    print(i)
    global TO_MOVE, TO_RELEASE, pinch, time_thumb_fle, last_time_12, last_time_12_inv
    start_in = time.time()
    data = raw_data_byts_checkout_2(ser, verbose=False)
    ms = int(round((time.time() - start) * 1000))
    data = np.append(data, ms)
    # data = gtac_data.preprocess_(data)
    # dt_list.append(data)
    data_frame_array = data - avg  # average by the initial data
    to_return = []
    for f_ind, f in enumerate(finger_to_plot):
        for s_ind, s in enumerate(sec_to_plot):
            update_vals(data_frame_array, finger=f, sec=s)
            ind = f_ind * len(sec_to_plot) + s_ind
            # print(ind)
            set_data_sec(ax1_scat_tri_mat_list[ind],
                         ax1_scat_pre_loc_list[ind],
                         ax2_magx_list[ind],
                         ax2_magy_list[ind],
                         ax2_magz_list[ind],
                         ax3_mat_sum_list[ind],
                         ax4_center_x_list[ind],
                         ax4_center_y_list[ind])
            to_return.append(ax1_scat_tri_mat_list[ind])
            to_return.append(ax1_scat_pre_loc_list[ind])
            to_return.append(ax2_magx_list[ind])
            to_return.append(ax2_magy_list[ind])
            to_return.append(ax2_magz_list[ind])
            to_return.append(ax3_mat_sum_list[ind])
            to_return.append(ax4_center_x_list[ind])
            to_return.append(ax4_center_y_list[ind])
    print('frames {}, time {}ms'.format(i, round((time.time() - start_in) * 1000)))
    return to_return


def animate_local(i):
    print(i)
    global TO_MOVE, TO_RELEASE, pinch, time_thumb_fle, last_time_12, last_time_12_inv
    start_in = time.time()
    # data = raw_data_byts_checkout_2(ser, verbose=False)
    data = data_pd.iloc[i, :]
    # ms = int(round((time.time() - start) * 1000))
    # data = np.append(data, ms)
    data = np.array(data)
    # data = gtac_data.preprocess_(data)
    # dt_list.append(data)
    print('data: {} '.format(data))
    data_frame_array = data  # average by the initial data
    to_return = []
    for f_ind, f in enumerate(finger_to_plot):
        for s_ind, s in enumerate(sec_to_plot):
            update_vals(data_frame_array, finger=f, sec=s)
            ind = f_ind * len(sec_to_plot) + s_ind
            # print(ind)
            set_data_sec(ax1_scat_tri_mat_list[ind],
                         ax1_scat_pre_loc_list[ind],
                         ax2_magx_list[ind],
                         ax2_magy_list[ind],
                         ax2_magz_list[ind],
                         ax3_mat_sum_list[ind],
                         ax4_center_x_list[ind],
                         ax4_center_y_list[ind])
            to_return.append(ax1_scat_tri_mat_list[ind])
            to_return.append(ax1_scat_pre_loc_list[ind])
            to_return.append(ax2_magx_list[ind])
            to_return.append(ax2_magy_list[ind])
            to_return.append(ax2_magz_list[ind])
            to_return.append(ax3_mat_sum_list[ind])
            to_return.append(ax4_center_x_list[ind])
            to_return.append(ax4_center_y_list[ind])
    print('frames {}, time {}ms'.format(i, round((time.time() - start_in) * 1000)))
    return to_return

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
    parser.add_argument("-fn", "--filename", help="set filename to analyze")
    parser.add_argument("-l", "--local", default=0, type=int,
                        help="choose if load local data")
    # Read arguments from command line
    args = parser.parse_args()
    SerialPort, finger, sec, filename, local = args.serialport, \
                              args.finger, \
                              args.section, args.filename, args.local
    # creat a pandas DataFrame to store the data
    df_RAW = pd.DataFrame(columns=COLUMNS_RAW_FINGER_DATA)
    dt_list = []

    if local == 1:
        # read the local dataset
        data_pd = pd.read_csv(filename, index_col=0, skiprows=0)
        # data_pd = data_pd.iloc[-1000:, :]
        DataPoints = len(data_pd)
    else:
        # read in real-time
        DataPoints = 2
        ser = serial.Serial(SerialPort, 115200)
        time.sleep(0.5)
        if ser.is_open:
            print('Serial Port Opened:\n', ser)
            ser.flushInput()
        # init position
        # ser.write(b'<>')
        time.sleep(1)
        # ser.write(b'<150>')
        start = time.time()
        TO_MOVE = True
        TO_RELEASE = True
        pinch = False
        time_thumb_fle = 0
        last_time_12 = 0
        last_time_12_inv = 0
        n = 0
        init_values = collect_DataPoints(ser, DataPoints=300, starttime=start)
        avg = np.array(init_values).mean(axis=0, dtype=int)

    finger_to_plot = [finger]
    sec_to_plot = [sec]
    fig_list = {}
    ax1_scat_tri_mat_list = {}
    ax1_scat_pre_loc_list = {}
    ax2_magx_list = {}
    ax2_magy_list = {}
    ax2_magz_list = {}
    ax3_mat_sum_list = {}
    ax4_center_x_list = {}
    ax4_center_y_list = {}
    for i, f in enumerate(finger_to_plot):
        for j, s in enumerate(sec_to_plot):
            ind = i * len(sec_to_plot) + j
            fig4, f4_ax1_scat_tri_mat, f4_ax1_scat_pre_loc, \
            f4_ax2_magx, f4_ax2_magy, f4_ax3_magz, \
            f4_ax3_mat_sum, f4_ax4_center_x, f4_ax4_center_y = setup_figures()
            fig_list[ind] = fig4
            ax1_scat_tri_mat_list[ind] = f4_ax1_scat_tri_mat
            ax1_scat_pre_loc_list[ind] = f4_ax1_scat_pre_loc
            ax2_magx_list[ind] = f4_ax2_magx
            ax2_magy_list[ind] = f4_ax2_magy
            ax2_magz_list[ind] = f4_ax3_magz
            ax3_mat_sum_list[ind] = f4_ax3_mat_sum
            ax4_center_x_list[ind] = f4_ax4_center_x
            ax4_center_y_list[ind] = f4_ax4_center_y
    # styles = ['r-', 'g-', 'y-', 'm-', 'k-', 'c-']
    # styles = ['r-', 'g-']
    # lines = [plot(ax, style) for ax, style in zip(axes, styles)]
    # line = axes[0].plot(mag_x, mag_y,animated=True)
    # fig = plt.figure()
    # line = plt.plot(mag_x,mag_y)

    # print('{}/{}'.format(n, DataPoints))
    # collect init values for average

    # collect init values for average

    if local == 0:
        ani = FuncAnimation(fig_list[0], animate2,
                            frames=DataPoints,
                            interval=1, blit=True)
    else:
        ani = FuncAnimation(fig_list[0], animate_local,
                            frames=DataPoints,
                            interval=6.6, blit=True)
        ani.save('video/tranlate_box_f_' + str(finger) + '_s_' + str(sec) + '.mp4',
                 writer="ffmpeg")
    # init position
    # ser.write(b'<>')
    # plt.tight_layout()
    plt.show()
    ser.close()
