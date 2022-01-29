# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 14:13:15 2020

@author: Zeyu
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
from matplotlib import style
import numpy as np
from data_gen import data_checkout,raw_data_checkout
import serial
import time

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

mat_x_0 = [4,4,4,4,3,3,3,3,2,2,2,2,1,1,1,1]
mat_y_0 = [1,2,3,4,1,2,3,4,1,2,3,4,1,2,3,4]

mat_amp_index = 50
mat_loc_index = 0.001
    
mat_sz = np.zeros(16)
mag_dt = np.zeros(3)

tri_x_0 = -21
tri_y_0 = -53
tri_z_0 = 31
def animate(i):
    global ser
    try:
        data = data_checkout(ser,3)
        print('data:',data) # print what data read-out
    except:
        print('data reading out is wrong')
    
    mat_data = data[:4]
    mat_sz = [val*mat_amp_index for sublist in mat_data for val in sublist]
    
    tri_x = data[-1][0]
    tri_y = data[-1][1]
    tri_z = data[-1][2]
    temp = data[-1][3]
    
    tri_cent_x = 2.5 + (tri_x-tri_x_0)*0.005
    tri_cent_y = 2.5 + (tri_y-tri_y_0)*0.005
    tri_cent_outsider_sz = 1500+(tri_z-tri_z_0)*-2
    
    plt.cla()
    # plt.scatter(tri_cent_x, tri_cent_y, s=tri_cent_outsider_sz, alpha=0.4)
    plt.scatter(mat_x, mat_y, s=500, alpha=1)
    plt.scatter(mat_x, mat_y, s=mat_sz, alpha=0.3)
#     plt.tight_layout()

def animate_quick(i):
    global ser
    try:
        data = raw_data_checkout(ser)
        print('data:',data) # print what data read-out
        if len(data)!=9:
            raise Exception('Sorry, wrong data size')
    except:
        print('data reading out is wrong')
    
    if len(data)==9 and data[0] in ['0','1','2','3']: # check if the data follows the right form.
        update_paras(data)
    
    tri_cent_x = 2.5 + (mag_dt[0]-tri_x_0)*0.005
    tri_cent_y = 2.5 + (mag_dt[1]-tri_y_0)*0.005
    tri_cent_outsider_sz = 1500+(mag_dt[2]-tri_z_0)*-2
    
    plt.cla()
    # plt.scatter(tri_cent_x, tri_cent_y, s=tri_cent_outsider_sz, alpha=0.4)
    plt.scatter(mat_x_0, mat_y_0, s=1500, alpha=0.4)
    # plt.scatter(mat_x, mat_y, s=500, alpha=1)
    plt.scatter(mat_x, mat_y, s=mat_sz, alpha=0.3)

def update_paras(data):
    col = int(data[0])
    row1 = int(data[1])
    row2 = int(data[2])
    row3 = int(data[3])
    row4 = int(data[4])
    
    mat_sz[4*col+3] = row1 * mat_amp_index
    mat_sz[4*col+2] = row2 * mat_amp_index
    mat_sz[4*col+1] = row3 * mat_amp_index
    mat_sz[4*col+0] = row4 * mat_amp_index
    
    mag_dt[0] = int(data[5])
    mag_dt[1] = int(data[6])
    mag_dt[2] = int(data[7])
    # update the matrix location
    mat_x[4*col+3] = 4-col + (mag_dt[0]-tri_x_0)*mat_loc_index
    mat_x[4*col+2] = 4-col + (mag_dt[0]-tri_x_0)*mat_loc_index
    mat_x[4*col+1] = 4-col + (mag_dt[0]-tri_x_0)*mat_loc_index
    mat_x[4*col+0] = 4-col + (mag_dt[0]-tri_x_0)*mat_loc_index
    
    mat_y[4*col+3] = 4 + (mag_dt[1]-tri_y_0)*mat_loc_index
    mat_y[4*col+2] = 3 + (mag_dt[1]-tri_y_0)*mat_loc_index
    mat_y[4*col+1] = 2 + (mag_dt[1]-tri_y_0)*mat_loc_index
    mat_y[4*col+0] = 1 + (mag_dt[1]-tri_y_0)*mat_loc_index
    
    
if __name__ == '__main__':
    while(1):
        try:
            ser = serial.Serial('COM3', 115200)
        except:
            print('Serial Connection Failed, Will Try Again in 3 SECONDS')
            time.sleep(3)
        else:
            if ser.is_open:
                print('Serial Port Opened:\n',ser)
                ser.flushInput()
            fig = plt.figure()
            fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
            ax = fig.add_subplot(111, aspect='equal', autoscale_on=False,
                                 xlim=(-5, 5), ylim=(-5, 5))
            # rect is the box edge
            rect = plt.Rectangle((-1,-1),
                                 5,
                                 5,
                                 ec='none', lw=2, fc='none')
            ax.add_patch(rect)
            ax.axes.xaxis.set_visible(False)
            ax.axes.yaxis.set_visible(False)
            
            ani = FuncAnimation(fig, animate_quick, frames=1500, interval=2)
            # plt.tight_layout()
            # ani.save('finger_rolling.gif', writer='pillow')
            plt.show()
            ser.close()