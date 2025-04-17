'''
Georgia Tech
@Author Peng CHEN
Created on 12-15-2023
Generate the Patterns with phase shift method. Matlab codes are integrated.
'''
import sys
import matlab.engine
import time
import numpy as np
import os  

# Define import parameters
HadamardSize = 64 # or 64 or 16 or 96
numPhaseShift = 3 # 3 or 4
DMDwidth = 1024
DMDheight = 768
selectedCarrier = 0.19
eng = matlab.engine.start_matlab()

# Test if matlab engine works.
# ret = eng.triarea(1.0,5.0)
# if ret == 2.5:
#     print("The Matlab engine functions well!")
# else:
#     print("Please check that if the Matlab engine works!")

start_time = time.time()
# generate interference basis patterns
# interferenceBasisPatterns = eng.fnPhaseShiftReferencePadLeeHologram(HadamardSize, leeBlockSize, numReferencePixels,\
#     numModes, numPhaseShift)
# Generate folder to save matrix 
matrixFolder = "D:\Software\Cache"
try:  
    os.mkdir(matrixFolder)  
except OSError as error:  
    print(error) 

# Generate Walsh basis phases
walshbasis = eng.fnBuildWalshBasis(HadamardSize); # sequency order of the hadamard matrix
phaseBasis = np.single((np.array(walshbasis) == 1)*np.pi)
print(phaseBasis.shape)
np.save("phaseBasis_{0}_{1}".format(HadamardSize**2, numPhaseShift), phaseBasis)

interferenceBasisPatterns = eng.LeeHologramGen(phaseBasis, numPhaseShift, DMDwidth, DMDheight, selectedCarrier)
end_time = time.time()
print("Using time {} seconds to generate the patterns".format(int(end_time - start_time)))
# Convert Matlab logic object to Python array
interferenceBasisPatterns = np.array(interferenceBasisPatterns)
print("The shape of the patterns: {}".format(interferenceBasisPatterns.shape))
np.save("interferenceBasisPatterns_{0}_{1}".format(HadamardSize**2, numPhaseShift), interferenceBasisPatterns)



