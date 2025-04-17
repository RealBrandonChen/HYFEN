import numpy as np
from PIL import Image
import sys
import os
import datetime

# add the path for raw data
# sys.path.append("E:\\PENG\\MMF_Codes\\Analysis\\cameraArrays\\12122024")
parent_dir = str(os.getcwd()) + "..\your_image_directory"

def saveTiff(parent_dir):
    
    print(parent_dir)
    for filename in os.listdir(parent_dir):
        imageArrays = np.load(os.path.join(parent_dir, filename))
        
        filename_without_ext = filename.split('/')[-1].split('.')[0]

        os.mkdir(os.path.join(parent_dir, filename_without_ext))
        os.chdir(os.path.join(parent_dir, filename_without_ext))
        for i in range(imageArrays.shape[2]):
            im = Image.fromarray(imageArrays[:,:,i])
            im.save("{:03d}.tiff".format(i), "TIFF")
    
    return

saveTiff(parent_dir)
print("Images saved successfully!")