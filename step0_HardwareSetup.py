'''
Setup the field of view of the Basler camera that used for output calibration and the 
exposure time. 
'''
from pypylon import pylon
import traceback

CAMERAWIDTH = 256 # Maximum framerate is 400 when 480, 500 when 256
CAMERAHEIGHT = 256
CAMBITDEPTH = "Mono10"
FRAMERATE = 200
cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
cam.Open()
# Print the model name of the camera.
print("Using camera device: ", cam.GetDeviceInfo().GetModelName())

################################################################
# Control the parameter of the Basler camera
cam.TriggerMode.Value = "Off"
# Set camera gain and frame rate.
# Set the offset to 0
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

cam.PixelFormat.Value = CAMBITDEPTH
cam.Gain.value = 0
cam.ExposureTime.Value = 1000
# Set acquisition rate
cam.AcquisitionFrameRateEnable.SetValue(True)
cam.AcquisitionFrameRate.SetValue(FRAMERATE)
d = cam.ResultingFrameRate.Value
print("The resulting frame rate is: " + str(d) + "\n")

cam.Close()
print("Camera field of view (FOV) set up successfully!")