'''
Check the curve of enhancement factor stability online
'''
import numpy as np
import matplotlib
matplotlib.use('qt5agg') # use Qt5 as the background engine, defacut matplot engine is Tk, will casue loop processes error
import matplotlib.pyplot as plt
import os
import os.path
import datetime
from scipy.signal import savgol_filter
import time

# Load data
rawDataFolder = "..\your_image_directory"
# file_count = len([name for name in os.listdir(rawDataFolder) if os.path.isfile(name)])
# print(file_count)
# raw_foci = []
# for i in os.listdir(rawDataFolder):
#   data = np.load(rawDataFolder+"\\" + i)
#   raw_foci.append(data)
# raw_foci = np.array(raw_foci)

plt.ion()
fig, ax = plt.subplots()
x_t = np.linspace(0.0, 600, num = 600)
y = np.linspace(0.0, 1500, num = 600)
ax.set_xlim([0, 600])
ax.set_ylim([0, 1500])
line1, = ax.plot(x_t, y, 'b-') # Returns a tuple of line objects, thus the comma

# raw_foci = np.zeros((256,256,file_count))
# I_avg = np.zeros((newShape[0],1))
EF_extend = np.zeros(600,)
data_directory = os.fsencode(rawDataFolder)

# update plot everyt 10 seconds
while True:
    raw_foci = []
    for i in os.listdir(rawDataFolder):
        data = np.load(rawDataFolder+"\\" + i)
        raw_foci.append(data)
    raw_foci = np.array(raw_foci)
    newShape = raw_foci.shape
    print(newShape)
    # background noise reduction
    baseline = (np.array(plt.imread('Analysis\\Baseline_ND=4.tiff'))[112:112+256, 192:192+256])/(2**6)
    # baseline = (np.array(plt.imread('Analysis\\Baseline_ND=4.tiff'))[:, 80:80+480])/(2**6)
    baseline_average = np.sum(baseline)/(256*256)
    focusImages = raw_foci - baseline_average
    focusImages = np.where(focusImages > 0, focusImages, 0)
    # Calculate the enhancement factor from the data

    I_peak = np.max(focusImages, axis=(1,2))
    # print("I_peak: ", I_peak[samping_1D])
    I_avg = (np.sum(focusImages, axis=(1,2)))/ (256 * 256)
    print("The shape of the I_peak is {0} and I_peak is {1}".format(I_peak.shape, I_peak[newShape[0]-2]))
    # print("The shape of the I_avg is {0} and I_avg is {1}".format(I_avg.shape, I_avg[0]))
    EF_matrix = np.round(np.divide(I_peak, I_avg), decimals=2)

    ################################################################
    # Plot the EF in terms of the elapsed time
    # X axis: time, Y axis: EF values
    EF_extend[0: newShape[0]] = EF_matrix
    y_ef = EF_extend
    # yhat = savgol_filter(y_ef, 51, 3) # window size 51, polynomial order 3

    line1.set_ydata(y_ef)
    # ax.plot(x_t, y_ef, alpha=0.3)
    # ax.plot(x_t, yhat, color='orange')
    ax.set(xlabel = 'Elapsed time (s)', ylabel = 'Enhancement Factor',
        title = 'Enhancement Factor (I_peak/I_avg) with time')
    # ax.grid()
    # fig.savefig('Analysis\EF_plots\Enhancement Factor_{0}_{1}_{2}.png'.format(numModes,
                                                            # shiftingPhases ,datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')))
    fig.canvas.draw()
    fig.canvas.flush_events()
    
    time.sleep(10)