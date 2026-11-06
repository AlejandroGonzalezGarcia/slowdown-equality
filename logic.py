import random
import time
import numpy as np
import json
import time, math, os
import utilities
from display import Display
from models import Trial
from tracker import Tracker
from EyeTracking import EyeTracker
from psychopy import visual, logging, core, monitors, event

# load experiment parameters
with open('parameters.json', 'r') as openfile:
    # Reading from json file
    exp_params = json.load(openfile)

(l_num, l_dimensions, l_dist, configurations, square_size,
test_speeds, ref_speed, num_blocks, num_reps, trial_duration, pause_time,
num_practice_runs, window_size, viewing_distance, monitor_width, 
monitor_resolution, participant_name, switch_percentage,
switch_duration, num_switch_practice_runs, folder_name) = utilities.error_handling(exp_params)

##############################################################################################
###### CREATE LIST OF TRIALS ######

# Generate final list
final_list = utilities.get_trial_list(num_reps, num_blocks, test_speeds,
                                      configurations, ref_speed, square_size,
                                      l_num)

# Generate practice trials
practice_trials = utilities.get_practice_trials(num_practice_runs, final_list)

##############################################################################################
######## CREATE MONITOR AND DEFINE WINDOW ######

# Step 1: Define monitor parameters manually

# # Create monitor object
my_monitor = monitors.Monitor(name='testmonitor', width=monitor_width, distance=viewing_distance)
my_monitor.setSizePix(monitor_resolution)  # Set monitor resolution if known

# Define window
# window_dimensions, full = display_utilities.create_window(window_size, monitor_resolution)

# Initialize display object (window is initialized as attribute)
display = Display(my_monitor, monitor_width, monitor_resolution, viewing_distance, window_size)

# ##############################################################################################
# ###### INTRO TEXT AND PRACTICE TRIALS ######

# Create tracker object
# tracker = Tracker("mouse", display)
tracker = EyeTracker(
    tracker="livetrack", 
    trackEyes=[True, True],
    fixationWindow=2.0,
    minFixDur=0.5,
    fixTimeout=5.0,
    psychopyWindow=display.win, 
    filefolder="dummyfolder", 
    filename="dummy",
    samplemode="average",
    calibrationpoints=5,
    fixationStimuli=display.square
)


# Initialize tracker and pop up video
tracker.initialize()

# Calibration text
calibration_text = [f"Welcome to the experiment! We will begin by calibrating our eye tracker. The process is simple: \
you will be presented with {tracker.calibrationpoints} stimuli at varying positions on the screen. The goal is for you \
to keep your head as still as possible, while following the simuli on the screen with your eyes only. By pressing any key, \
you will begin the calibration process. Enjoy!"
]

# Display calibration text
display.display_text_slides(calibration_text)

# Start collecting and calibrate
tracker.openfile()
tracker.startcollecting()
tracker.calibrate()

# Intro text
intro_text = ["Well done! We will begin by introducing the experiment, \
and what you are required to do. Press any key to continue.",
    "Instructions are simple. You will be required to focus your eyes on a square-shaped fixation spot \
located in the centre of the screen. The screen will be divided down the middle by a solid black line, \
and on either side of the screen you will see 4 pairs of Ls that are rotating. Press any key to continue.",
    f"The idea is that, while keeping your eyes on the square-shaped fixation spot, you pay attention to the \
Ls on the left and right side of the screen. The Ls will appear for a duration of {trial_duration}s  \
and then disappear. Once they have disappeared, you are asked to make a decision about which side of the screen the Ls \
were moving faster, using the 'right' and 'left' arrow keys. This makes up a single trial. Press any key to continue.",
    f"Let's try {num_practice_runs} practice trials. Throughout these trials, you will \
select whether you think the Ls on the left or the right side of the screen moved faster. \
Remember: focus on the fixation spot, and once the Ls disappear, make your choice using \
the 'left' or 'right' arrow key. After this, the next trial will begin. Please note that the trials \
will not begin unless your vision is fixated on the square. Ready? Press \
any key to begin your practice trials."]

# Display intro text
display.display_text_slides(intro_text)

# Ensure wait for participant to obtain fixation
tracker.waitForFixation()

# # Make sure participant presses centre square before experiment begins
# tracker.touch_shape(display.square)

# Display practice trials
failure_count = 0
total_count = 0
i = 0
print("Beginning Practice Trials...")
while (i < len(practice_trials)):
    print(f"\nDisplaying trial {i+1} of practice trials.")
    trial = practice_trials[i]
    display.trial_display(trial, trial_duration,
                        pause_time, l_dimensions, l_dist, tracker)
    if trial.deviation:
        print(f"\nTrial {i+1} has failed. If participant wishes to recalibrated, press 'r'.")
        display.display_failed_trial(tracker)
        tracker.waitForFixation()
        trial.deviation = False
        practice_trials.append(practice_trials.pop(i))
        print(f"Practice trial {i+1} has failed. Discarding trial.")
        failure_count += 1
    else:
        i += 1
    total_count += 1

    # print(f"test side: {trial.test_side}")
    # print(f"participant choice: {trial.participant_choice}")
print(f"\nPractice trials ended with {total_count} trials and {failure_count} failed trials.")


# Introduce text between practice results and actual experiment
inter_text = [
    f"You have completed the {num_practice_runs} practice trials with {failure_count} \
failed trials, for a total {total_count} trials. Press any key to continue.",
    f"The experiment is divided into {num_blocks} blocks, and after each block you will \
have an opportunity to take a break until you are ready to proceed. During the experiment, \
you can exit at any time by pressing the 'q' key. Press any key to continue."
]

# Display text after practice trials
display.display_text_slides(inter_text)

################# EXPERIMENT DISPLAY #################

# Initialize results dictionary and trial counter
results = {}
k = 0
for i, block in enumerate(final_list):
    print(f"\nBeginning block {i+1}")
    # Initialize results dictionary for current block
    block_results = {}
    # Add key for current block to results dictionary
    results[f"Results for block {i + 1}"] = block_results
    
    # Display text prior to block
    if i > 0:
        # recalibrate for the upcoming block
        tracker.recalibrate()
        block_text = [f"You are now beginning block {i + 1}. Press any key to proceed."]
    else:
        block_text = ["You are about to begin the first block. Press any key to begin."]
    display.display_text_slides(block_text)

    # Initialize attention on fixation
    tracker.waitForFixation()

    # Initialize counters for block
    total_count = 0
    failure_count = 0
    j = 0

    # Display block trials
    # while j < len(block):
    #     trial = block[j]
    #     display.trial_display(trial, trial_duration,
    #                     pause_time, l_dimensions, l_dist, tracker)
    #     if trial.deviation:
    #         # display.display_failed_trial()
    #         # tracker.touch_shape(display.square)
    #         # trial.deviation = False 
    #         # practice_trials.append(practice_trials.pop(i))
    #         # failure_count += 1
    #         display.display_failed_trial()
    #         tracker.waitForFixation()
    #         trial.deviation = False
    #         block.append(block.pop(i))
    #         print(f"trial {j}  in block {i} popped and appended")
    #         failure_count += 1
    #     else: # Save trial results in results dictionary
    #         block_results[f"Trial {k+1}"] = {
    #             "test location": trial.test_side,
    #             "participant choice": trial.participant_choice,
    #             "speed of test": trial.test_params["speed"],
    #             "speed of reference": trial.ref_params["speed"],
    #             "selection": trial.answer,
    #             "reference orientation": trial.ref_params["orientation"],
    #             "test orientation": trial.test_params["orientation"]
    #         }
    #         j += 1
    #         k += 1
    #     total_count += 1
    
    while j < len(block):
        DISCARDED = False
        trial = block[j]
        print(f"\nDisplaying trial {j+1} ({total_count+1} including discarded trials) in block {i+1}.")
        display.trial_display(trial, trial_duration,
                        pause_time, l_dimensions, l_dist, tracker)
        if trial.deviation:
            print(f"\nTrial {total_count+1} has failed. If participant wishes to recalibrated, press 'r'.")
            DISCARDED = True
            display.display_failed_trial(tracker)
            tracker.waitForFixation()
            trial.deviation = False
            block.append(block.pop(j))
            print(f"Discarding trial {j+1} ({total_count+1} including discarded trials) in block {i+1} and appending it to end of block.")
            failure_count += 1
        else:
            j += 1
        block_results[f"Trial {k+1}"] = {
                "test location": trial.test_side,
                "participant choice": trial.participant_choice,
                "speed of test": trial.test_params["speed"],
                "speed of reference": trial.ref_params["speed"],
                "selection": trial.answer,
                "reference orientation": trial.ref_params["orientation"],
                "test orientation": trial.test_params["orientation"],
                "trial discarded": DISCARDED
            }
        k += 1
        total_count += 1

    print(f"\nBlock {i+1} performance:\n{total_count} total trials\n{failure_count} failed trials")
    # Give feedback for the block that was just completed
    feedback_text = [f"The previous block originally consisted of {j} trials. Due to your attention on the \
fixation, you had to completed {total_count} trials, with having failed {failure_count} trials. Press \
any key to continue."]
    display.display_text_slides(feedback_text)

#thank you text
final_text = [
    "You completed the experiment! Thank you for your participation and for \
contributing towards our research. Your time and patience is greatly appreciated. \
Press any key to exit."
]
display.display_text_slides(final_text)
######################################################

################### EXPORT RESULTS ###################

# Export results to a json file within 'results' folder
folder = f"{folder_name}"
os.makedirs(folder, exist_ok=True)

file_path = os.path.join(folder, f'output_{participant_name}.json')

with open(file_path, 'w') as file:
    json.dump(results, file, indent=4)

######################################################