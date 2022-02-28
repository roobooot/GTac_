# Visualization of GTac-Hand offline
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 14:13:15 2020
Draw bubbles offline
@author: Zeyu
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
from matplotlib.animation import FuncAnimation
from matplotlib import style
import numpy as np
from data_gen import data_checkout,raw_data_checkout
import serial
import time
from queue import Queue
import threading
# from celluloid import Camera
from data_collect_fingers import pre_process, FINGER, SECTION
from data_collect_fingers_five import pre_process_five

# def rotate90Clockwise(A): 
#     N = len(A[0]) 
#     for i in range(N // 2): 
#         for j in range(i, N - i - 1): 
#             temp = A[i][j] 
#             A[i][j] = A[N - 1 - j][i] 
#             A[N - 1 - j][i] = A[N - 1 - i][N - 1 - j] 
#             A[N - 1 - i][N - 1 - j] = A[j][N - 1 - i] 
#             A[j][N - 1 - i] = temp
#     return A

mat_x = [4,4,4,4,3,3,3,3,2,2,2,2,1,1,1,1]
mat_y = [1,2,3,4,1,2,3,4,1,2,3,4,1,2,3,4]

mat_xy = np.zeros([16,2])

mat_x_0 = [4,4,4,4,3,3,3,3,2,2,2,2,1,1,1,1]
mat_y_0 = [1,2,3,4,1,2,3,4,1,2,3,4,1,2,3,4]

mat_amp_index = 10
mat_loc_index = 0.001
    
mat_sz = np.zeros(16)
mag_dt = np.zeros(3)


data_length = 34



q = Queue(maxsize=34)


def plot_fingertip(ax):
    ax.cla()
    # plt.scatter(tri_cent_x, tri_cent_y, s=tri_cent_outsider_sz, alpha=0.4)
    ax.scatter(mat_x_0, mat_y_0, s=1500, alpha=0.4)
    # plt.scatter(mat_x, mat_y, s=500, alpha=1)
    ax.scatter(mat_x, mat_y, s=mat_sz, alpha=0.3)

def plot_fingertip_2(scat,mat_x,mat_y,mat_sz):
    # ax.scatter(mat_x_0, mat_y_0, s=1500, alpha=0.4)
    # ax.scatter(mat_x, mat_y, s=mat_sz, alpha=0.3)
    scat.set_offsets(np.array([mat_x,mat_y]).T)
    scat.set_sizes(mat_sz)


def animate_quick(i):

    start = time.time()
    data_frame = data_fingertip.iloc[i]
    update_paras_one_block(data_frame)

    # tri_cent_x = 2.5 + (mag_dt[0]-tri_x_0)*0.005
    # tri_cent_y = 2.5 + (mag_dt[1]-tri_y_0)*0.005
    # tri_cent_outsider_sz = 1500+(mag_dt[2]-tri_z_0)*-2

    # plot_fingertip(ax1)
    plot_fingertip_2(scat1,mat_x,mat_y,mat_sz)
    # plot_fingertip(ax2)
    # plot_fingertip(ax3)
    print('frames {}, time {}'.format(i,round((time.time() - start) * 1000)))


# def update_paras_twofinger(data):
#
#     col = data.col
#
#     if col in [8,9,10,11]:
#         col = col - 8 # to make it 0 1 2 3
#         row1 = data.mat5
#         row2 = data.mat6
#         row3 = data.mat7
#         row4 = data.mat8
#
#         mat_sz[4*col+3] = row1 * mat_amp_index
#         mat_sz[4*col+2] = row2 * mat_amp_index
#         mat_sz[4*col+1] = row3 * mat_amp_index
#         mat_sz[4*col+0] = row4 * mat_amp_index
#
#         mag_dt[0] = data.mag_x6
#         mag_dt[1] = data.mag_y6
#         mag_dt[2] = data.mag_z6
#         tri_x_0 = init_avg.mag_x6
#         tri_y_0 = init_avg.mag_y6
#
#         # update the matrix location
#         mat_x[4*col+3] = 4-col + (mag_dt[0]-tri_x_0)*mat_loc_index
#         mat_x[4*col+2] = 4-col + (mag_dt[0]-tri_x_0)*mat_loc_index
#         mat_x[4*col+1] = 4-col + (mag_dt[0]-tri_x_0)*mat_loc_index
#         mat_x[4*col+0] = 4-col + (mag_dt[0]-tri_x_0)*mat_loc_index
#
#         mat_y[4*col+3] = 4 + (mag_dt[1]-tri_y_0)*mat_loc_index
#         mat_y[4*col+2] = 3 + (mag_dt[1]-tri_y_0)*mat_loc_index
#         mat_y[4*col+1] = 2 + (mag_dt[1]-tri_y_0)*mat_loc_index
#         mat_y[4*col+0] = 1 + (mag_dt[1]-tri_y_0)*mat_loc_index
#
#         print('data updated')

def update_paras_one_block(assigned_data_frame):
    for i in range(16):
        mat_sz[i] = int(assigned_data_frame.iloc[i+4] * mat_amp_index)
        col = 4 - i // 4
        row = i % 4 + 1
        mat_x[i] = col + assigned_data_frame.mag_x * mat_loc_index
        mat_y[i] = row + assigned_data_frame.mag_y * mat_loc_index


def setup_scatter_ax(ax):
    # rect is the box edge
    rect = plt.Rectangle((-1,-1),
                         5,
                         5,
                         ec='none', lw=2, fc='none')
    ax.add_patch(rect)
    ax.axes.xaxis.set_visible(False)
    ax.axes.yaxis.set_visible(False)
    scat_base = ax.scatter(mat_x_0, mat_y_0, s=1500, alpha=0.4)
    scat = ax.scatter(mat_x, mat_y, s=150, alpha=1)
    return scat
# def init():
#     update_paras(np.zeros(data_length))

# def read_data(ser):
#     while True:
#         try:
#             data = raw_data_checkout(ser)
#             print('data:{}'.format(data)) # print what data read-out
#             print('length:{}'.format(len(data)))
#             if data:
#                 print('data:{}'.format(data)) # print what data read-out
#                 print('length:{}'.format(len(data)))
#                 if len(data)!=data_length:
#                     raise Exception('Sorry, wrong data size')
#         except:
#             print('data reading out is wrong')
#
#         # if len(data)==data_length and data[col_index//4] in ['0','1','2','3']: # check if the data follows the right form.
#         if len(data)==data_length: # check if the data follows the right form.
#             update_paras_twofinger(data)
# def draw_fingertip(fig):
#     ani = FuncAnimation(fig, animate_quick, frames=1000, interval=2)
#     # plt.tight_layout()
#     # ani.save('finger_rolling.gif', writer='pillow')
#     plt.show()
def find_init(data_seq, n):
    # average the n head data point of data_seq
    sum = data_seq.iloc[0]
    for i in range(1,n):
        sum = sum + data_seq.iloc[i]
    avg = (sum/n).astype('int64')
    return avg

def celluloid_draw(data_seq):
    return data_seq

def make_fingertip_video(finger,section):

    video_name = 'video/' + finger+ '_' + section + '.mp4'
    print('Start to save sensor video: {} of {}'.format(finger,section))
    ani = FuncAnimation(fig, animate_quick, frames=len(data_fingertip), interval=120)

    # ani.save('finger_rolling.gif', writer='pillow')
    ani.save(video_name, writer='ffmpeg')
    # plt.show()
    print('Saved: {}'.format(video_name))

if __name__ == '__main__':
    # try:
    #     ser = serial.Serial('COM12', 115200,timeout=.01)
    # except:
    #     print('Serial Connection Failed, Will Try Again in 3 SECONDS')
    #     time.sleep(3)
    # else:
    #     if ser.is_open:
    #         print('Serial Port Opened:\n',ser)
    #         ser.flushInput()
    #         time.sleep(1)
        # thread1 = threading.Thread(target=read_data,args=(ser,))
        # thread1.start()
        print('starting to draw data from sensors')
        data_seq = pd.read_csv('data/Achieved/test_five_2000_points_20210518_103354.csv', index_col=0)
        # init_avg = find_init(data_seq, 100)
        data_assigned = pre_process_five(data_seq)

        data_thumb_dis = (data_assigned.loc[(data_assigned.finger == 'THUMB') & (data_assigned.section == 'DISTAL')]).reset_index()
        data_index_dis = (data_assigned.loc[(data_assigned.finger == 'INDEX') & (data_assigned.section == 'DISTAL')]).reset_index()
        data_thumb_pro = (data_assigned.loc[(data_assigned.finger == 'THUMB') & (data_assigned.section == 'PROXIMAL')]).reset_index()
        data_index_pro = (data_assigned.loc[(data_assigned.finger == 'INDEX') & (data_assigned.section == 'PROXIMAL')]).reset_index()
        data_thumb_met = (data_assigned.loc[(data_assigned.finger == 'THUMB') & (data_assigned.section == 'METACARPAL')]).reset_index()
        data_index_met = (data_assigned.loc[(data_assigned.finger == 'INDEX') & (data_assigned.section == 'METACARPAL')]).reset_index()

        for finger in FINGER:
            for section in SECTION:
                data_fingertip = (data_assigned.loc[(data_assigned.finger == finger) & (data_assigned.section == section)]).reset_index()
                fig = plt.figure()
                # fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
                ax1 = fig.add_subplot(111, aspect='equal', autoscale_on=False,
                                      xlim=(0, 5), ylim=(0, 5))
                scat1 = setup_scatter_ax(ax1)
                #
                # ax2 = fig.add_subplot(312, aspect='equal', autoscale_on=False,
                #                      xlim=(-5, 5), ylim=(-5, 5))
                # ax2 = setup_ax(ax2)
                #
                # ax3 = fig.add_subplot(313, aspect='equal', autoscale_on=False,
                #                      xlim=(-5, 5), ylim=(-5, 5))
                # ax3 = setup_ax(ax3)

                make_fingertip_video(finger, section)
# data_index = (data_assigned.loc[data_assigned.finger == 'INDEX']).reset_index()

        # data_thumb_dis.plot.line(x='milliseconds', y='mag_x')

        # fig = plt.figure()
        # # fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        # ax1 = fig.add_subplot(111, aspect='equal', autoscale_on=False,
        #                       xlim=(0, 5), ylim=(0, 5))
        # scat1 = setup_ax(ax1)
        # #
        # # ax2 = fig.add_subplot(312, aspect='equal', autoscale_on=False,
        # #                      xlim=(-5, 5), ylim=(-5, 5))
        # # ax2 = setup_ax(ax2)
        # #
        # # ax3 = fig.add_subplot(313, aspect='equal', autoscale_on=False,
        # #                      xlim=(-5, 5), ylim=(-5, 5))
        # # ax3 = setup_ax(ax3)
        #
        # ani = FuncAnimation(fig, animate_quick, frames=150, interval=10)
        #
        # # ani.save('finger_rolling.gif', writer='pillow')
        # ani.save('./video/index_pro.mp4', writer='ffmpeg')
        # plt.show()