'''
Georgia Tech
@Author Peng CHEN
Created on 11-23-2023
Generate random speckles for the multimode fiber. Bascally used for fiber coupling and 
setup calibrations.
Notes: If the cell samples are in good condition (non-bleached), for ground truth recording, 
the camera exposure time should be under 20,000 us with laser power 10 mW or fiber output under 200 uW.
'''

import numpy as np
import time
from pathlib import Path
import cv2
from ALP4 import *

# Load the Vialux .dll
DMD = ALP4(version = '4.3')
# define some common parameters
frameRate = float(input("Please assign the DMD frequency as Hz:")) # Hz, matched with camera exposured time
bitDepth = 1 
IlluminateTime = 0 # Ignored, we are in uninterrupted binary mode
PictureTime = int(1.0 / (frameRate) * 1000000) # in uSecs, 5000 PictureTime is 200 Hz, need to be integer
numModes = 256
shiftingPhases = 3
numFrames = numModes * shiftingPhases 

# Load patterns and convert it to grayscale
t1 = time.time()
interferenceBasisPatterns = np.load("interferenceBasisPatterns_{0}_{1}.npy".format(numModes, shiftingPhases)) * (2**8-1)
t2 = time.time()
print("Sequences raveling is {} seconds".format(int(t2-t1)))

# Initialize the device
DMD.Initialize()
print("Operating DMD type: " + str(DMD.DevInquire(ALP_DEV_DMDTYPE)))
print("Run DMD with {} Hz".format(frameRate))

t3 = time.time()
# allocate onboard memory for the image sequence
DMD.SeqAlloc(nbImg = numFrames, bitDepth = bitDepth)
print("Using DMD RAM {} MB ...".format(int(interferenceBasisPatterns.shape[0] * interferenceBasisPatterns.shape[1] * interferenceBasisPatterns.shape[2] / 1e6)))
# Ravel Lee Hologram to 1D array for sequences put, value must be 0 or 255
raveledLeeHologram = np.uint8(interferenceBasisPatterns.transpose(1, 0, 2).ravel(order='F'))
t4 = time.time()
print("Sequences raveling is {} seconds".format(int(t4-t3)))
# Send the image sequence as a 1D list/array/numpy array
DMD.SeqPut(imgData = raveledLeeHologram)
# Set image rate
DMD.SetTiming(pictureTime = PictureTime)
t5 = time.time()
print("Sequences upload time is {} seconds".format(int(t5-t4)))

# Run the sequence in an infinite loop
DMD.Run(loop=True)
input("Press enter to stop...")

# Stop the sequence display
DMD.Halt()
# Free the sequence from the onboard memory
DMD.FreeSeq()
# De-allocate the device
DMD.Free()