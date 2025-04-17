'''
Georgia Tech
@Author Peng CHEN
Created on 06-20-2024
Simulation of raster scanning with experimental PSF convolved with imaging target.
Algorithm: 
'''
import numpy as np
import sys
sys.path.append("..\your_codes_root")
import matplotlib.pyplot as plt
from PIL import Image
import os 

# define parameters:
testing_1D = 128
totalPoints = testing_1D ** 2

array_name = "\.npy" # hydrogel fiber scanning foci
array_dir = str(os.getcwd()) + "..\your_image_directory" + array_name
# import data
cameraImages = np.load(array_dir)
# img_foci = plt.imshow(cameraImages[:,:,9001])
# plt.colorbar()
# plt.show()
# baseline = (np.array(plt.imread('Analysis\\Baseline_ND=4.tiff'))[112:112+256, 192:192+256])/(2**6)
camShape = cameraImages.shape
print(camShape)
# baseline_average = np.sum(baseline)/(camShape[0]*camShape[1])
# focusImages = cameraImages - baseline_average
# focusImages = np.where(focusImages > 0, focusImages, 0)
noise_threshold = 10
sparse_points  = np.where(cameraImages > noise_threshold, cameraImages, 0)
sparse_points = np.reshape(sparse_points, (256,256,testing_1D,testing_1D))

groundTruthImage = np.array(plt.imread('Simulations\\GT_250um_FOV_1_256.tif'))
groundTruthImage_crop = groundTruthImage
# img_foci = plt.imshow(sparse_points[:,:,100,100])
# plt.colorbar()
# plt.show()

simScanImage = np.ones((testing_1D, testing_1D)) * 255
groundTruthImage_crop_sim  = np.ones((256, 256)) * 255
# for i in range(testing_1D):
#     for j in range(testing_1D):
#         simScanImage[i, j] = np.sum(np.multiply(sparse_points[:,:,i*testing_1D+j], groundTruthImage_crop))

for i in range(testing_1D):
    for j in range(testing_1D):
        simScanImage[i, j] = np.sum(np.multiply(groundTruthImage_crop, sparse_points[:,:,i,j]))
        # print(simScanImage[i, j])
        
plt.imshow(simScanImage)
plt.colorbar()
plt.show()          
# show simulated image
# simScanImage_norm = 1-simScanImage/simScanImage.max()
# fig, ax = plt.subplots()
# simScanImage_norm = ax.imshow(simScanImage_norm, cmap=plt.get_cmap('binary'), vmin=0, vmax=1)
# fig.colorbar(simScanImage_norm)
# ax.set_axis_off()
# plt.show()

im_foci = Image.fromarray(simScanImage)
im_foci.save("Figures\hydrogel.tiff".format(array_name.split('/')[-1].split('.')[0]), "TIFF")
