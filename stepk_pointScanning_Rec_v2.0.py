"v2.0: hardware trigger by DMD and calibration camera."
import numpy as np
import time
import matplotlib.pyplot as plt
from ALP4 import *
from pypylon import pylon
import traceback
import datetime
from fncudaLee2 import *
import matlab.engine

# Instantiate Matlab engine.
eng = matlab.engine.start_matlab()
# Define import parameters.
# Adjust settings here.
hadamardSize = 64
shiftingPhases = 3 # Poppof proposes:
FRAMERATE = 1000 # Adjust the camera and DMD rates here.
scanPoints_1D = 64 # 8 # 32 # 64 # 128 # 256
scanPoints_total = scanPoints_1D ** 2
numFrames = scanPoints_total

SELECTEDCARRIER = 0.19
ROTATION = 55/180*np.pi
DMDWIDTH = 1024
DMDHEIGH = 768
CAMWDITH = 256
CAMHEIGHT = 256
CAMWDITH_REC = 480
CAMHEIGHT_REC = 480
CAMBITDEPTH = "Mono10"
BITDEPTH = 1
PictureTime = int(1.0 / (FRAMERATE) * 1000000) # in uSecs, 5000 PictureTime is 200 Hz, need to be integer
numModes = hadamardSize * hadamardSize # 64 * 64 hadamard size

if hadamardSize == 16:
    leeBlockSize = 32 # the block number to expand the hadamard matrix
    numReferencePixels = 128 # (768-hadamardsize*leeBlockSize)/2 for marginal pixel
elif hadamardSize == 64:
    leeBlockSize = 12 # the block number to expand the hadamard matrix (also the mirror number per mode)
    numReferencePixels = 0 # (768-hadamardsize*leeBlockSize)/2 for marginal pixels
elif hadamardSize == 32:
    leeBlockSize = 24 # the block number to expand the hadamard matrix (also the mirror number per mode)
    numReferencePixels = 0 # (768-hadamardsize*leeBlockSize)/2 for marginal pixels
        

print("Generating focus point patterns...")
# test scanning focus points on the camera
startTime = time.time()
Kinv_angle = np.load("Kinv_angle_{0}_{1}_0.npy".format(numModes, shiftingPhases))

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

phaseBasis = np.load("phaseBasis_{0}_{1}.npy".format(numModes,  shiftingPhases))
WeightedInputToGenerateTarget = np.reshape(np.matmul(np.exp(1j*(np.reshape(phaseBasis, (hadamardSize*hadamardSize, numModes)))), np.exp(1j*E_in_phase)), (hadamardSize,hadamardSize,scanPoints_total))
# Wrap Angles to 2Pi Radians
E_in=np.angle(WeightedInputToGenerateTarget)%(2*np.pi)
endTime = time.time()
print("Phase calculation using {} seconds".format(endTime-startTime))

## Start to generate one focus point on the camera
# Generate sequences with input field E_in
SweepSequences = np.array(cudaLee2(input_phases=E_in, hadamardSize=hadamardSize, totalPoints=scanPoints_total,
                                 Lxy=leeBlockSize, f_carrier=SELECTEDCARRIER, rot=ROTATION))
# With packing array as DMD sequences
raveledTargetSequences = np.uint8(SweepSequences.transpose(1, 0, 2).ravel(order='F'))

# Load the Vialux .dll
DMD = ALP4(version = '4.3')
cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
cam.Open()

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

if CAMWDITH_REC <= cam.Width.Value or CAMHEIGHT_REC <= cam.Height.Value:
    cam.Width.Value = CAMWDITH_REC
    cam.Height.Value = CAMHEIGHT_REC
    cam.OffsetX.Value = int((640-CAMWDITH_REC)/2)
    cam.OffsetY.Value = int((480-CAMHEIGHT_REC)/2)
else:
    cam.OffsetX.Value = int((640-CAMWDITH_REC)/2)
    cam.OffsetY.Value = int((480-CAMHEIGHT_REC)/2)
    cam.Width.Value = CAMWDITH_REC
    cam.Height.Value = CAMHEIGHT_REC
    
# Set camera gain and frame rate.
cam.PixelFormat.Value = CAMBITDEPTH
cam.Gain.value = 0
cam.ExposureTime.Value = 400
# Set acquisition
# cam.AcquisitionFrameRateEnable.SetValue(True)
# cam.AcquisitionFrameRate.SetValue(FRAMERATE)
d = cam.ResultingFrameRate.Value
print("The resulting frame rate is: " + str(d))

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
DMD.SeqPut(imgData = raveledTargetSequences)
# Set image rate to FRAMERATE
DMD.SetTiming(pictureTime = PictureTime)
# Run the sequence in an infinite loop

# Instantiate callback handler of camera image
handler = ImageHandler()
# handler registration for camera
cam.RegisterImageEventHandler(handler , pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_None)
# Background loop to get the camera images (use this mode to communicate with the 
# camera while the images are collected in the backgound.)
cam.StartGrabbingMax(numFrames + 1, pylon.GrabStrategy_LatestImages, pylon.GrabLoop_ProvidedByInstantCamera)

DMD.Run(loop=False)
# camera_display(numFrames = numFrames)
DMD.Wait()

cam.StopGrabbing()
cam.DeregisterImageEventHandler(handler)
cam.TriggerMode.Value = "Off"
cam.Close()
print("Camera closed!")
print("Recorded frames in the camera is: ", str(handler.count)) # if N * phases shifting, sync correctly
cameraImages = np.array(handler.img_sum).transpose(1,2,0)
print("first frames of the camera is: ", str(cameraImages[1:20,300:320,1]))
print("The shape of the images is: {}".format(cameraImages.shape))
# check if captured camera frames are the same with the patterns
assert cameraImages.shape[2] == numFrames

#################################################
## Release DMD
DMD.Halt()
DMD.FreeSeq()
DMD.Free()
print("DMD release complete!")
print("Saving camera images...")
np.save("CamImages_1DSampling_{0}_{1}".format(scanPoints_1D, datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')), cameraImages)
print("Saving completed!")
# Show the first record
plt.imshow(cameraImages[:,:,int((scanPoints_total+scanPoints_1D-1.5)/2)])
plt.colorbar()
plt.show()