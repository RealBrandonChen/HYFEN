'''
Georgia Tech
@Author Peng CHEN
Created on 02-23-2024
V1.0 Generate scanning foucs points --> collect the signals from PMT --> reconstruction images
with the scanning signals.
V2.0 update: using TM tracking method to accelerate the phase generation.
V2.1 update: hardware trigger between the DMD and DAQ with a PWM trigger multiplier.
'''

import numpy as np
import time
from ALP4 import *
from NI_Sampling_v2 import *
from fncudaLee2 import *
import datetime
import matlab.engine
import gc # memory management

# Instantiate Matlab engine.
eng = matlab.engine.start_matlab()

# Define import parameters.
hadamardSize = 64
shiftingPhases = 3 # Poppof proposes:
scanPoints_1D = 256 # 8 # 32 # 64 # 128 # 256
scanPoints_total = scanPoints_1D**2
FRAMERATE = 2e4 # Adjust the camera and DMD rates here.

SELECTEDCARRIER = 0.19
ROTATION = 55/180*np.pi
DMDWIDTH = 1024
DMDHEIGH = 768
BITDEPTH = 1
CAMWDITH = 256
CAMHEIGHT = 256
PictureTime = int(1.0 / (FRAMERATE) * 1000000) # in uSecs, 5000 PictureTime is 200 Hz, need to be integer
# zDepth = int(input("Assign the focal distance (microns, 0 --> 7.5, 1,2,3,4,5 --> 12.5):")) # the distance between the fiber facet and the sample
zDepth = 0

numModes = hadamardSize * hadamardSize # 64 * 64 hadamard size
numFrames = numModes * shiftingPhases
if hadamardSize == 16:
    leeBlockSize = 32 # the block number to expand the hadamard matrix
    numReferencePixels = 128 # (768-hadamardsize*leeBlockSize)/2 for marginal pixel
elif hadamardSize == 64:
    leeBlockSize = 12 # the block number to expand the hadamard matrix (also the mirror number per mode)
    numReferencePixels = 0 # (768-hadamardsize*leeBlockSize)/2 for marginal pixels
elif hadamardSize == 32:
    leeBlockSize = 24 # the block number to expand the hadamard matrix (also the mirror number per mode)
    numReferencePixels = 0 # (768-hadamardsize*leeBlockSize)/2 for marginal pixels
      
# Load the Vialux .dll
DMD = ALP4(version = '4.3')
# Initiate the DAQ
NI = daq_samp(sample_rate=FRAMERATE, im_size=int(scanPoints_1D), showplot=True, savefig=True)
# start the task but acquisition is activated by DMD running, see NI_Sampling codes for details
NI.start_acquisition()
print("Generating focus point patterns...")
# test scanning focus points on the camera
startTime = time.time()

Kinv_angle = np.load("Kinv_angle_{0}_{1}_{2}.npy".format(numModes, shiftingPhases, zDepth))
# input Ein_all and the scanning index output target phases

if scanPoints_1D == 1:
    scanXRange = int(CAMWDITH/2)
    scanYRange = int(CAMHEIGHT/2)
else:
    scanXRange = np.linspace(start=0, stop=CAMWDITH, num=scanPoints_1D, endpoint=False, dtype=int)
    scanYRange = np.linspace(start=0, stop=CAMHEIGHT, num=scanPoints_1D, endpoint=False, dtype=int)
XV, YV = np.meshgrid(scanXRange, scanYRange)
# transfer index arrays to flat indices
ravelIndex = np.ravel_multi_index(multi_index=(YV.flatten(), XV.flatten()), dims=(CAMWDITH, CAMHEIGHT))
E_in_phase = Kinv_angle[:,ravelIndex]

endTime = time.time()
print("Phase generation using {} seconds".format(np.round(endTime-startTime, decimals=1)))

phaseBasis = np.load("phaseBasis_{0}_{1}.npy".format(numModes,  shiftingPhases))
WeightedInputToGenerateTarget = np.reshape(np.matmul(np.exp(1j*(np.reshape(phaseBasis, (hadamardSize*hadamardSize, numModes)))), np.exp(1j*E_in_phase)), (hadamardSize,hadamardSize,scanPoints_total))
# Wrap Angles to 2Pi Radians
E_in=np.angle(WeightedInputToGenerateTarget)%(2*np.pi)
# show the target phase
# print("The shape of the E_in_phase is: {}".format(E_in.shape))
# plt.imshow(E_in[:,:,0])
# plt.colorbar()
# plt.show()
del Kinv_angle
del phaseBasis
del E_in_phase

# Generate sequences with input field E_in
SweepSequences = np.array(cudaLee2(input_phases=E_in, hadamardSize=hadamardSize, totalPoints=scanPoints_total,
                                 Lxy=leeBlockSize, f_carrier=SELECTEDCARRIER, rot=ROTATION))
# With packing array as DMD sequences
raveledTargetSequences = np.uint8(SweepSequences.transpose(1, 0, 2).ravel(order='F'))

del SweepSequences
gc.collect()

################################################################
# Upload and play sequences
# Initialize the DMD device
print("Generating target points...")
DMD.Initialize()
DMD.SeqAlloc(nbImg = scanPoints_total, bitDepth = BITDEPTH)
# # Sequences uploaded in a packed format
DMD.SeqControl(ALP_DATA_FORMAT, ALP_DATA_BINARY_TOPDOWN)
DMD.SeqControl(ALP_BITNUM, BITDEPTH)
DMD.SeqControl(ALP_FIRSTFRAME, 0)
DMD.SeqControl(ALP_LASTFRAME, int(scanPoints_total)-1)
DMD.SeqControl(ALP_BIN_MODE, ALP_BIN_UNINTERRUPTED)
# Send the image sequence as a 1D list/array/numpy array
# DMD.SeqPut(imgData = SweepSequences.ravel())
DMD.SeqPut(imgData = raveledTargetSequences)
# Set image rate to FRAMERATE
DMD.SetTiming(pictureTime = PictureTime)
# DAQ activated to acquire the PMT analogous voltage
print("DAQ start acquisition...")
# Run the sequence in an infinite loop
DMD.Run(loop=True)
input('press return to stop imaging...')
NI.stop_acquisition()
NI.close_tasks()

#################################################
## Release DMD
DMD.Halt()
DMD.FreeSeq()
DMD.Free()
print("DMD release complete!")