#LiveTrackGS.py
# version 2.0 for Python3

# Copyright 2018 Cambridge Research Systems Ltd.
#
# Used to playback video from a connected LiveTrack device. 
#
# Linux
# This library depends on GStreamer 1.8 and above.
#
# Windows 32
# The path below must be listed in the system path environment variable:
# The path C:\Program Files (x86)\Cambridge Research Systems\LiveTrack Viewer x86\ 
#
# Windows 64
# The path below must be listed in the system path environment variable:
# The path C:\Program Files\Cambridge Research Systems\LiveTrack Viewer\ 

import ctypes
import sys

try:
    if sys.platform == 'win32': # if Windows
        print('Using Windows')
        _dll = ctypes.CDLL("C:\\Program Files (x86)\\Cambridge Research Systems\\LiveTrack Viewer x86\\libLiveTrackGS.dll")
    elif sys.platform.startswith('linux'): # if Linux
        print('Using Linux')
        _dll = ctypes.CDLL('/usr/lib/libLiveTrackGS.so')
    elif sys.platform == 'darwin': # if Mac OS X
        print('Using Mac OS X')
        _dll = ctypes.CDLL('/usr/local/lib/libLiveTrackGS.dylib')
    else:
        raise Exception('OS not supported! Must be Windows or Linux.')
except:
    raise Exception('Error loading Library. Please check if the file path is correct')
 
def VideoInit(handle):
    result = _dll.crsLiveTrackVideoInit(ctypes.c_ushort(handle))
    if result==0:
        print('LiveTrackGS: Successfully initialised video device')
    else:
        print('LiveTrackGS: Error initialising video device')
    return result

def VideoStart():
    result = _dll.crsLiveTrackVideoStart()
    if result==0:
        print('LiveTrackGS: Successfully started video playback')
    else:
        print('LiveTrackGS: Error starting video playback')
    return result

def VideoStartRecord(filename):
    namebuf = ctypes.create_string_buffer(filename, 512)
    result = _dll.crsLiveTrackVideoStartRecord(ctypes.byref(namebuf))
    if result==0:
        print('LiveTrackGS: Successfully started video recording')
    else:
        print('LiveTrackGS: Error starting video recording')
    return result

def VideoStopRecord():
    result = _dll.crsLiveTrackVideoStopRecord()
    if result==0:
        print('LiveTrackGS: Successfully stopped video recording')
    else:
        print('LiveTrackGS: Error stoppping video recording')
    return result

def VideoStop():
    result = _dll.crsLiveTrackVideoStop()
    if result==0:
        print('LiveTrackGS: Successfully stopped video playback')
    else:
        print('LiveTrackGS: Error stopping video playback')
    return result

