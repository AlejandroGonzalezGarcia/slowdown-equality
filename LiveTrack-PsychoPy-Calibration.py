# LiveTrack-PsychoPy-Calibration.py
# version 1.0
# 05/2018 JT
# 05/2019 RJL Updated for Python3

import LiveTrack
import numpy as np
import math
import time
from psychopy import visual, core

# This script calibrated LiveTrack using PsychoPy. After Calibration the results 
# will be in screen pixels with origin at the centre of the screen
# %% User Input

viewDist = 576 # viewing distance in mm

# Define the defualt location of the the fixation targets in degrees
# (origin at the centre, x-positive=right, y-positive=down)
targetsDeg = np.array([[-10,-10],[0,-10],[10,-10],[-10,0],[0,0],[10,0],[-10,10],[0,10],[10,10]])

# Define screen resolution
screenRes = [1920,1080]

# Define screen size in mm
screenSize = [530,293]

# Time before getting data from fixation (to ignore initial saccade)
setupDelay = 1000.0 # duration in mS

# Define the minimum amount of time required for each fixation (in mS) - 
# decrease to make calibration "easier"/faster
minDur = 1200 # fixation duration in mS

# Time limit for aquiring fixation - if a fixation has not been aquired 
# within this time, the fixation point will be skipped.
fixTimeout = 5  # timeout duration in seconds

# Fixation threshold in camera pixels (all samples taken wihtin the "minDur"
# time must be within this threshold) - increase this to make the  
# calibration "easier" (e.g. for subjects with difficulties making precise
# eye fixations)
fixThreshold = 3.1

# Define the diameter of the fixation points (in degrees of visual angle)
fixDotInDeg = 0.3 # inner circle
fixDotOutDeg = 0.6 # outer circle

# Randomize the order of the targets:
s = np.shape(targetsDeg)
order = np.arange(s[0])
np.random.shuffle(order)
targetsDeg2 = targetsDeg.astype(float)
for x in range(0,s[0]):
    targetsDeg2[x] = targetsDeg[order[x]]

# Calculate pixel size (in mm) assuming square pixels
pixSize = float(screenSize[0])/float(screenRes[0])

# Caliculate millimetres per degree (NB. Only accurate for small eye angles)
MMperDeg = math.tan(1/(180/math.pi))*viewDist

# Calculate pixels per degree
pixPerDeg = MMperDeg/pixSize

# Target locations in screen pixel coordinates
cnrTarget = [0,0]
tgtLocs = targetsDeg2.astype(float)
tgtLocs[:,0] = np.round(targetsDeg2[:,0]*pixPerDeg+cnrTarget[0])
tgtLocs[:,1] = np.round(targetsDeg2[:,1]*pixPerDeg+cnrTarget[1])

# Calculate the diameter of the fixation points (in pixels on the monitor)
fixDotInPix = fixDotInDeg*pixPerDeg
fixDotOutPix = fixDotOutDeg*pixPerDeg


# Start LiveTrack raw data streaming
LiveTrack.SetResultsTypeRaw()

# Start buffering data to the library
LiveTrack.StartTracking()

# Get an estimate of the sample rate
[ width, height, sampleRate, offsetX, offsetY ] = LiveTrack.GetCaptureConfig()

# Calculate how many data samples the fixation duration (fixDur) contains
fixDurSamples = round((float(minDur)/1000)*float(sampleRate))

# Find out which eye to get fixation data from
[trackLeftEye, trackRightEye] = LiveTrack.GetTracking()

# %% 

win = visual.Window(monitor='testMonitor', size=[1920, 1080], units="pix", fullscr=True, screen=1)

VectXL = [None] * s[0]
VectYL = [None] * s[0]
GlintXL = [None] * s[0]
GlintYL = [None] * s[0]
VectXR = [None] * s[0]
VectYR = [None] * s[0]
GlintXR = [None] * s[0]
GlintYR = [None] * s[0]

for i in range(0,s[0]):
    # plot a circle at the fixation position.
    dot = visual.Circle(win,units='pix',radius=fixDotOutPix/2,fillColor=[-1] * 3,lineColor=[-1] * 3,pos=[tgtLocs[i,0],tgtLocs[i,1]]) # outer circle
    dot.draw()
    dot = visual.Circle(win,units='pix',radius=fixDotInPix/2,fillColor=[1] * 3,lineColor=[-1] * 3,pos=[tgtLocs[i,0],tgtLocs[i,1]]) # inner circle
    dot.draw()
    win.flip()

    # This flag will be set to true when a valid fixation has been acquired
    gotFixLeft = 0  
    gotFixRight = 0
    
    t0 = time.time() # reset fixation timer 
 
    # Loop until fixation data has been aquired for this dot (or timed out) 
    while 1:
        d = LiveTrack.GetBufferedEyePositions(0,fixDurSamples,0)
        VectX = LiveTrack.GetFieldAsList(d,'VectX')
        VectY = LiveTrack.GetFieldAsList(d,'VectY')
        GlintX = LiveTrack.GetFieldAsList(d,'GlintX')
        GlintY = LiveTrack.GetFieldAsList(d,'GlintY')
        Tracked = LiveTrack.GetFieldAsList(d,'Tracked')
        VectXRight = LiveTrack.GetFieldAsList(d,'VectXRight')
        VectYRight = LiveTrack.GetFieldAsList(d,'VectYRight')
        GlintXRight = LiveTrack.GetFieldAsList(d,'GlintXRight')
        GlintYRight = LiveTrack.GetFieldAsList(d,'GlintYRight')
        TrackedRight = LiveTrack.GetFieldAsList(d,'TrackedRight')
        
        # Calculate the maximum difference in the pupil-to-glint 
        # vectors for the samples in the buffer, for left eye
        pgDistL = max([max(VectX)-min(VectX),max(VectY)-min(VectY)])

        # and for the right eye
        pgDistR = max([max(VectXRight)-min(VectXRight),max(VectYRight)-min(VectYRight)])

        # Check if the maximum vector difference is within the defined
        # limit for a fixation (fixWindow) and all samples are tracked, and
        # the time to wait for fixations (waitTimeForFix) has passed, for
        # the left eye
        if pgDistL<=fixThreshold and np.all(Tracked) and (time.time()-t0)>setupDelay/1000:
            # Check if there are enough samples in the buffer for the
            # defined duration (fixDurSamples)
            if len(d)>=fixDurSamples and gotFixLeft==0:
                # save the data for this fixation
                VectXL[i] = np.median(VectX)
                VectYL[i] = np.median(VectY)
                GlintXL[i] = np.median(GlintX)
                GlintYL[i] = np.median(GlintY)
                print('Fixation #',str(i+1),': Found valid fixation for left eye')
                gotFixLeft = 1 # good fixation aquired

        # and for the right eye
        if pgDistR<=fixThreshold and np.all(TrackedRight) and (time.time()-t0)>setupDelay/1000:
            # Check if there are enough samples in the buffer for the
            # defined duration (fixDurSamples)
            if  len(d)>=fixDurSamples and gotFixRight==0:
                # save the data for this fixation
                VectXR[i] = np.median(VectXRight)
                VectYR[i] = np.median(VectYRight)
                GlintXR[i] = np.median(GlintXRight)
                GlintYR[i] = np.median(GlintYRight)
                print('Fixation #',str(i+1),': Found valid fixation for right eye')
                gotFixRight = 1 # good fixation aquired
        
        if (time.time()-t0)>fixTimeout:
            if not gotFixLeft and trackLeftEye>0:
                print('Fixation #',str(i+1),': Did not get fixation for left eye (timeout)')
            if not gotFixRight and trackRightEye>0:
                print('Fixation #',str(i+1),': Did not get fixation for right eye (timeout)')
            break # fixation timed out

        
        # Exit if all eyes that are enabled have got a fixation
        if (gotFixLeft or trackLeftEye==False) and (gotFixRight or trackRightEye==False):
            win.flip()
            break


# Stop buffering data to the library
LiveTrack.StopTracking()

# Clear the data in the buffer
LiveTrack.ClearDataBuffer()


# %% remove failed fixations from data

# left eye
failedFixL = []
for i in range(0,len(VectXL)):
    if VectXL[i] is None:
        failedFixL.append(i)

VectXL = np.delete(VectXL, failedFixL).tolist()
VectYL = np.delete(VectYL, failedFixL).tolist()
GlintXL = np.delete(GlintXL, failedFixL).tolist()
GlintYL = np.delete(GlintYL, failedFixL).tolist()
tgtLocsXL = np.delete(tgtLocs[:,0], failedFixL).tolist()
tgtLocsYL = np.delete(tgtLocs[:,1], failedFixL).tolist()

# right eye
failedFixR = []
for i in range(0,len(VectXR)):
    if VectXR[i] is None:
        failedFixR.append(i)

VectXR = np.delete(VectXR, failedFixR).tolist()
VectYR = np.delete(VectYR, failedFixR).tolist()
GlintXR = np.delete(GlintXR, failedFixR).tolist()
GlintYR = np.delete(GlintYR, failedFixR).tolist()
tgtLocsXR = np.delete(tgtLocs[:,0], failedFixR).tolist()
tgtLocsYR = np.delete(tgtLocs[:,1], failedFixR).tolist()

# %% send fixation data to LiveTrack to calibrate

if trackLeftEye:
    calErrL = LiveTrack.CalibrateDevice(0, len(tgtLocsXL), tgtLocsXL, tgtLocsYL, VectXL, VectYL, viewDist, np.median(GlintXL), np.median(GlintYL))
    print('Left eye calibration accuraccy: ',str(math.sqrt(float(calErrL)/len(tgtLocsXL))), 'pixels')
    print('Left eye calibration accuraccy: ',str(math.sqrt(float(calErrL)/len(tgtLocsXL))/pixPerDeg), 'degrees of visual angle')

if trackRightEye:
    calErrR = LiveTrack.CalibrateDevice(1, len(tgtLocsXR), tgtLocsXR, tgtLocsYR, VectXR, VectYR, viewDist, np.median(GlintXR), np.median(GlintYR))
    print('Left eye calibration accuraccy: ',str(math.sqrt(float(calErrR)/len(tgtLocsXR))), 'pixels')
    print('Left eye calibration accuraccy: ',str(math.sqrt(float(calErrR)/len(tgtLocsXR))/pixPerDeg), 'degrees of visual angle')

    
gazeXL = [x+10 for x in tgtLocsXL]
gazeYL = [x+10 for x in tgtLocsYL]
gazeXR = [x-10 for x in tgtLocsXR]
gazeYR = [x-10 for x in tgtLocsYR]
