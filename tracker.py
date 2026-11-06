import random
import time
import numpy as np
from display import Display
from psychopy import visual, logging, core, monitors, event

class Tracker:

    def __init__(self, tracker, display):
        """
        Initialize a tracker with a Psychopy window

        Parameters:
        tracker (str): Specifies tracker used ("mouse", "eyetracker", "none").
        window (Pyschopy window object): Window used for experiment.
        display (Display object): display for tracker.
        """

        self.display = display 

        # Ensure that tracker is a valid input
        if tracker not in ["mouse", "eyetracker", "none"]:
            raise ValueError('Invalid tracker type. Options: "mouse", "eyetracker", "none".')

        if tracker == "mouse":
            self.tracker = event.Mouse(win = self.display.win)
        elif tracker == "eyetracker":
            #TODO: INCORPORATE EYETRACKER
            pass 


    def touch_shape(self, shape):
        """
        checks for mouse touching shape.
        
        Args:
        shape (Psychopy visual.ShapeStim() object): defines the shape whose boundaries we will
        consider.
        """
        while True:
            tracker_pos = self.tracker.getPos()

            # exit if 'q' is pressed
            if event.getKeys(keyList=["escape", "q"]):
                self.display.win.close()
                core.quit()

            # check if mouse is within square
            if shape.contains(tracker_pos):
                break
            else:
                shape.draw()
            self.display.win.flip()

    def deviation_from_shape(self, shape):
        """
        Checks for deviation from within the shape boundaries.
            
        Args:
        shape (Psychopy visual.ShapeStim() object): defines the shape whose boundaries we will
        consider.

        Returns:
        True if mouse leaves shape boundaries
        False if mouse remains within shape boundaries (indicating no deviation from shape)
        """
        mouse_pos = self.tracker.getPos()
        if not shape.contains(mouse_pos):
            return True #return true for mouse leaving shape
        else:
            return False