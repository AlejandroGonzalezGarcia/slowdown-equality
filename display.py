import math
import numpy as np
from models import Trial
from EyeTracking import EyeTracker
import utilities
import time
import random
from psychopy import visual, logging, core, monitors, event

class Display:
    def __init__(self,
                 monitor,
                 screen_width,
                 screen_resolution,
                 viewing_distance,
                 window_size,
                 screen_index,
                 line_width = 0.13,
                 square_coords = [(0.10, 0.10), (0.10, -0.10), (-0.10, -0.10), (-0.10, 0.10)]
                 ):
        """
        Initializes display.

        Parameters:
        win (visual.Window object): Window used for experiment.
        screen_width (float): Screen width in cm.
        screen_resolution (int array): Array of length 2 specifying monitor
            resolution [width, height] in pixels.
        viewing_distance (float): Participant distance from screen in cm.
        win (Psychopy visual.Window Object): Window used to display experiment
        """

        self.monitor = monitor
        self.screen_width = screen_width
        self.screen_resolution = screen_resolution
        self.viewing_distance = viewing_distance
        self.line_width = line_width
        self.square_coords = square_coords
        self.screen_index = screen_index

        # Initialize window
        # if window_size != "full":
        #     full = False
        # else:
        #     full = True
        # self.win = visual.Window(
        #     size = window_size,
        #     units = "deg",
        #     fullscr=True,
        #     monitor = self.monitor,
        #     screen=1,
        #     color = [127,127,127],
        #     colorSpace = 'rgb255'
        # )

        if window_size == "full":
            self.win = visual.Window(
                size = screen_resolution,
                units = "deg",
                fullscr=True,
                monitor = self.monitor,
                screen=self.screen_index,
                color = [127,127,127],
                colorSpace = 'rgb255'
        )
        else:
            self.win = visual.Window(
            size = window_size,
            units = "deg",
            fullscr=False,
            monitor = self.monitor,
            screen=1,
            color = [127,127,127],
            colorSpace = 'rgb255'
        )
        self.win.mouseVisible = False

        # Initialize middle line
        line_y = self.pixels_to_degrees(self.screen_resolution[1]) / 2
        line_coords = [(self.line_width, line_y), (self.line_width, -line_y), (-self.line_width, -line_y), (-self.line_width, line_y)]

        self.line_shape = visual.ShapeStim(win=self.win,
                            units="deg",
                            vertices=line_coords,
                            fillColor='black',
                            lineColor='none',
                            closeShape=True)
        
        # Initialize square
        self.square = visual.ShapeStim(win=self.win, units="deg",
                          vertices=self.square_coords,
                          fillColor='white',
                          closeShape=True)
        

    def pixels_to_degrees(self, pixels):
        """
        Convert pixels to units of degrees of visual angle

        Parameters:
        pixels (int): Number of pixels to be converted.
        screen_width (float): The width of your monitor (or window) screen in cm.
        screen_resolution_width (int): Screen resolution in pixels.
        viewing_distance (float): Distance from the screen to the observer in cm.

        Outputs:
        degrees (float): Degrees of visual angle
        """
        # Calculate the degrees of visual angle
        degrees = 2 * math.atan((pixels * self.screen_width) / (2 * self.viewing_distance * self.screen_resolution[0])) * (180 / math.pi)
        return degrees

    
    def display_text_slides(self, text_array):
        """
        Displays slides of text in sequential order, where each slide
        is an element in an array of Strings and does not proceed to 
        next slide until user presses a key.

        Inputs:
        text_array (array of String values): Slides of text to be displayed
        """
        for document in text_array:
            message = visual.TextStim(self.win, text=document, pos=(0,0), color='white')
            message.draw()
            self.win.flip()
            event.waitKeys()
    
    def display_failed_trial(self, tracker):
        """
        displays a failed trial that should get recycled.
        """
        document = "Trial discarded. Press any key to continue and refocus on the square, or let us know if you wish to recalibrate."

        message = visual.TextStim(self.win, text=document, pos=(0,0))
        message.draw()
        self.win.flip()

        # Wait for a keypress
        key = event.waitKeys()

        # `event.waitKeys()` returns a list; get the first key pressed
        key = key[0]

        if key in ["q", "escape"]:
            tracker.shutdown()
            self.win.close()
            core.quit()
        elif key == "r":
            tracker.recalibrate()
            return


    def trial_display(self, trial, duration, pause_time, l_dimensions, l_dist, tracker):
        #display trial on screen. each trial records key strokes and will
        #exit if 'q' is pressed. 'right' indicates participant chooses the right
        #side of the screen and 'left' indicates participant chooses the left side
        #of the screen. if the participant makes a mistake, the function takes into
        #account which key was pressed MORE, so if 'n' is accidentally pressed, 'm'
        #can be pressed twice to correct for this error.
        #trial is a list of the form [ref_params, test_params]
        ref = trial.ref_params
        test = trial.test_params
        l_ref = [utilities.l_maker(l_dimensions[0], l_dimensions[1], l_dimensions[2], x, ref['vertex']) for x in ref['orient']]
        l_test = [utilities.l_maker(l_dimensions[0], l_dimensions[1], l_dimensions[2], x, test['vertex']) for x in test['orient']]
        trial_start = time.time()
        TRIAL_DONE = False
        direction = random.choice([-1, 1])
        while not TRIAL_DONE:
            elapsed_time = time.time() - trial_start
            cur_angle_ref = ref['speed'] * elapsed_time * direction
            cur_angle_test = test['speed'] * elapsed_time  * direction
            cur_coords_ref = utilities.l_placer(cur_angle_ref, l_dist, l_ref, ref['phase'], ref['displacement'])
            cur_coords_test = utilities.l_placer(cur_angle_test, l_dist, l_test, test['phase'], test['displacement'])
            for c in cur_coords_ref:
                visual_shape = visual.ShapeStim(win=self.win, units="deg", vertices=c, fillColor='black',lineColor='none',closeShape=True)
                visual_shape.draw()
            for c in cur_coords_test:
                visual_shape = visual.ShapeStim(win=self.win, units="deg", vertices=c, fillColor='black',lineColor='none',closeShape=True)
                visual_shape.draw()
            self.line_shape.draw()
            self.square.draw()
            self.win.flip()
            if elapsed_time > duration:
                TRIAL_DONE = True

            if tracker is not None:
                if not tracker.gazeInFixationWindow():
                    trial.deviation = True
                    return

            key = event.getKeys()
            if "q" in key or "escape" in key:
                if tracker is not None:
                    tracker.shutdown()
                self.win.close()
                core.quit()
        await_response = False
        while not await_response:
            self.line_shape.draw()
            self.square.draw()
            self.win.flip()
            key = event.getKeys()
            if "q" in key or "escape" in key:
                tracker.shutdown()
                self.win.close()
                core.quit()
            if 'r' in key: 
                tracker.recalibrate()
                trial.deviation = True
                return
            if 'right' in key:
                trial.participant_choice = "right"
                await_response = True
            elif 'left' in key:
                trial.participant_choice = "left"
                await_response = True
        self.line_shape.draw()
        self.square.draw()
        self.win.flip()
        #determine whether test is on the left or right during trial
        # if test['vertex'] == [-6,0]: #degrees of visual angle
        #     test_side = "left"
        # else:
        #     test_side = "right"
        if trial.participant_choice == "left":
            trial.answer = "same"
        elif trial.participant_choice == "right":
            trial.answer = "different"
        core.wait(pause_time)
        # return participant_choice, test_side, test['speed'], answer, ref['orientation'], test['orientation'], DEVIATION


# line_y = display_utilities.pixels_to_degrees(window_dimensions[1], monitor_width, monitor_resolution[0], viewing_distance) / 2

# # Define coordinates for centre line
# line_coords = [(0.13, line_y), (0.13, -line_y), (-0.13, -line_y), (-0.13, line_y)]

# # Define coordinates for fixation spot in degrees of visual angle
# square_coords = [(0.10, 0.10), (0.10, -0.10), (-0.10, -0.10), (-0.10, 0.10)]

# line_shape = visual.ShapeStim(win=win,
#                             units="deg",
#                             vertices=line_coords,
#                             fillColor='black',
#                             lineColor='none',
#                             closeShape=True)


