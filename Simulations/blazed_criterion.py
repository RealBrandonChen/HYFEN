# -*- coding: utf-8 -*-
# Written by Sebastien Popoff, adapted by Shengfu Cheng
# 08/06/2020
import matplotlib.pyplot as plt
import numpy as np

import matplotlib as mpl
from matplotlib import rc

## Parameters of DMD
d = 13.68 #micromirror pitch
gamma = 12./180*np.pi  #micromirror tilt angle relative to flat state

#Use sqrt(2) to calibrate the incident angle and tilt angle 
#the angle of rotation of the mirrors is at 45 degrees compared to the axis of the pixels
gamma_1D = np.arctan(np.tan(gamma)/np.sqrt(2))
_lambda = 488e-3 #wavelength

## A simple criterion matching the diffraction angle and the reflection angle
_beta = lambda x: 2*gamma_1D-x
m = lambda x: 1.*d/_lambda * (np.sin(x)+np.sin(_beta(x)))

## Test different incident angles
# when m is an integer, we are at a blazing angle with a maximum of energy at the order along the optical axis
# whem m is n+1/2, the enregy is spread over many diffraction orders not aligned with the optical axis
alpha_vec = np.linspace(-np.pi/2,np.pi/2,1000)
alpha_1D_vec = np.arctan(np.tan(alpha_vec)/np.sqrt(2))
criterion = np.abs(np.mod([m(a) for a in alpha_1D_vec],1)-0.5)
#find blaze angle
alpha_loc = np.linspace(0,5*np.pi/18,100)
blaze_angle = 0
for a in alpha_loc:
    if np.abs(np.mod(m(np.arctan(np.tan(a)/np.sqrt(2))),1)-0.5) > np.abs(np.mod(m(np.arctan(np.tan(blaze_angle)/np.sqrt(2))),1)-0.5):
        blaze_angle = a

plt.figure()
plt.plot(alpha_vec*180/np.pi,criterion,linewidth = 1)

plt.plot([0,0],[0.,0.5],color = 'C3',label = r'$\alpha = 0, \mu = %.4f$' \
    % np.abs(np.mod(m(0),1)-0.5), linewidth = 1) #At Normal line of grating surface 

plt.plot([gamma*180/np.pi,gamma*180/np.pi],[0.,0.5],color = 'C1',label = r'$\alpha = \theta_B, \mu = %.4f$' \
     % np.abs(np.mod(m(gamma_1D),1)-0.5),linewidth = 1) #At Normal line of groove surface 

plt.plot([2*gamma*180/np.pi,2*gamma*180/np.pi],[0.,0.5],color = 'C2',label = r'$\alpha = 2\theta_B, \mu = %.4f$' \
    % np.abs(np.mod(m(2*gamma_1D),1)-0.5), linewidth = 1) #2-time angles away from the normal of grating surface

plt.plot([blaze_angle*180/np.pi,blaze_angle*180/np.pi],[0.,0.5],color = 'C4',label = r'$\alpha = %.2f^{0}, \mu = %.4f$' \
    % (blaze_angle*180/np.pi, np.abs(np.mod(m(np.arctan(np.tan(blaze_angle)/np.sqrt(2))),1)-0.5)), linewidth = 1) #blaze angle

plt.xticks(np.arange(-90,90,10))
plt.yticks(np.arange(0,0.55,0.05))
plt.title(r'Blazing condition when $d=%.1f\mu m, \lambda =%g nm$' % (d,1e3*_lambda))
plt.legend(loc='center right')
plt.ylabel(r'Blazing criterion $\mu$')
plt.xlabel(r'Incident angle $\alpha$')

## A full numerical simulation of the Fourier plane for an all-on configuration
# alpha = 24/180*np.pi # Incident angle
alpha = blaze_angle
alpha_1D = np.arctan(np.tan(alpha)/np.sqrt(2))
beta = -alpha +2*gamma # reflection angle
alpha_1D = np.arctan(np.tan(alpha)/np.sqrt(2))
beta_1D = 2*gamma_1D-alpha_1D#np.arctan(np.tan(beta)/np.sqrt(2))
N = 20 # number of mirrors in each direction
g = 2 # gap between mirrors in micron
res = 10 # pixels per mirror 
Nx = N*res

## Pixelate image function
f = np.ones([N,N]) # all-on configuration
## Phase slope due to incident and reflection angle
X,Y = np.meshgrid(np.arange(N),np.arange(N))
phi = np.exp((X-Y)*1j*2*np.pi/_lambda*d*(np.sin(alpha_1D)+np.sin(beta_1D))) 

## cell unit
Cell = np.zeros([res,res])
gpix = int(np.round(g/(2.*d)*res))
Cell[gpix:res-gpix,gpix:res-gpix] = 1.
## Mirror image
MI = np.zeros([Nx,Nx],dtype='complex')
for i in range(N):
    for j in range(N):
        MI[i*res:(i+1)*res,j*res:(j+1)*res]= f[i,j]*phi[i,j]*Cell
plt.figure()
plt.imshow(np.real(MI),interpolation = 'None')

## In the Fourier plane
coeff = 5
FP = np.fft.fftshift(np.fft.fft2(MI,s=[coeff*Nx,coeff*Nx]))
ROIsize = 500
ROI = 1
plt.figure()
plt.imshow((np.abs(FP[coeff*Nx//2-ROIsize//2:coeff*Nx//2+ROIsize//2,coeff*Nx//2-ROIsize//2:coeff*Nx//2+ROIsize//2])),interpolation = 'None')
plt.clim([0,(np.max(np.abs(FP)))/1.5])
plt.scatter(ROIsize//2, ROIsize//2, s=200, edgecolors='red',alpha = 0.5,c='yellow',linewidths= 1.,  marker='x')

plt.show()
