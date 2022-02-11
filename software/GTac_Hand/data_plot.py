# -*- coding: utf-8 -*-
"""
Created on Fri Dec  4 15:01:28 2020

@author: Zeyu
"""

import serial
import time
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
# sns.set_theme(style="ticks")

COL_ORDER_1 = ['mat_x1y4','mat_x2y4','mat_x3y4','mat_x4y4',
             'mat_x1y3','mat_x2y3','mat_x3y3','mat_x4y3',
             'mat_x1y2','mat_x2y2','mat_x3y2','mat_x4y2',
             'mat_x1y1','mat_x2y1','mat_x3y1','mat_x4y1']
COL_ORDER_2 = ['mat_x1y4','mat_x2y4','mat_x3y4','mat_x4y4',
             'mat_x1y3','mat_x2y3','mat_x3y3','mat_x4y3',
             'mat_x1y2','mat_x2y2','mat_x3y2','mat_x4y2',
             'mat_x1y1','mat_x2y1','mat_x3y1','mat_x4y1',
             'mag_x','mag_y','mag_z']

def melt_data_steps(filename):
    data = pd.read_csv(filename, index_col=0)
    # unpivot the matrix data into long data frame
    data_mat_melted = data.melt(id_vars=['motor_step'],
                                value_vars=data.columns[:16],
                                var_name='signal_type',
                                value_name='signal_reading')
    data_mag_melted = data.melt(id_vars=['motor_step'],
                            value_vars=['mag_x','mag_y','mag_z'],
                            var_name='signal_type',
                            value_name='signal_reading')
    data_mat_mag_melted = data.melt(id_vars=['motor_step'],
                        value_vars=data.columns[:19],
                        var_name='signal_type',
                        value_name='signal_reading')
    return data_mat_melted, data_mag_melted, data_mat_mag_melted

def melt_data_time(filename,rang=False):
    data = pd.read_csv(filename, index_col=0)
    if rang:
        data = data[rang[0]:rang[1]]
    # unpivot the matrix data into long data frame
    data_mat_melted = data.melt(id_vars=['milliseconds'],
                                value_vars=data.columns[:16],
                                var_name='signal_type',
                                value_name='signal_reading')
    data_mag_melted = data.melt(id_vars=['milliseconds'],
                            value_vars=['mag_x','mag_y','mag_z'],
                            var_name='signal_type',
                            value_name='signal_reading')
    data_mat_mag_melted = data.melt(id_vars=['milliseconds'],
                        value_vars=data.columns[:19],
                        var_name='signal_type',
                        value_name='signal_reading')
    return data_mat_melted, data_mag_melted, data_mat_mag_melted

def plot_mat(filename, save=False, show=True):
    # unpivot the matrix data into long data frame
    data_mat_melted, data_mag_melted, data_mat_mag_melted = melt_data_steps(filename)
    # matrix plot
    g = sns.lmplot(x="motor_step", y="signal_reading", col="signal_type", hue="signal_type", data=data_mat_melted,
               col_wrap=4, height=3, col_order=COL_ORDER_1, sharey=False,order=2,ci=90,palette="dark", fit_reg=True,
               scatter_kws={"s": 2, "alpha": 1})
    g.set(ylim=(data_mat_melted.signal_reading.min(),data_mat_melted.signal_reading.max()))
    if save:
        plt.savefig('fig/'+filename[:-4]+'_MAT.png')
    if show:
        plt.show()
        
    # magnetic plot
    g = sns.lmplot(x="motor_step", y="signal_reading", col="signal_type", hue="signal_type", data=data_mag_melted,
           col_wrap=3, ci=90, palette="dark", height=3, sharey=False,order=2,
           scatter_kws={"s": 2, "alpha": 1})
    g.set(ylim=(data_mag_melted.signal_reading.min(),data_mag_melted.signal_reading.max()))
    if save:
        plt.savefig('fig/'+filename[:-4]+'_MAG.png')
    if show:
        plt.show()
        
    # both matrix and magnetic plot
    g = sns.lmplot(x="motor_step", y="signal_reading", col="signal_type", hue="signal_type", data=data_mat_mag_melted,
           col_wrap=4, ci=90, palette="dark", height=3, col_order=COL_ORDER_2, sharey=False,
           scatter_kws={"s": 2, "alpha": 1})
    # set axis limit
    axes = g.axes
    for i in range(16):
        axes[i].set_ylim(data_mat_melted.signal_reading.min(),data_mat_melted.signal_reading.max())
    axes[-3].set_ylim(data_mag_melted.signal_reading.min(),data_mag_melted.signal_reading.max())
    axes[-2].set_ylim(data_mag_melted.signal_reading.min(),data_mag_melted.signal_reading.max())
    axes[-1].set_ylim(data_mag_melted.signal_reading.min(),data_mag_melted.signal_reading.max())
    if save:
        plt.savefig('fig/'+filename[:-4]+'_MAT_MAG.png')
    if show:
        plt.show()
        
    # line plot for magnetic signal
    g = sns.lineplot(data=data_mag_melted, x="motor_step", y="signal_reading",hue="signal_type",
                     ci="sd")
    if show:
        plt.show()
    # line plot for piezoresistive signal
    g = sns.relplot(data=data_mat_melted, x="motor_step", y="signal_reading", col="signal_type", hue="signal_type",col_wrap=4,
                     kind="line")
    if show:
        plt.show()
def plot_time(filename, save=False, show=True, rang=False):
    
    data_mat_melted, data_mag_melted, data_mat_mag_melted = melt_data_time(filename,rang)
    g = sns.lineplot(data=data_mag_melted, x="milliseconds", y="signal_reading",hue="signal_type",
                     ci="sd")
    if show:
        plt.show()
    
if __name__ == '__main__':
    filename = 'data/Achieved/S4_1000_points_20201217_164234.csv'
    plot_mat(filename,save=False,show=True)
    plot_time(filename,rang=[100,270])
    