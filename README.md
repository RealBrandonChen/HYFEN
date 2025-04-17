# HYFEN
This respoitory includes the software for the calibration and imaging of the paper "High-Resolution Fluorescence Endoscopy via Flexible Hydrogel Optical Fibers". Conventional multimode fiber (MMF) imaging system can also be drived with the repository.

## Software environment setup
1. Install Anaconda Navigator, Visual Studio Code, and Git
2. Clone this repository from to your local folder
3. Run the following in your terminal:
```
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```
4.  Install conda environment for Python == 3.10 
5.  Run the following in your terminal to install the dependencies
```
pip install -r requirements.txt
``` 
6. Create empty folder "D:/Software/Cache" to store the Hadamard basis.

## Hardware
### Digital micro-mirror device (DMD) ViALUX V-7001
Width: `1024` Height: `768` RAM: `16GB (128Gbit)` 
### Camera Basler ace acA640-750um
Width: `256`
Height: `256`
PixelFormat:`"Mono10"`
ExposureTime: `1000`
TriggerMode: `ON`
### Photomultiplier tube (PMT) Thorlabs PMT2101
Bandwith: `250 kHz`
Gain: `1`
Output offset: `-0.022 V`

## Experimental step
### A. Hadamard basis generation
Run `interferenceArryaGen.py` and the phases based on Hadamard basis will be saved in the folder.
### B. Transmission matrix (TM) measurement
1. Run `step0_HardwareSetup.py` to adjust the exposure time for the camera
2. Run `step1_calibrateSpeckle.py` for fiber coupling and adjusting the laser power
3. Run `step2_measureTM_Angle_v2.0` to start the calibration process, and the angular TM will be saved in the folder
### C. Imaging step
Align the fiber imaging plane with the sample plane. Run `step3_pointScanningFluo_v2.1`. Real-time imaging window will popup. You can press `Enter` to stop imaging. All the images will be saved automatically into the folder `Acquisition`.

## Creators
Peng Chen@[Github](https://github.com/RealBrandonChen)
## Acknowledgments
Design files and source code for fiber microscope[^1]
[^1]: [The DiCarlo Lab at MIT](https://github.com/dicarlolab)