import sys
import warnings
import numbers
import numpy as np
import time
import math
import os
import json
import copy
import random
import re

from glob import glob


# to test if input objects are valid psychopy classes:
import psychopy
# mouse dummy needs a psychopy.event.mouse object
# calibration requires a psychopy.visual.Window
# and psychopy.visual.*Stim (circleStim?)
from psychopy import core, event, visual, gui, monitors

from psychopy.tools import monitorunittools
from psychopy.tools.coordinatetools import pol2cart, cart2pol
from psychopy.hardware import keyboard
from pyglet.window import key

# import sys, os
# sys.path.append(os.path.join('..', 'EyeTracking'))
# from EyeTracking import EyeTracker



# this file has just 1 object that is needed: EyeTracker
# for now, it can be used as:
# -  from EyeTracker import EyeTracker
# -  myEyeTracker = EyeTracker(tracker='LiveTrack', trackEyes=[True,True], fixationWindow=2, psychopyWindow=cfg['hw']['win'])
# I could set up the folder to work like a proper Python module later where that is taken care of


class EyeTracker:

    def __init__(self, 
                 tracker=None, 
                 trackEyes=[False, False], 
                 fixationWindow=None,
                 minFixDur=None,
                 fixTimeout=None,
                 psychopyWindow=None, 
                 filefolder=None, 
                 filename=None,
                 samplemode=None,
                 calibrationpoints=5,
                 fixationStimuli=None):


        # the functions below check the user input,
        # and store it for future use if OK
        # they can also be used later on to change how the object works
        # and are supposed to be device-agnostic

        self.setPsychopyWindow(psychopyWindow)
        self.setCalibrationpoints(calibrationpoints)
        self.setEyetracker(tracker)
        self.setTrackEyes(trackEyes)
        self.setFixationWindow(fixationWindow)
        self.setMinFixDur(minFixDur)
        self.setFixTimeout(fixTimeout)
        self.setFilePath(filefolder, filename)
        self.setSamplemode(samplemode)
        self.setFixationStimuli(fixationStimuli)

        # things below this comment are still up for change... depends a bit on how the EyeLink does things

        # maybe these should be a property that has a function to set it?
        # it's only used for the LiveTrack, so probably not...
        # self.__calibrationTargets = np.array([[0,0],   [-3,0],[0,3],[3,0],[0,-3],     [6,6],[6,-6],[-6,6],[-6,-6]])
        
        # print(filefolder)
        # print(filename)
        # print(self.storefiles)
        
        self.__fileOpen = False
        self.__recording = False

        self.__N_calibrations = 0
        self.__N_rawdatafiles = 0

        self.__createTargetStim()
        # self.target = self.__createTargetStim


    def setEyetracker(self, tracker):
            if isinstance(tracker, str):
                if tracker in ['livetrack', 'mouse']:

                    if tracker == 'livetrack':
                        # set up the livetrack device here
                        self.setupLiveTrack()

                    if tracker == 'mouse':
                        # not sure what to do here
                        self.setupMouse()

                    self.tracker = tracker
                else:
                    raise Warning("unkown eye-tracker: %s"%(tracker))
            else:
                raise Warning("tracker must be a string")

    def setTrackEyes(self, trackEyes):
        if isinstance(trackEyes, list):
            if len(trackEyes) == 2:
                if all([isinstance(x, bool) for x in trackEyes]):
                    if any(trackEyes):
                        self.trackEyes = trackEyes
                    else:
                        raise Warning("one or both eyes must be tracked")
                else:
                    raise Warning("trackEyes must only contain booleans")
            else:
                raise Warning("trackEyes must have length 2")
        else:
            raise Warning("trackEyes must be a list")
        
    def setFixationWindow(self, fixationWindow):
        if isinstance(fixationWindow, numbers.Number):
            if fixationWindow > 0:
                self.fixationWindow = fixationWindow
            else:
                raise Warning("fixationWindow must be larger than 0")
        else:
            raise Warning("fixationWindow must be a number")
    
    def setMinFixDur(self, minFixDur):
        if isinstance(minFixDur, numbers.Number):
            if minFixDur > 0:
                self.minFixDur = minFixDur
            else:
                raise Warning("minimum fixation duration must be larger than 0")
        else:
            raise Warning("minimum fixation duration must be a number")
        
    def setFixTimeout(self, fixTimeout):
        if isinstance(fixTimeout, numbers.Number):
            if fixTimeout > self.minFixDur:
                self.fixTimeout = fixTimeout
            else:
                raise Warning("fixation timeout must be larger than minimum fixation duration")
        else:
            raise Warning("fixation timeout must be a number")

    def setPsychopyWindow(self, psychopyWindow):
        if isinstance(psychopyWindow, psychopy.visual.Window):
            if psychopyWindow.units == 'deg':
                self.psychopyWindow = psychopyWindow
            else:
                raise Warning("psychopyWindow must have units set to 'deg'")
        else:
            raise Warning("psychopyWindow must be a psychopy Window")
    
    def setFilePath(self, filefolder, filename):
        self.storefiles = False
        self.filefolder = None
        self.filename = None
        if isinstance(filefolder, str):
            if len(filefolder) > 0:
                # check if it is an existing path
                if os.path.isdir(filefolder):
                    if isinstance(filename, str):
                        if len(filename) > 0:

                            # check if target file already exists:
                            if len(glob(os.path.join(filefolder, filename + '.*'))):
                                y = 1
                                while len(glob(os.path.join(filefolder, filename + '_' + str(y) + '.*'))):
                                    y += 1
                                filename = filename + '_' + str(y)
                                print('NOTE: target eye-tracking data file already exists, changing to: '+filename)

                            self.storefiles  = True
                            self.filefolder  = filefolder
                            self.filename    = filename
                        else:
                            print('NOTE: not storing any data since filename is an empty string')
                    else:
                        print('NOTE: not storing any data since filename is not a string')
                else:
                    raise Warning("filefolder is not a valid or existing path: %s"%(filefolder))
            else:
                print('NOTE: not storing any files since filefolder is an empty string')
        else:
            print('NOTE: not storing any files since filefolder is not a string')
    
    def setSamplemode(self, samplemode):
        if isinstance(samplemode, str):
            if samplemode in ['both', 'left', 'right', 'average']:
                self.samplemode = samplemode
            else:
                raise Warning("unkown samplemode: %s"%(samplemode))
        else:
            raise Warning("samplemode must be a string")
    
    def setCalibrationpoints(self, calibrationpoints):
        if isinstance(calibrationpoints, numbers.Number):
            if calibrationpoints in [5,9]:
                # allowed number of points?
                self.calibrationpoints = calibrationpoints
                if calibrationpoints == 5:
                    self.calibrationTargets = np.array([[0,0],   [-3,0],[0,3],[3,0],[0,-3]                                 ])
                    # self.__calibrationTargets = np.array([[0,0],   [-10.437,0],[0,5.916],[10.437,0],[0,-5.916]                                 ])
                if calibrationpoints == 9:
                    self.calibrationTargets = np.array([[0,0],   [-3,0],[0,3],[3,0],[0,-3],     [6,6],[6,-6],[-6,6],[-6,-6]])
                    # self.__calibrationTargets = np.array([[0,0],   [-10.437,0],[0,5.916],[10.437,0],[0,-5.916],     [2*10.437,2*5.916],[2*10.437,-2*5.916],[-2*10.437,2*5.916],[-2*10.437,-2*5.916]  ])
                # print(self.__calibrationTargets)
            else:
                raise Warning("calibration points must be 5 (default) or 9")
        else:
            raise Warning("calibration points must be a number")
    
    def setFixationStimuli(self, fixationStimuli):
        if not fixationStimuli == None:
            # make sur eit's a list:
            if not isinstance(fixationStimuli, list):
                fixationStimuli = [fixationStimuli]
            for stim in fixationStimuli:
                if hasattr(stim, 'draw'): 
                    if callable(stim.draw):
                        if stim.win == self.psychopyWindow:
                            # seems good?
                            pass
                        else:
                            raise Warning("fixationStimuli must be defined for 'psychopyWindow'")
                    else:
                        raise Warning("fixationStimuli.draw must be callable")
                else:
                    raise Warning("fixationStimuli must have a draw property")
            # all good, store them:
            self.fixationStimuli = fixationStimuli
        else:
            pass # it's fine not to specify any
    
    def setupLiveTrack(self):
        import LiveTrack
        import LiveTrackGS
        self.LiveTrack = LiveTrack
        self.LiveTrackGS = LiveTrackGS

        # remap functions:
        self.initialize = self.__LT_initialize
        self.calibrate  = self.__LT_calibrate
        self.savecalibration = self.__LT_savecalibration

        self.lastsample = self.__LT_lastsample

        self.openfile = self.__LT_openfile
        self.startcollecting = self.__LT_startcollecting
        self.stopcollecting = self.__LT_stopcollecting
        self.closefile = self.__LT_closefile

        self.comment = self.__LT_comment
        self.shutdown = self.__LT_shutdown
        # ...
        # here we map other functions
        # ...

    def setupMouse(self):
        # this will be a psychopy mouse object
        # import numpy as np
        # self.__np = np

        # remap functions:
        self.initialize = self.__DM_initialize
        # self.calibrate  = self.__DM_calibrate
        # self.savecalibration = self.__DM_savecalibration

        # self.lastsample = self.__DM_lastsample

        # self.openfile = self.__DM_openfile
        # self.startcollecting = self.__DM_startcollecting
        # self.stopcollecting = self.__DM_stopcollecting
        # self.closefile = self.__DM_closefile

        # self.comment = self.__DM_comment
        # self.shutdown = self.__DM_shutdown
        # ...
        # here we map other functions
        # ...

    def __LT_initialize(self, calibrationPoints=None):
        print('initialize LiveTrack')
        self.LiveTrack.Init()

        self.LiveTrackGS.VideoInit(0)
        self.LiveTrackGS.VideoStart()
        print("display screen")

        # Start LiveTrack using raw data (camera coords)
        self.LiveTrack.SetResultsTypeRaw()

        # Start buffering data
        self.LiveTrack.StartTracking()
        self.LiveTrack.SetTracking(leftEye=self.trackEyes[0],rightEye=self.trackEyes[1])

        # what's this for?
        [ width, height, sampleRate, offsetX, offsetY ] = self.LiveTrack.GetCaptureConfig()
        self.__LiveTrackConfig = { 'width'      : width,
                                'height'     : height,
                                'sampleRate' : sampleRate,
                                'offsetX'    : offsetX,
                                'offsetY'    : offsetY      }

        # these checks can be much simpler! but leave it be for now...
        if isinstance(calibrationPoints, np.ndarray):
            if len(calibrationPoints) >= 3:
                if all([isinstance(x, np.ndarray) and len(x) == 2 for x in calibrationPoints]):
                    if all([len(x) == 2 for x in calibrationPoints]):
                        if all([all([isinstance(y, numbers.Number) for y in x]) for x in calibrationPoints]):
                            # seems more or less OK?
                            self.calibrationTargets = calibrationPoints
                        else:
                            raise Warning("all elements in calibrationPoints must be numeric")
                    else:
                        raise Warning("all rows in calibrationPoints must have 2 items")
                else:
                    raise Warning("all rows in calibrationPoints must be numpy.ndarray")
            else:
                raise Warning("calibrationPoints must have at least 3 rows")
        else:
            if calibrationPoints == None:
                return
            else:
                raise Warning("calibrationPoints must be a numpy.ndarray")
    
    def __DM_initialize(self):
        print('initialize dummy mouse tracker')
        self.__mousetracker = event.Mouse( visible = True,
                                           newPos = None,                    # what does this even do?
                                           win = self.psychopyWindow )
    
    def __LT_calibrate(self):
        print('calibrate livetrack')

        calTargets = copy.deepcopy(self.calibrationTargets)

        # print(self.calibrationpoints)

        # midTarget = calTargets[0]
        # extTargets = calTargets[1:]

        # np.random.shuffle(extTargets)

        # calTargets = [midTarget].append(extTargets).append(midTarget)

        # ntargets = len(calTargets)

        mididx = list(range(1,len(calTargets)))
        random.shuffle(mididx)
        allidx = [0] + mididx + [0]
        ntargets = len(allidx)


        # configure calibration:
        setupDelay = 1000.0 # time before collecting any samples in ms
        minDur = 300 # min fixation duration in ms
        fixTimeout = 5  # timeout duration in seconds (point is skipped!)
        fixThreshold = 5 # pixel window for all samples within a 'fixation'

        # ntargets = np.shape(self.__calibrationTargets)[0]
        # tgtLocs = self.__calibrationTargets.astype(float) 
        tgtLocs = copy.deepcopy(self.calibrationTargets)
        tgtLocs = tgtLocs[allidx,:]
        tgtLocs = tgtLocs.astype(float) # make sure locations are floats

        # show calibration on separate video window (not necessary):
        # if self.useVideo:
        #     print('Please align camera')
        #     import LiveTrackGS
        #     LiveTrackGS.VideoInit(0)
        #     result= LiveTrackGS.VideoStart()
        #     time.sleep(5)

        # initialise LiveTrack
        # LiveTrack.Init() # already done



        self.LiveTrack.SetResultsTypeRaw() # stream raw data
        # self.LiveTrack.StartTracking() # buffer data to lib
        [ width, height, sampleRate, offsetX, offsetY ] = self.LiveTrack.GetCaptureConfig() # estimate sample rate
        fixDurSamples = round((float(minDur)/1000)*float(sampleRate)) # samples per fixation duration

        self.LiveTrack.SetTracking(self.trackEyes[0], self.trackEyes[1]) # make sure we're only tracking the requires eyes
        # print(self.LiveTrack.GetTracking()) # see what's being tracked

        if self.trackEyes[0]:
            VectXL = [None] * ntargets
            VectYL = [None] * ntargets
            GlintXL = [None] * ntargets
            GlintYL = [None] * ntargets
        if self.trackEyes[1]:
            VectXR = [None] * ntargets
            VectYR = [None] * ntargets
            GlintXR = [None] * ntargets
            GlintYR = [None] * ntargets

        visual.TextStim(self.psychopyWindow,'calibration', height = 1,wrapWidth=30, color = 'black').draw()
        self.psychopyWindow.flip()
        time.sleep(0.3333) # is this necessary? well, we just show this briefly, so the participant knows what's going to happen

        for target_idx in range(ntargets):
            # plot a circle at the fixation position.
            # self.cal_dot_o.pos = self.calibrationTargets[target_idx,:]
            # self.cal_dot_o.draw()
            # self.cal_dot_i.pos = self.calibrationTargets[target_idx,:]
            # self.cal_dot_i.draw()

            targetpos = tgtLocs[target_idx]

            self.target.pos = targetpos
            self.target.draw()

            self.psychopyWindow.flip()

            # This flag will be set to true when a valid fixation has been acquired
            gotFixLeft = 0  
            gotFixRight = 0
            
            t0 = time.time() # reset fixation timer 
        
            # Loop until fixation data has been aquired for this dot (or timed out) 
            while 1:
                d = self.LiveTrack.GetBufferedEyePositions(0,fixDurSamples,0)


                if self.trackEyes[0]:

                    VectX = self.LiveTrack.GetFieldAsList(d,'VectX')
                    VectY = self.LiveTrack.GetFieldAsList(d,'VectY')
                    GlintX = self.LiveTrack.GetFieldAsList(d,'GlintX')
                    GlintY = self.LiveTrack.GetFieldAsList(d,'GlintY')
                    Tracked = self.LiveTrack.GetFieldAsList(d,'Tracked')

                    # Calculate the maximum difference in the pupil-to-glint 
                    # vectors for the samples in the buffer, for left eye
                    pgDistL = max([max(VectX)-min(VectX),max(VectY)-min(VectY)])

                    # Check if the maximum vector difference is within the defined
                    # limit for a fixation (fixWindow) and all samples ajsone tracked, and
                    # the time to wait for fixations (waitTimeForFix) has passed, for
                    # the left eye
                    if pgDistL<=fixThreshold and np.all(Tracked) and (time.time()-t0)>setupDelay/1000:
                        # Check if there are enough samples in the buffer for the
                        # defined duration (fixDurSamples)
                        if len(d)>=fixDurSamples and gotFixLeft==0:
                            print(pgDistL)
                            # save the data for this fixation
                            VectXL[target_idx] = np.median(VectX)
                            VectYL[target_idx] = np.median(VectY)
                            GlintXL[target_idx] = np.median(GlintX)
                            GlintYL[target_idx] = np.median(GlintY)
                            print('Fixation #',str(target_idx+1),str(targetpos),': Found valid fixation for left eye')
                            gotFixLeft = 1 # good fixation aquired
                
                if self.trackEyes[1]:
                    VectXRight = self.LiveTrack.GetFieldAsList(d,'VectXRight')
                    VectYRight = self.LiveTrack.GetFieldAsList(d,'VectYRight')
                    GlintXRight = self.LiveTrack.GetFieldAsList(d,'GlintXRight')
                    GlintYRight = self.LiveTrack.GetFieldAsList(d,'GlintYRight')
                    TrackedRight = self.LiveTrack.GetFieldAsList(d,'TrackedRight')
                
                    # and for the right eye
                    pgDistR = max([max(VectXRight)-min(VectXRight),max(VectYRight)-min(VectYRight)])


                    # and for the right eye
                    if pgDistR<=fixThreshold and np.all(TrackedRight) and (time.time()-t0)>setupDelay/1000:
                        # Check if there are enough samples in the buffer for the
                        # defined duration (fixDurSamples)
                        if  len(d)>=fixDurSamples and gotFixRight==0:
                            # save the data for this fixation
                            VectXR[target_idx] = np.median(VectXRight)
                            VectYR[target_idx] = np.median(VectYRight)
                            GlintXR[target_idx] = np.median(GlintXRight)
                            GlintYR[target_idx] = np.median(GlintYRight)
                            print('Fixation #',str(target_idx+1),str(targetpos),': Found valid fixation for right eye')
                            gotFixRight = 1 # good fixation aquired
                

                if (time.time()-t0)>fixTimeout:
                    if not gotFixLeft and self.trackEyes[0]>0:
                        print('Fixation #',str(target_idx+1),str(targetpos),': Did not get fixation for left eye (timeout)')
                    if not gotFixRight and self.trackEyes[1]>0:
                        print('Fixation #',str(target_idx+1),str(targetpos),': Did not get fixation for right eye (timeout)')
                    break # fixation timed out

                
                # Exit if all eyes that are enabled have got a fixation
                if (gotFixLeft or self.trackEyes[0]==False) and (gotFixRight or self.trackEyes[1]==False):
                    self.psychopyWindow.flip()
                    break

        # Stop buffering data to the library
        ######################################################### NOT SURE ABOUT THIS:

        # self.LiveTrack.StopTracking()

        # Clear the data in the buffer
        self.LiveTrack.ClearDataBuffer()


        viewDist = self.psychopyWindow.monitor.getDistance()

        redoCalibration = False

        # %% remove failed fixations from data

        if self.trackEyes[0]:
            # left eye
            failedFixL = []
            for i in range(0,len(VectXL)):
                if VectXL[i] is None:
                    failedFixL.append(i)
            
            # %% remove failed fixations from data
            VectXL = np.delete(VectXL, failedFixL).tolist()
            VectYL = np.delete(VectYL, failedFixL).tolist()
            GlintXL = np.delete(GlintXL, failedFixL).tolist()
            GlintYL = np.delete(GlintYL, failedFixL).tolist()
            tgtLocsXL = np.delete(tgtLocs[:,0], failedFixL).tolist()
            tgtLocsYL = np.delete(tgtLocs[:,1], failedFixL).tolist()

            if len(tgtLocsXL) < 2:
                print('left eye calibration fewer than 3 good points: redoing calibration')
                redoCalibration = True
            else:
                # %% send fixation data to LiveTrack to calibrate
                calErrL = self.LiveTrack.CalibrateDevice(0, len(tgtLocsXL), tgtLocsXL, tgtLocsYL, VectXL, VectYL, viewDist, np.median(GlintXL), np.median(GlintYL))
                print('Left eye calibration accuracy: ',str(math.sqrt(float(calErrL)/len(tgtLocsXL))), 'errors in dva')


        if self.trackEyes[1]:
            # right eye
            failedFixR = []
            for i in range(0,len(VectXR)):
                if VectXR[i] is None:
                    failedFixR.append(i)

            # %% remove failed fixations from data
            VectXR = np.delete(VectXR, failedFixR).tolist()
            VectYR = np.delete(VectYR, failedFixR).tolist()
            GlintXR = np.delete(GlintXR, failedFixR).tolist()
            GlintYR = np.delete(GlintYR, failedFixR).tolist()
            tgtLocsXR = np.delete(tgtLocs[:,0], failedFixR).tolist()
            tgtLocsYR = np.delete(tgtLocs[:,1], failedFixR).tolist()
            
            if len(tgtLocsXR) < 2:
                print('right eye calibration fewer than 3 good points: redoing calibration')
                redoCalibration = True
            else:
                calErrR = self.LiveTrack.CalibrateDevice(1, len(tgtLocsXR), tgtLocsXR, tgtLocsYR, VectXR, VectYR, viewDist, np.median(GlintXR), np.median(GlintYR))
                print('Right eye calibration accuraccy: ',str(math.sqrt(float(calErrR)/len(tgtLocsXR))), 'errors in dva')
        

        if redoCalibration:

            # redo_text = visual.TextStim(win = self.psychopyWindow,
            #                            'not enough fixations detected\n\nadjust eye-tracker?\n\n    press  [ SPACE ]\nto redo calibration')
            while True:
                visual.TextStim(self.psychopyWindow,'not enough fixations detected\n\nadjust eye-tracker?\n\n    press  [ SPACE ]\nto redo calibration', height = 1,wrapWidth=30, color = 'black').draw()
            # redo_text.draw()
                self.psychopyWindow.flip()
                keys = event.waitKeys(keyList=['space', 'q'])
    
                # If the spacebar or 'q' is pressed, break out of the loop
                if keys and 'space' in keys:
                    break
                elif keys and 'q' in keys:
                    print("Exiting experiment")
                    self.psychopyWindow.close()
                    self.shutdown()
                    core.quit()
                    
            # k=[]
            # while k[0] not in ['q','space']:
            k = event.waitKeys()
            event.clearEvents(eventType='keyboard')
            self.__LT_calibrate()
            
        else:

            # %% plot the estimated fixation locations for the calibration
            #if trackLeftEye:
            #    [gazeXL, gazeYL] = LiveTrack.CalcGaze(0, len(tgtLocsXL), VectXL, VectYL)
            #
            #if trackRightEye:
            #    [gazeXR, gazeYR] = LiveTrack.CalcGaze(1, len(tgtLocsXR), VectXR, VectYR)
            # errors are added?
            # gazeXL = [x+10 for x in tgtLocsXL]
            # gazeYL = [x+10 for x in tgtLocsYL]
            # gazeXR = [x-10 for x in tgtLocsXR]
            # gazeYR = [x-10 for x in tgtLocsYR]
            
            # if useVideo:
            #     self.LiveTrackGS.VideoStop()

            self.LiveTrack.SetResultsTypeCalibrated()
            # self.LiveTrack.StartTracking()

            if self.storefiles:
                
                cal_files = glob( os.path.join(self.filefolder, 'calibration_*.json' ) )
                if len(cal_files):
                    idx = np.max([int(os.path.splitext(os.path.basename(x))[0].split('_')[1]) for x in cal_files]) + 1
                else:
                    idx = 1

                self.__N_calibrations = idx
                self.comment('calibration %d'%(self.__N_calibrations))

                self.savecalibration()

    def recalibrate(self):
        print("\nRecalibrating. When participant agrees they are ready, press [space] to begin recalibration.\n")
        while True:
            recalibrate_text = "You are initiating recalibration. If you are ready to begin, press the spacebar. Press 'q' to exit the experiment"
            visual.TextStim(self.psychopyWindow, text=recalibrate_text, color='black').draw()
            self.psychopyWindow.flip()
            keys = event.waitKeys(keyList=['space', 'q'])

            # If the spacebar or 'q' is pressed, break out of the loop
            if keys and 'space' in keys:
                break
            elif keys and 'q' in keys:
                print("Exiting experiment")
                self.psychopyWindow.close()
                self.shutdown()
                core.quit()
        self.calibrate()


    
    def __LT_savecalibration(self):

        # collect calibration info in a dictionary:
        calibrations = {}
        if self.trackEyes[0]:
            calibrations['left']  = self.LiveTrack.GetCalibration(eye=0)
        if self.trackEyes[1]:
            calibrations['right'] = self.LiveTrack.GetCalibration(eye=1)

        # write calibration info to a json file:
        filename = '%s/calibration_%s.json'%(self.filefolder, self.__N_calibrations)
        out_file = open(filename, "w")
        json.dump( calibrations,
                   fp=out_file,
                   indent=4)
        out_file.close()


    def __LT_openfile(self):
        
        # maybe this should also be done at the level of the whole session?
        # yes!

        if self.__fileOpen:
            self.closefile()
            print('note: closed open file before opening a new file')

        # filename = self.saneFilename(self.filename, ext='.csv')


        print(os.path.join(self.filefolder,self.filename)+'.csv')
        self.LiveTrack.SetDataFilename(os.path.join(self.filefolder,self.filename)+'.csv')

        self.__fileOpen = True
        self.__N_rawdatafiles += 1
    
    def __LT_startcollecting(self):
        self.LiveTrack.StartTracking()
        

    def __LT_stopcollecting(self):
        self.LiveTrack.StopTracking()

    def __LT_closefile(self):
        if self.__fileOpen:
            self.LiveTrack.CloseDataFile()
            self.__fileOpen = False
        else:
            print('no file to close, moving on')
    
    def __LT_lastsample(self):
        # data = LiveTrack.GetBufferedEyePositions(0,fixDurSamples,0) # this would get the last x samples, given by the second argument
        data = self.LiveTrack.GetLastResult() # gets only the very last sample

        # this needs to be formatted in some standard way that is the same for all eye-tracker devices
        sample = {}
        if self.samplemode in ['both','left','average']:
            if self.trackEyes[0]:
                if data.Tracked:
                    sample['left'] = np.array([data.GazeX, data.GazeY])
                else:
                    sample['left'] = np.array([np.NaN, np.NaN])
        if self.samplemode in ['both','right','average']:
            if self.trackEyes[1]:
                if data.TrackedRight:
                    sample['right'] = np.array([data.GazeXRight, data.GazeYRight])
                else:
                    sample['right'] = np.array([np.NaN, np.NaN])

        if self.samplemode == 'average':
            X = []
            Y = []
            # skip NAN values? 
            if data.Tracked:
                X.append(sample['left'][0])
                Y.append(sample['left'][1])
            if data.TrackedRight:
                X.append(sample['right'][0])
                Y.append(sample['right'][1])
            if (any([data.Tracked, data.TrackedRight])):
                sample['average'] = np.array([np.mean(X), np.mean(Y)])

        return(sample)
    
    def gazeInFixationWindow(self):

        sample = self.lastsample()
        check_samples = self.getSamplesToCheck()
        
        for cs in check_samples: # skipping irrelevant sample types
            if cs in sample.keys():
                if any(np.isnan(sample[cs])):
                    return(False) # return False if there is a nan value
                d = np.sqrt(np.sum(np.array(sample[cs])**2))
                if d > self.fixationWindow:
                    return(False) # return false if the distance from fixation is larger than 2 (or whatever the fixation window is)
            else:
                return(False) # return false if any of the samples that need to be checked are not in the data

        return(True) # should only get here if all samples exist, are not nans, and are within the fixation window
    
    def getSamplesToCheck(self):

        return( {'both':['left','right'],
                 'left':['left'],
                 'right':['right'],
                 'average':['average']}[self.samplemode] )
    
    def waitForFixation(self, minFixDur=None, fixTimeout=None, fixationStimuli=None):

        if minFixDur == None:
            minFixDur = self.minFixDur
        if fixTimeout == None:
            fixTimeout = self.fixTimeout

        if fixationStimuli == None:
            if hasattr(self, 'fixationStimuli'):
                fixationStimuli = self.fixationStimuli
            else:
                self.target.pos = [0,0]
                fixationStimuli = [self.target]
        else:
            if not isinstance(fixationStimuli, list):
                fixationStimuli = [fixationStimuli]
        

        # most the initially set values should be used, but we do 1 sanity check here:
        # if the initially set values are used, this should already be true:
        if fixTimeout < minFixDur:
            raise Warning("fixation timeout should be longer than minimum fixation duration")

        starttime = time.time()
        timeout = starttime + fixTimeout
        now = starttime

        fixationStart = None
        fixation_text = visual.TextStim(self.psychopyWindow, text="Please fixate on the square.", pos=(0, 2), color='white')

        while now < timeout:

            for stim in fixationStimuli:
                stim.draw()
            fixation_text.draw()
            self.psychopyWindow.flip()

            now = time.time()

            fixated = self.gazeInFixationWindow()

            if fixated:
                if fixationStart == None:
                    fixationStart = now
                else:
                    if (now - fixationStart) >= minFixDur:
                        return True
            else:
                fixationStart = None
        
        return False

    def __LT_comment(self, comment):

        if self.__fileOpen:
            self.LiveTrack.SetDataComment(comment)
            time.sleep(1.5/self.__LiveTrackConfig['sampleRate'])
        # the experiment sleeps for 1.5 eye-tracker samples
        # this ensures actually storing the comment
        # and doesn't get overwritten by the next comment... at the same sample (shouldn't send comments that quickly?)
        # and we might skip 1 sample, but that will be less than 1 frame
    
    def __LT_shutdown(self):
        self.stopcollecting()
        print("stopped collecting")
        self.closefile()
        self.LiveTrack.Close()
        print("closed livetrack")
        self.LiveTrackGS.VideoStop()
        print("shutdown video")
        

    def __createTargetStim(self):
        
        # should these be accessible / changeble by the user?
        fixDotInDeg  = 0.2 # inner circle
        fixDotOutDeg = 1.0
        
        # self.target = visual.TargetStim(self.psychopyWindow, 
        #                                 name='fixTarget',
        #                                 radius=fixDotOutDeg/2, 
        #                                 innerRadius=fixDotInDeg/2, 
        #                                 fillColor=[-1,-1,-1], 
        #                                 innerFillColor=[1,1,1], 
        #                                 lineWidth=0, 
        #                                 innerLineWidth=0, 
        #                                 borderColor=None, 
        #                                 innerBorderColor=None,
        #                                 units='deg')
        # self.target = visual.Circle(self.psychopyWindow, 
        #                name='fixTarget',
        #                radius=fixDotOutDeg, 
        #                fillColor=[-1,-1,-1], 
        #                units='deg', 
        #                lineWidth=0)

        self.target = visual.Rect(self.psychopyWindow, 
                          width=0.2,          # Width of the square
                          height=0.2,         # Height of the square (same as width for a square)
                          fillColor=[1, 1, 1],  # Black color, using RGB (-1,-1,-1) for black, [1,1,1] for white
                          lineColor="black",      # No border
                          units='deg')


