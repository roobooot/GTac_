import argparse

import matplotlib.pyplot as plt
import pandas as pd
from IMU_wit import plot_all_imu

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filename", help="set filename to analyze")
    args = parser.parse_args()
    filename_1 = args.filename
    data_pd = pd.read_csv(filename_1, index_col=0, skiprows=0)
    plot_all_imu(data_pd, filename_1)
    plt.show()
    # DueData(datahex)
