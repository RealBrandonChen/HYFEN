'''
Georgia Tech
@Author Peng CHEN
Created on 11-23-2023
Measurement of the transmission matrix of the multimode fiber/ hydrogel fiber
with a Vialux DMD and Basler camera. Install the dependencies at requirements.txt first.
v2.0 update: Hardware trigger between DMD and camera.
'''
import numpy as np
import time
from ALP4 import *
from pypylon import pylon
import traceback
import matplotlib.pyplot as plt
import gc # memory management

# Define import parameters.
hadamardSize = 64 # (needs to be power of 2. Use 8,16,32,64)
FRAMERATE = 1000 # 50, 100, 125, 200 # Adjust the camera and DMD rates here. !!! 1000 % framerate = 0 to satisfy the integer of the DMD rate.
shiftingPhases = 3 # Poppof proposes:
SELECTEDCARRIER = 0.19
DMDWIDTH = 1024
DMDHEIGH = 768
CAMERAWIDTH = 256 # Maximum framerate is 400 when 480, 500 when 256
CAMERAHEIGHT = 256
CAMBITDEPTH = "Mono10"
numModes = hadamardSize * hadamardSize # 64 * 64 hadamard size

# define some common parameters for DMD
BITDEPTH = 1 
IlluminateTime = 0 # Ignored, we are in uninterrupted binary mode
PictureTime = int(1.0 / (FRAMERATE) * 1000000) # in uSecs, 5000 PictureTime is 200 Hz, need to be integer
SynchDelay = 0 # Ignored
SynchPulseWidth = int(PictureTime / 2) # Ignored
TriggerInDelay = 0 # Ignored for binary mode
numFrames = numModes * shiftingPhases
# zDepth = int(input("Assign the focal distance (microns, 0 --> 7.5, 1,2,3,4,5 --> 12.5):")) # the distance between the fiber facet and the sample
zDepth = 0

# Load the Vialux .dll
DMD = ALP4(version = '4.3')
# Initiate the camera
cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
cam.Open()
# Print the model name of the camera.
print("Using camera device: ", cam.GetDeviceInfo().GetModelName())

# class of image handler
class ImageHandler(pylon.ImageEventHandler):
    def __init__(self):
        super().__init__()
        self.count = 0
        self.img_sum = []
        
    def OnImagesSkipped(self, camera, countOfSkippedImages):
        print(countOfSkippedImages, " images have been skipped.")
        
    def OnImageGrabbed(self, camera, grabResult):
        """ we get called on every image
            !! this code is run in a pylon thread context
            always wrap your code in the try .. except to capture
            errors inside the grabbing as this can't be properly reported from 
            the background thread to the foreground python code
        """
        try:
            if grabResult.GrabSucceeded():
                # check image contents
                img = grabResult.Array
                # Stack images to 3D array
                self.img_sum.append(img)
                self.count += 1
                grabResult.Release()
            else:
                raise RuntimeError("Grab Failed")
        except Exception as e:
            traceback.print_exc() 


################################################################
# Control the parameter of the Basler camera
# Get clean powerup state
cam.UserSetSelector.Value = "Default"
cam.UserSetLoad.Execute()
# Set the io section
cam.LineSelector.Value = "Line1"
cam.LineMode.Value = "Input"
# Setup the trigger/ acquisition controls
cam.TriggerSelector.Value = "FrameStart"
cam.TriggerSource.Value = "Line1"
cam.TriggerMode.Value = "On"
cam.TriggerActivation.Value = "RisingEdge"
print("The resulting Trigger Activation is: " + str(cam.TriggerActivation.Value))

if CAMERAWIDTH <= cam.Width.Value or CAMERAHEIGHT <= cam.Height.Value:
    cam.Width.Value = CAMERAWIDTH
    cam.Height.Value = CAMERAHEIGHT
    cam.OffsetX.Value = int((640-CAMERAWIDTH)/2)
    cam.OffsetY.Value = int((480-CAMERAHEIGHT)/2)
else:
    cam.OffsetX.Value = int((640-CAMERAWIDTH)/2)
    cam.OffsetY.Value = int((480-CAMERAHEIGHT)/2)
    cam.Width.Value = CAMERAWIDTH
    cam.Height.Value = CAMERAHEIGHT

# Set camera gain and frame rate.
# Set the offset to 0
cam.PixelFormat.Value = CAMBITDEPTH
cam.Gain.value = 0
cam.ExposureTime.Value = 1000

# Set acquisition
# cam.AcquisitionFrameRateEnable.SetValue(True)
# cam.AcquisitionFrameRate.SetValue(FRAMERATE)
d = cam.ResultingFrameRate.Value
print("The resulting frame rate is: " + str(d))

## Upload calibration sequences ##
print("Uploading calibration sequences...")
interferenceBasisPatterns = np.uint8(np.load("interferenceBasisPatterns_{0}_{1}.npy".format(numModes, shiftingPhases))) * (2**8-1)
t1 = time.time()
# Ravel Lee Hologram to 1D array for sequences put, value must be 0 or 255
raveledLeeHologram = interferenceBasisPatterns.transpose(1, 0, 2).ravel(order='F')
t2 = time.time()
print("Sequences raveling with {} seconds".format(int(t2-t1)))

# Initialize the DMD device
DMD.Initialize()
print("Operating DMD type: " + str(DMD.DevInquire(ALP_DEV_DMDTYPE)))
# onboard memory for the image sequence
DMD.SeqAlloc(nbImg = numFrames, bitDepth = BITDEPTH)
print("Using DMD RAM {} MB ...".format(int(interferenceBasisPatterns.shape[0] * interferenceBasisPatterns.shape[1] * interferenceBasisPatterns.shape[2] / 1e6)))
# Send the image sequence as a 1D list/array/numpy array
DMD.SeqPut(imgData = raveledLeeHologram)
# Set image rate
DMD.SetTiming(pictureTime = PictureTime)
t5 = time.time()
print("Sequences upload time with {} seconds".format(int(t5-t2)))

# delete the large sequence in the memory
# trigger garbage collection, free memory
del interferenceBasisPatterns
del raveledLeeHologram
collected = gc.collect() 
print("CPU matrix memory freed.")

# Instantiate callback handler of camera image
handler = ImageHandler()
# handler registration for camera
cam.RegisterImageEventHandler(handler , pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_None)

# Background loop to get the camera images (use this mode to communicate with the 
# camera while the images are collected in the backgound.)
print("Running sequences and calibration...")

cam.StartGrabbingMax(numFrames + 1, pylon.GrabStrategy_LatestImages, pylon.GrabLoop_ProvidedByInstantCamera)
t1 = time.time()
# Start DMD display in parallel and fetch some images with background loop
DMD.Run(loop=False)
# Wait for the sequences to finish
DMD.Wait()
# time.sleep(numFrames / FRAMERATE)
t2 = time.time()
cam.StopGrabbing()
cam.DeregisterImageEventHandler(handler)
cam.TriggerMode.Value = "Off"
cam.Close()
print("Camera closed!")
print("Recorded frames in the camera is: ", str(handler.count)) # if N * phases shifting, sync correctly
cameraImages = np.array(handler.img_sum).transpose(1,2,0)
print("first frames of the camera is: ", str(cameraImages[1:20,1,1]))
print("Calibration time: ", str(t2-t1))
print("The shape of the images is: {}".format(cameraImages.shape))
# check if captured camera frames are the same with the patterns
assert cameraImages.shape[2] == numFrames

DMD.Halt()
DMD.FreeSeq()
DMD.Free()
print("DMD device freed!")
################################################################

# Show the cropped image and decide whether to proceed the procedure
plt.imshow(cameraImages[:,:,0])
plt.colorbar()
plt.show()

################################################################
# Calculate the inverse Transmission Matrix
print("Computing transmission matrix...\n")
newSize = cameraImages.shape
K = np.zeros((numModes, newSize[0]*newSize[1]), dtype=np.single)
J2 = np.array(cameraImages).astype(np.single)
'''
Three phases: [0, pi/2, pi]
(I[0]-I[pi/2])/4 +i*(I[pi]-I[pi/2])/4
Four phases: [0, pi/2, pi, 3*pi/2]
I[0]-I[pi]   +i*I[3*pi/2]-I[pi/2])
'''

calStartTime = time.time()
k = numModes
calStartTime = time.time()
if shiftingPhases == 3: # fast method
    K = (J2[:,:,:3*k+1:3]-J2[:,:,1:3*k+1:3])/4 + 1j * (J2[:,:,2:3*k+1:3] - J2[:,:,1:3*k+1:3])/4
elif shiftingPhases == 4: # old, PRL method
    K = (J2[:,:,:4*k+1:4]-J2[:,:,2:4*k+1:4])/4 + 1j * (J2[:,:,3:4*k+1:4] - J2[:,:,1:4*k+1:4])/4

K_obs = np.reshape(K, (newSize[0]*newSize[1], numModes))
Kinv_angle = -np.angle(K_obs.T)

calEndTime = time.time()

print("Calculated using {} seconds".format(calEndTime-calStartTime))
# np.save("K_obs_{0}_{1}".format(numModes, shiftingPhases), K_obs)
np.save("Kinv_angle_{0}_{1}_{2}".format(numModes, shiftingPhases, zDepth), Kinv_angle)