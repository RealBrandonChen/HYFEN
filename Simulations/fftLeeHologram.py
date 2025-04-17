import numpy as np
import matplotlib.pyplot as plt

# interference patterns loaded into DMD
interferencePatterns = np.load("interferenceBasisPatterns_16_16_256_3.npy")
pattern1 = interferencePatterns[:,:,0]

plt.show()
# At Fourier plane
coeff = 5
ROIsize = 1500
ROI = 1

fftPat = np.fft.fftshift(np.fft.fft2(pattern1, s=[coeff*768,coeff*1024]))
plt.figure()
plt.imshow((np.abs(fftPat[coeff*768//2-ROIsize//2:coeff*768//2+ROIsize//2,coeff*1024//2-ROIsize//2:coeff*1024//2+ROIsize//2])),interpolation = 'None')
plt.clim([0,(np.max(np.abs(fftPat)))/1.5])
# plt.scatter(ROIsize//2, ROIsize//2, s=200, edgecolors='red',alpha = 0.5,c='yellow',linewidths= 3.,  marker='x')
# plt.imshow(np.abs(fftPat))
plt.show()



