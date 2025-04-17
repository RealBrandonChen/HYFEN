'''
Georgia Tech
@Author Peng CHEN
Created on 12-07-2024
Stitch overlapped images with Fiji (Image2) plugin - Pairwise stitching. Especially useful for microscopy images with large overlap areas.
Adapted from https://github.com/imagej/pyimagej/issues/119. Orignal algorithm proposed by Preibisch, Bioinformatics, 2009
v1.0: cells stitching for large field of view.
'''
import imagej
import scyjava as sj
import os

parent_dir = "..\your_image_directory"
def renameTiff(parent_dir):
    
    print(parent_dir)
    image_count = 0
    os.chdir(parent_dir)
    for filename in os.listdir(parent_dir):
        os.rename(filename, "{}.tif".format(image_count))
        image_count += 1
    return image_count
# rename the images in the folder as sequences
total_image_tiles = renameTiff(parent_dir)
# total_image_tiles = 11
print("Rename images successfully!")

# ///////////////////////////////////////////////////////////////////////// #
# start imagej
ij = imagej.init('sc.fiji:fiji:2.14.0', headless=False)

# get ConvertService and ImagePlus class
ConvertService = ij.get('org.scijava.convert.ConvertService')
ImagePlus = sj.jimport('ij.ImagePlus')

stitching_image_name = "paired_image.tif"
os.chdir(parent_dir)
print("Current dir: " + str(os.getcwd()))
# total images for stitching
for i in range(total_image_tiles-1):
    # open images
    if i == 0:
        img_temp_a = ij.io().open(os.path.join(parent_dir, '{}.tif'.format(0)))
        img_temp_b = ij.io().open(os.path.join(parent_dir, '{}.tif'.format(1)))
    else:
        img_temp_a = ij.io().open(os.path.join(parent_dir, stitching_image_name))
        img_temp_b = ij.io().open(os.path.join(parent_dir, '{}.tif'.format(i+1)))
    # convert Img to ImagePlus
    imp_temp_a = ConvertService.convert(img_temp_a, ImagePlus)
    imp_temp_b = ConvertService.convert(img_temp_b, ImagePlus)


    # setup plugin args
    plugin = "Pairwise stitching"
    stitching_image_name = "paired_image_{}.tif".format(i)
    args = {"first_image":imp_temp_a,
            "second_image":imp_temp_b,
            "fusion_method":"[Linear Blending]",
            "fused_image": stitching_image_name,
            "check_peaks":400,
            "compute_overlap":True,
            "subpixel_accuracy":False,
            "x":0.0000,
            "y":0.0000,
            "registration_channel_image_1":"[Average all channels]",
            "registration_channel_image_2":"[Average all channels]",
        }


    # now you can show and hide an image
    imp_temp_a.show()
    imp_temp_a.getWindow().setVisible(False)
    imp_temp_b.show()
    imp_temp_b.getWindow().setVisible(False)

    # run plugin
    ij.py.run_plugin(plugin, args)

    # get stitched result, convert to Dataset and save
    
    stitched_imp= ij.py.active_image_plus()
    stitched_imp_python=ij.py.to_dataset(stitched_imp)
   
    ij.io().save(stitched_imp_python, os.path.join(parent_dir, stitching_image_name))

    # close all windows
    ij.py.window_manager().closeAllWindows()

print("Stitching finished!")