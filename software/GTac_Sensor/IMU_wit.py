# source: IMU wit
# coding:UTF-8
# 运行前需先安装pyserial，用WIN+R调出运行框，输入CMD，进入命令行，输入pip install pyserial更新一下函数库
import time
import pandas as pd
import serial
import numpy as np
from matplotlib import pyplot as plt

ACCData = [0.0] * 8
GYROData = [0.0] * 8
AngleData = [0.0] * 8
FrameState = 0  # 通过0x后面的值判断属于哪一种情况
Bytenum = 0  # 读取到这一段的第几位
CheckSum = 0  # 求和校验位

a = [0.0] * 3
w = [0.0] * 3
Angle = [0.0] * 3

COLUMNS_RAW_IMU = ['acc_x', 'acc_y', 'acc_z',
                   'gyro_x', 'gyro_y', 'gyro_z',
                   'angle_x', 'angle_y', 'angle_z',
                   'mag_x', 'mag_y', 'mag_z', 'ms']
data_type = ['acc', 'gyro', 'angle', 'mag']

def DueData(inputdata):  # 新增的核心程序，对读取的数据进行划分，各自读到对应的数组里
    global FrameState  # 在局部修改全局变量，要进行global的定义
    global Bytenum
    global CheckSum
    global a
    global w
    global Angle
    for data in inputdata:  # 在输入的数据进行遍历
        # Python2软件版本这里需要插入 data = ord(data)*****************************************************************************************************
        data_hh = hex(data)
        if FrameState == 0:  # 当未确定状态的时候，进入以下判断
            if data == 0x55 and Bytenum == 0:  # 0x55位于第一位时候，开始读取数据，增大bytenum
                CheckSum = data
                Bytenum = 1
                continue
            elif data == 0x51 and Bytenum == 1:  # 在byte不为0 且 识别到 0x51 的时候，改变frame
                CheckSum += data
                FrameState = 1
                Bytenum = 2
            elif data == 0x52 and Bytenum == 1:  # 同理
                CheckSum += data
                FrameState = 2
                Bytenum = 2
            elif data == 0x53 and Bytenum == 1:
                CheckSum += data
                FrameState = 3
                Bytenum = 2
        elif FrameState == 1:  # acc    #已确定数据代表加速度

            if Bytenum < 10:  # 读取8个数据
                ACCData[Bytenum - 2] = data  # 从0开始
                CheckSum += data
                Bytenum += 1
            else:
                if data == (CheckSum & 0xff):  # 假如校验位正确
                    a = get_acc(ACCData)
                CheckSum = 0  # 各数据归零，进行新的循环判断
                Bytenum = 0
                FrameState = 0
        elif FrameState == 2:  # gyro

            if Bytenum < 10:
                GYROData[Bytenum - 2] = data
                CheckSum += data
                Bytenum += 1
            else:
                if data == (CheckSum & 0xff):
                    w = get_gyro(GYROData)
                CheckSum = 0
                Bytenum = 0
                FrameState = 0
        elif FrameState == 3:  # angle

            if Bytenum < 10:
                AngleData[Bytenum - 2] = data
                CheckSum += data
                Bytenum += 1
            else:
                if data == (CheckSum & 0xff):
                    Angle = get_angle(AngleData)
                    d = a + w + Angle
                    print("a(g):%10.3f %10.3f %10.3f w(deg/s):%10.3f %10.3f %10.3f Angle(deg):%10.3f %10.3f %10.3f" % d)
                CheckSum = 0
                Bytenum = 0
                FrameState = 0


def get_acc(datahex):
    axl = datahex[0]
    axh = datahex[1]
    ayl = datahex[2]
    ayh = datahex[3]
    azl = datahex[4]
    azh = datahex[5]

    k_acc = 16.0

    acc_x = (axh << 8 | axl) / 32768.0 * k_acc
    acc_y = (ayh << 8 | ayl) / 32768.0 * k_acc
    acc_z = (azh << 8 | azl) / 32768.0 * k_acc
    if acc_x >= k_acc:
        acc_x -= 2 * k_acc
    if acc_y >= k_acc:
        acc_y -= 2 * k_acc
    if acc_z >= k_acc:
        acc_z -= 2 * k_acc

    return acc_x, acc_y, acc_z


def get_gyro(datahex):
    wxl = datahex[0]
    wxh = datahex[1]
    wyl = datahex[2]
    wyh = datahex[3]
    wzl = datahex[4]
    wzh = datahex[5]
    k_gyro = 2000.0

    gyro_x = (wxh << 8 | wxl) / 32768.0 * k_gyro
    gyro_y = (wyh << 8 | wyl) / 32768.0 * k_gyro
    gyro_z = (wzh << 8 | wzl) / 32768.0 * k_gyro
    if gyro_x >= k_gyro:
        gyro_x -= 2 * k_gyro
    if gyro_y >= k_gyro:
        gyro_y -= 2 * k_gyro
    if gyro_z >= k_gyro:
        gyro_z -= 2 * k_gyro
    return gyro_x, gyro_y, gyro_z


def get_angle(datahex):
    rxl = datahex[0]
    rxh = datahex[1]
    ryl = datahex[2]
    ryh = datahex[3]
    rzl = datahex[4]
    rzh = datahex[5]
    k_angle = 180.0

    angle_x = (rxh << 8 | rxl) / 32768.0 * k_angle
    angle_y = (ryh << 8 | ryl) / 32768.0 * k_angle
    angle_z = (rzh << 8 | rzl) / 32768.0 * k_angle
    if angle_x >= k_angle:
        angle_x -= 2 * k_angle
    if angle_y >= k_angle:
        angle_y -= 2 * k_angle
    if angle_z >= k_angle:
        angle_z -= 2 * k_angle

    return angle_x, angle_y, angle_z


def get_mag(datahex):
    mxl = datahex[0]
    mxh = datahex[1]
    myl = datahex[2]
    myh = datahex[3]
    mzl = datahex[4]
    mzh = datahex[5]

    mag_x = (mxh << 8 | mxl)
    mag_y = (myh << 8 | myl)
    mag_z = (mzh << 8 | mzl)
    return mag_x, mag_y, mag_z


def get_all_imu(data_40):
    data_type_head = [0x51, 0x52, 0x53, 0x54]
    data_all_ = {}
    index_dt = [8, 16, 24, 32]
    for i, h in enumerate(data_type_head):
        index = index_dt[i] + 1
        dt = data_type[i]
        if dt == 'acc':
            data = get_acc(data_40[index + 1:index + 7])
            data = [round(i, 2) for i in data]
        if dt == 'gyro':
            data = get_gyro(data_40[index + 1:index + 7])
            data = [round(i, 2) for i in data]
        if dt == 'angle':
            data = get_angle(data_40[index + 1:index + 7])
            data = [round(i, 2) for i in data]
        if dt == 'mag':
            data = get_mag(data_40[index + 1:index + 7])
            data = [round(i, 2) for i in data]
        data_all_[dt] = data
    print(data_all_)
    return data_all_


def read_imu(ser, verbose=False):
    datahex = ser.read(40)
    ser.flushInput()
    if verbose:
        datahex_ = [hex(i) for i in datahex]
        print(datahex_)
    check_head = [i for i, x in enumerate(datahex) if x == 0x55]
    if all(i in check_head for i in [0, 8, 16, 24, 32]):
        return datahex


def imu_to_list(data_dict):
    data_list = []
    for k, v in data_dict.items():
        for d in v:
            data_list.append(d)
    return data_list

def plot_all_imu(data_imu,filename=' ',cycle_start=None,cycle_end=None):
    fig_SA_II, axs_SA_II = plt.subplots(2, 3,
                                        sharex=True,
                                        sharey=False,
                                        constrained_layout=True)
    fig_SA_II.suptitle('IMU' \
                       + filename, fontsize=16)
    if isinstance(data_imu, pd.DataFrame):
        data_seq = data_imu.to_numpy()
    elif isinstance(data_imu, np.ndarray):
        data_seq = data_imu

    for i in range(3):
        index = 3 * i
        for d in range(3):
            plot_title = data_type[i]
            axs_SA_II[0, i].set_title(plot_title)
            axs_SA_II[0, i].plot(data_seq[:, index+d], label=COLUMNS_RAW_IMU[index+d])
            axs_SA_II[0, i].axhline(y=0, c='k')
            if cycle_start:
                axs_SA_II[0, i].axvline(x=cycle_start, c='r')
            if cycle_end:
                axs_SA_II[0, i].axvline(x=cycle_end, c='b')
        axs_SA_II[0, i].legend(loc=0)
    index = 9
    for d in range(3):
        plot_title = COLUMNS_RAW_IMU[index + d]
        axs_SA_II[1, d].set_title(plot_title)
        axs_SA_II[1, d].plot(data_seq[:, index + d], label=COLUMNS_RAW_IMU[index + d])
        axs_SA_II[1, d].legend(loc=0)
    # plt.show()

def main(data_points=1000, save=False, plot=False, verbose=False, remarks='test'):
    to_save_df = pd.DataFrame(columns=COLUMNS_RAW_IMU)
    i = 0
    timestr = time.strftime("%Y%m%d_%H%M%S")
    filename = save_path + remarks + '_' + \
               str(data_points) + '_IMU_' + \
               timestr + '.csv'
    start = time.time()
    while i < data_points:
        st = time.time()
        data = read_imu(ser, verbose=False)
        if data is not None:
            data_all = get_all_imu(data)
        data_list = imu_to_list(data_all)
        ms = int(round((time.time() - start) * 1000))
        data_list.append(ms)
        to_save_df.loc[len(to_save_df)] = data_list

        if verbose:
            hz = round(1 / (time.time() - st))
            print('{}/{}: {} Hz'.format(i, data_points, hz))
        i += 1
    if save:
        to_save_df.to_csv(filename)
    if plot:
        plot_all_imu(to_save_df, filename)
        plt.show()

if __name__ == '__main__':
    # use raw_input function for python 2.x or input function for python3.x
    port = '/dev/ttyUSB0'  # port = input('please input port No. such as com7:'));
    baud = 230400
    ser = serial.Serial(port, baud, timeout=0.5)  # ser = serial.Serial('com7',115200, timeout=0.5)
    save_path = 'data/mag_interference_rotation_general/'
    if ser.is_open:
        print('Serial Port Opened:\n', ser)
        # ser.flushInput()
    main(data_points=2000, save=True, verbose=True, plot=True, remarks='00-set')
    # DueData(datahex)
