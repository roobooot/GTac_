from data_gen import raw_data_byts_checkout_2
from data_collect_fingers_five import COLUMNS_RAW_FINGER_DATA, MAG_NUM, COL_INDEX
from Handover import collect_DataPoints, find_location, find_mat_value
from Stably_Gentle_Grasping import find_mat_sum_sec
from draw_bubbles_py_3 import setup_scatter_ax,plot_fingertip_2
import serial
import time
import pandas as pd
import numpy as np
import argparse
import matplotlib
# matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation

x_vals = []
x = np.linspace(0,199,200)
y = np.zeros(len(x))
y_vals = []

mat_x_0 = [4,4,4,4,3,3,3,3,2,2,2,2,1,1,1,1]
mat_y_0 = [1,2,3,4,1,2,3,4,1,2,3,4,1,2,3,4]

mat_x = [1,2,3,4,1,2,3,4,1,2,3,4,1,2,3,4]
mat_y = [1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4]

press_location_r = 2.5
press_location_c = 2.5
sum_value = 0

mat_sz = np.zeros(16)
mat_amp_index = 10
pressing_loc_amp_index = 2
mat_loc_index = 0.001


def update_vals(data_frame_array,window_len=200):
    finger = 0
    sec = 2
    sum_r = 0
    sum_c = 0

    global x_vals, y_vals, sum_value, press_location_r, press_location_c
    sum_value = 0
    x_vals.append(data_frame_array[-1])
    y_vals.append(data_frame_array[0])
    if len(x_vals)>window_len:
        x_vals = x_vals[-window_len:]
        y_vals = y_vals[-window_len:]
    for i in range(len(mat_x)):
        r = i//4
        c = i%4
        index, value = find_mat_value(data_frame_array,finger,sec,r,c)
        if value > 40: # threshold to remove noise for obtaining pressing location
            sum_r += (r+1)*value
            sum_c += (c+1)*value
            sum_value += value

        mat_sz[i] = abs(value * mat_amp_index)

        mat_x[i] = c+1 + data_frame_array[0] * mat_loc_index
        mat_y[i] = r+1 + data_frame_array[1] * mat_loc_index
    if sum_value != 0:
        press_location_r = round(sum_r/sum_value, 1)
        press_location_c = round(sum_c/sum_value, 1)
    print('r:{};c:{}'.format(press_location_r,press_location_c))

def plot_pressing_loc(scat, press_location_r, press_location_c, sec_sum):
    scat.set_offsets(np.array([press_location_c,press_location_r]))
    scat.set_sizes([sec_sum*pressing_loc_amp_index])

def animate(i):
    s = time.time()
    data = raw_data_byts_checkout_2(ser, verbose=False)
    ms = int(round((time.time() - start) * 1000))
    data.append(ms)
    # dt_list.append(data)
    data_frame_array = data - avg  # average by the initial data
    update_vals(data_frame_array)

    plt.cla()
    plt.plot(y_vals,label='channel-0')
    plt.legend()
    print('frames {}, time {}'.format(i,round((time.time() - s) * 1000)))

def animate2(i):
    s = time.time()
    data = raw_data_byts_checkout_2(ser, verbose=False)
    ms = int(round((time.time() - start) * 1000))
    data.append(ms)
    # dt_list.append(data)
    data_frame_array = data - avg  # average by the initial data
    update_vals(data_frame_array)

    # line.set_xdata(x_vals)
    if len(y_vals)==200:
        line1.set_data(x_vals,y_vals)
        # line1.set_xdata(x_vals)
        # line2.set_ydata(y_vals)
        line12.set_ydata(y_vals)
        line22.set_ydata(y_vals)
    plot_fingertip_2(scat_tri_mat, mat_x, mat_y, mat_sz)
    plot_pressing_loc(scat_pre_loc,
                      press_location_r,
                      press_location_c,
                      sum_value)
    # print(x_vals)
    # for j, line in enumerate(lines):
    #     line.set_xdata(x_vals)
        # line.set_ydata(y_vals)
    print('frames {}, time {}ms'.format(i,round((time.time() - s) * 1000)))
    return line1,line2,line12,line22,scat_tri_mat,scat_pre_loc

def plot(ax, style):
    return ax.plot(x, y, style, animated=True)[0]

def setup_scatter_ax2(ax):
    # rect is the box edge
    rect = plt.Rectangle((-1,-1),
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
    # init position
    ser.write(b'<>')
    time.sleep(0.2)

    # prepare the figure
    fig = plt.figure()
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)
    ax1.set_ylim([-1000,1000])
    ax2.set_ylim([-1000,1000])
    line1 = ax1.plot(x,y, label='channel 1')[0]
    line2 = ax1.plot(y, label='channel 2')[0]
    ax1.legend()
    ax2.legend()

    fig2 = plt.figure()
    ax12 = fig2.add_subplot(121)
    ax22 = fig2.add_subplot(122)
    ax12.set_ylim([-1000,1000])
    ax22.set_ylim([-1000,1000])
    line12 = ax12.plot(y)[0]
    line22 = ax22.plot(y)[0]

    fig3 = plt.figure()
    # fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax_tri = fig3.add_subplot(111, aspect='equal', autoscale_on=False,
                          xlim=(0, 5), ylim=(0, 5))
    # draw information for one section,
    # e.g., array normal force, shear force, pressing location
    scat_tri_mat, scat_pre_loc = setup_scatter_ax2(ax_tri)

    # styles = ['r-', 'g-', 'y-', 'm-', 'k-', 'c-']
    # styles = ['r-', 'g-']
    # lines = [plot(ax, style) for ax, style in zip(axes, styles)]
    # line = axes[0].plot(x_vals, y_vals,animated=True)
    # fig = plt.figure()
    # line = plt.plot(x_vals,y_vals)
    start = time.time()
    n = 0
    init_values = collect_DataPoints(ser, DataPoints=100, starttime=start)
    avg = np.array(init_values).mean(axis=0,dtype=int)

    print('{}/{}'.format(n, DataPoints))
    # collect init values for average


    ani = FuncAnimation(fig, animate2,
                        frames=DataPoints, interval=1,blit=True)
    # plt.tight_layout()

    plt.show()
    ser.close()