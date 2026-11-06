from psychopy import visual, logging, core, monitors, event
import random
import time
import numpy as np
import json
import time, math, random, json, os

#seed for reproducibility 
random.seed(42)

###############################################################################################
# function definitions 
def rotate(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.
    """
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy

def l_maker(width, height, thickness, orientation=0, origin=[0, 0]):
    # Define L shape points without rotation
    pt1 = [ -width/2 + origin[0], height/2 + origin[1] ]
    pt2 = [ -width/2 + origin[0], -height/2 + origin[1] ]
    pt3 = [ width/2 + origin[0], -height/2 + origin[1] ]
    pt4 = [ width/2 + origin[0], -height/2 + origin[1] + thickness ]
    pt5 = [ -width/2 + origin[0] + thickness, -height/2 + origin[1] + thickness ]
    pt6 = [ -width/2 + origin[0] + thickness, height/2 + origin[1] ]
    # now rotate the coordinates
    coord_list = [ pt1, pt2, pt3, pt4, pt5, pt6 ]
    coord_list = [ rotate(origin, p, np.deg2rad(orientation)) for p in coord_list ]
    return coord_list

def l_placer(cur_angle, l_dist, l_coords, start_angle = [45, 45, 45, 45], displacement = [ [100, 100], [-100, 100], [-100,-100], [100, -100] ]):
     # cur_angle is the current angle of rotation - single number, same for all Ls
    # l_dist is the distance between the Ls - single number, same for all Ls
    # l_coords is the distance between the Ls - list of n lists of six (x,y) coordinates
    # start_angle is the starting angle of the Ls - list of n numbers [degrees]
    # displacement is the displament of the L pairs, list of n [x,y] coordinates

    cur_coords = []
    l_angles = [ a + cur_angle for a in start_angle ]
    for i, a in enumerate(l_angles):
        x_shift = float(np.cos(np.deg2rad(a))) * float(l_dist/2)
        y_shift = float(np.sin(np.deg2rad(a))) * float(l_dist/2)
        cur_coords.append( [ [ c[0]+x_shift+displacement[i][0], c[1]+y_shift+displacement[i][1] ] for c in l_coords[i] ] )
    return cur_coords

def error_handling(parameters):
    #simple error handling to make sure we receive valid inputs from json

    #check number of Ls is an integer number
    assert isinstance(parameters['number of L pairs'], int), "number of L \
pairs must be an integer"

    #check L_dimensions is an array of length 3 and elements are floats
    assert len(parameters['L size']) == 3, "L size must contain dimensions \
of Ls [width, height, thickness]"
    assert all(isinstance(element, float) for element in parameters['L size']), "\
L size elements must be floats"

    #check inter-L distance is a float
    assert isinstance(parameters['inter-L distance'], float), "Inter-L distance \
must be a float"

    #make sure configurations is a list with each element being a list of 2 elements
    assert (len(config) == 2 for config in parameters['configurations']), "elements in configuration \
list must be lists of two configurations"
    #make sure configurations are either "local" or "global"
    assert ((config[0] == "local" or config[0] == "global") and (config[1] == "local" or config[1] == "global")
            for config in parameters['configurations']), "configurations must be either 'local' or 'global'"

    #make sure square size is array of floats with 3 dimensions
    assert all(isinstance(element, float) for element in parameters['square dimensions']), "\
square dimensions must be floats [x, y]"

    #check that test speeds are floats and ref speed is a float
    assert all(isinstance(speed, float) for speed in parameters['test speeds']), "\
test speeds must be floats"
    assert isinstance(parameters['standard speed'], float), "standard speed must be a float"

    #make sure number of total reps is divisible by num_blocks
    assert parameters['total reps'] % parameters['number of blocks'] == 0, "\
total reps is not divisible by number of blocks"
    #make sure quotient of total reps / number of blocks yields an even number
    #to allow for blocks with an equal number of left and right test trials
    assert (parameters['total reps'] / parameters['number of blocks']) % 2 == 0, "\
number of blocks must be selected such that each block has an even number"

    #make sure time between trials is a float value
    assert isinstance(parameters['time between trials'], float), "time between trials \
must be a float value"

    #make sure number of practice runs is an integer value
    assert isinstance(parameters['number of practice runs'], int), "number of practice runs \
must be an integer value"

#     #make sure window size is array of length 2 for dimensions [width, height]
#     assert (len(parameters['window size']) == 2), "window size must be array of length 2 for \
# [width, height]"

    #make sure viewing distance is integer or float
    assert isinstance(parameters['viewing distance'], (float, int)), "viewing distance must be \
numerical value (either int or float)"

    #make sure monitor width is numerical
    assert isinstance(parameters['monitor width'], (int, float))

    #make sure monitor resolution is list of 2 dimensions
    assert (len(parameters['monitor resolution']) == 2), "monitor resolution must be array of \
length 2 for [width, height]"

    return (parameters['number of L pairs'], parameters['L size'], parameters['inter-L distance'],
            parameters['configurations'],
            parameters['square dimensions'], parameters['test speeds'], parameters['standard speed'],
            parameters['number of blocks'], parameters['total reps'], parameters['trial duration'],
            parameters['time between trials'], parameters['number of practice runs'],
            parameters['window size'], parameters['viewing distance'], parameters['monitor width'], 
            parameters['monitor resolution'], parameters['participant name'], 
            parameters["percentage of switch trials"], parameters["duration of fixation change"],
            parameters["number of switch practice runs"], parameters["folder name"])

def conditions(square_size, l_num):
    #generate global and local conditions given parameters imported
    #from json

    #define dispalcemenet array depending on square size
    displacement = [
        [square_size[0], square_size[1]],
        [-square_size[0], square_size[1]],
        [-square_size[0], -square_size[1]],
        [square_size[0], -square_size[1]]
    ]
    #define global orientations to form a square
    global_orientation = [180, 270, 0, 90]
    # given n number of Ls, we we create a numpy array where each element in
    # displacement is repeated n times
    displacement = np.repeat(displacement, l_num, axis=0)
    displacement = [list(array) for array in displacement]
    #for global configuration, the orientations are such that we have n squares
    global_orientation = list(np.repeat(global_orientation, l_num, axis=0))
    # local orientations are random elements from global configuration such that neighbouring
    # configurations are not identical
    local_orientation = [random.choice(global_orientation)]
    while len(local_orientation) < len(global_orientation):
        new_orientation = random.choice(global_orientation)
        if new_orientation != local_orientation[-1]:
            local_orientation.append(new_orientation)
    # generate list of possible phases
    possible_phases = np.arange(0,360,30)
    # draw 5 values from list of possible values and assign one to global
    local_phases = random.sample(list(possible_phases), 5)
    global_phases = [float(local_phases.pop())]
    # create global phases that are 360/n apart
    for i in range(l_num-1):
        next_phase = global_phases[i] + 360/l_num
        global_phases.append(next_phase)
    global_phases = global_phases * 4
    #local phases are also 360/n degrees apart
    local_phases = [float(element) + (360 // l_num) * i for element in local_phases for i in range(l_num)]

    return (displacement, global_orientation, global_phases, local_orientation,
            local_phases)

def trial_display(trial, duration, pause_time):
    #display trial on screen. each trial records key strokes and will
    #exit if 'q' is pressed. 'right' indicates participant chooses the right
    #side of the screen and 'left' indicates participant chooses the left side
    #of the screen. if the participant makes a mistake, the function takes into
    #account which key was pressed MORE, so if 'n' is accidentally pressed, 'm'
    #can be pressed twice to correct for this error.
    #trial is a list of the form [ref_params, test_params]
    ref = trial[0]
    test = trial[1]
    l_ref = [l_maker(l_dimensions[0], l_dimensions[1], l_dimensions[2], x, ref['ref vertex']) for x in ref['orient']]
    l_test = [l_maker(l_dimensions[0], l_dimensions[1], l_dimensions[2], x, test['test vertex']) for x in test['orient']]
    trial_start = time.time()
    TRIAL_DONE = False  
    participant_choice = None
    direction = random.choice([-1, 1])
    DEVIATION = False
    while not TRIAL_DONE:
        elapsed_time = time.time() - trial_start
        cur_angle_ref = ref['ref speed'] * elapsed_time * direction
        cur_angle_test = test['test speed'] * elapsed_time  * direction
        cur_coords_ref = l_placer(cur_angle_ref, l_dist, l_ref, ref['phase'], ref['displacement'])
        cur_coords_test = l_placer(cur_angle_test, l_dist, l_test, test['phase'], test['displacement'])
        for c in cur_coords_ref:
            visual_shape = visual.ShapeStim(win=win, units="deg", vertices=c, fillColor='black',lineColor='none',closeShape=True)
            visual_shape.draw()
        for c in cur_coords_test:
            visual_shape = visual.ShapeStim(win=win, units="deg", vertices=c, fillColor='black',lineColor='none',closeShape=True)
            visual_shape.draw()
        line_shape.draw()
        square.draw()
        win.flip()
        if elapsed_time > duration:
            TRIAL_DONE = True

        # mouse_pos = mouse.getPos()
        # if not square.contains(mouse_pos):
        #     DEVIATION = True
        #     return None, None, None, None, None, None, DEVIATION
        if deviation_from_shape(mouse, square):
           DEVIATION = True
           return None, None, None, None, None, None, DEVIATION

        
        key = event.getKeys()
        if 'q'in key:
            win.close()
            core.quit()
    await_response = False
    while not await_response:
        line_shape.draw()
        square.draw()
        win.flip()
        key = event.getKeys()
        if 'q' in key:
            win.close()
            core.quit()
        if 'right' in key:
            participant_choice = "right"
            await_response = True
        elif 'left' in key:
            participant_choice = "left"
            await_response = True
    line_shape.draw()
    square.draw()
    win.flip()
    #determine whether test is on the left or right during trial
    if test['test vertex'] == [-6,0]: #degrees of visual angle
        test_side = "left"
    else:
        test_side = "right"
    if participant_choice is None:
        answer = None
    elif test_side == participant_choice:
        answer = "correct"
    elif test_side != participant_choice:
        answer = "incorrect"
    core.wait(pause_time)
    return participant_choice, test_side, test['test speed'], answer, ref['ref orientation'], test['test orientation'], DEVIATION

def create_window(window_size, monitor_resolution):
    if window_size != "full":
        size = window_size
        fullscreen = False
    else:
        size = monitor_resolution
        fullscreen = True
    return size, fullscreen

##############################################################################################
####### IMPORT PARAMETERS #######

# load experiment parameters
with open('./parameters.json', 'r') as openfile:
    # Reading from json file
    exp_params = json.load(openfile)

(l_num, l_dimensions, l_dist, configurations, square_size,
test_speeds, ref_speed, num_blocks, num_reps, trial_duration, pause_time,
num_practice_runs, window_size, viewing_distance, monitor_width, 
monitor_resolution, participant_name, switch_percentage,
switch_duration, num_switch_practice_runs, folder_name) = error_handling(exp_params)

##############################################################################################
####### CREATE LIST OF TRIALS ######

#In this section we create a list that contains blocks. Each block is 
#a list itself that contains trials. Each trial is a list of the form
#[ref_params, test_params], where these are simply the reference and test
#parameters for each trial.
#Note that each block will contain an even number of trials, half with the
#test located on the left and half with the test located on the right


#define needed values and generate empty final list
reps_per_block = int(num_reps / num_blocks)
possible_locations = ["left", "right"]
final_list = []

#iterate and complete one block at a time
for block in range(num_blocks):
    #create empty list for block
    block_list = []
    #iterate over each speed
    for speed in test_speeds:
        #generate array of locations of length equal to even number of reps
        #to be in the block
        test_location = possible_locations * int(reps_per_block / 2)
        #iterate over test locations
        for loc in test_location:
            parameter_list = []
            if loc == "left":
                test_vertex = [-6,0] #in units of degrees of visual angle
                ref_vertex = [6,0] #in units of degrees of visual angle
            else:
                test_vertex = [6,0] #in units of degrees of visual angle
                ref_vertex = [-6,0] #in units of degrees of visual angle
            #iterate over configurations
            for configuration in configurations:
                #generate random configurations for each trial
                (displacement, global_orientation, global_phases,
                local_orientation, local_phases) = conditions(square_size, l_num)
                standard_config = configuration[0]
                test_config = configuration[1]
                if (test_config == "global") and (standard_config == "global"):
                    ref_params = {
                        "orient": global_orientation,
                        "phase": global_phases,
                        "displacement": displacement,
                    }
                    test_params = {
                        "orient": global_orientation,
                        "phase": global_phases,
                        "displacement": displacement
                    }
                elif (test_config == "local") and (standard_config == "local"):
                    ref_params = {
                        "orient": local_orientation,
                        "phase": local_phases,
                        "displacement": displacement
                    }
                    test_params = {
                        "orient": local_orientation,
                        "phase": local_phases,
                        "displacement": displacement
                    }
                elif (test_config == "global") and (standard_config == "local"):
                    ref_params = {
                        "orient": local_orientation,
                        "phase": local_phases,
                        "displacement": displacement
                    }
                    test_params = {
                        "orient": global_orientation,
                        "phase": global_phases,
                        "displacement": displacement
                    }
                elif (test_config == "local") and (standard_config == "global"):
                    ref_params = {
                        "orient": global_orientation,
                        "phase": global_phases,
                        "displacement": displacement
                    }
                    test_params = {
                        "orient": local_orientation,
                        "phase": local_phases,
                        "displacement": displacement
                    }
                #add useful key value pairs to parameter dictionaries
                test_params["test vertex"] = test_vertex
                ref_params["ref vertex"] = ref_vertex
                test_params["test speed"] = speed
                ref_params["ref speed"] = ref_speed
                test_params["test orientation"] = test_config
                ref_params["ref orientation"] = standard_config
                #append a list of parameters to the block list for each trial
                block_list.append([ref_params, test_params])
    #once block list is complete, shuffle the list
    random.shuffle(block_list)
    final_list.append(block_list)
#shuffle final list of blocks
random.shuffle(final_list)

##############################################################################################
####### MONITOR INFO #######

# Define the monitor
my_monitor = monitors.Monitor(name='testmonitor', width=monitor_width, distance=viewing_distance)
my_monitor.setSizePix(monitor_resolution)  # Set monitor resolution if known

# Create a window with the specified monitor
window_dimensions, full = create_window(window_size, monitor_resolution)
win = visual.Window(
    size = window_dimensions,
    units="deg",
    fullscr=full,
    monitor=my_monitor,
    color=[127,127,127],
    colorSpace='rgb255'
)

##############################################################################################
####### MAIN SECTION #######

#introduction text
intro_text = ["Welcome to the experiment! We will begin by introducing the experiment, \
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
will not begin unless your mouse is on the centre square. Ready? Press \
any key to begin your practice trials."]

#display intro text
for text_ in intro_text:
    message = visual.TextStim(win, text=text_, pos=(0,0), color='white')
    message.draw()
    win.flip()
    event.waitKeys()

# create practice trials by taking random trials from list of final trials
def practice(practice_trials = [], num_trials = num_practice_runs, sample_list = final_list):
    while len(practice_trials) < num_trials:
        random_index = random.randint(0, len(sample_list) - 1)
        random_block = sample_list[random_index]
        random_trial = random.choice(random_block)
        practice_trials.append(random_trial)
    return practice_trials
practice_trials = practice()

#define coordinates for fixation spot
square_coords = [(0.10, 0.10), (0.10, -0.10), (-0.10, -0.10), (-0.10, 0.10)]

#get height of window in degrees of visual angle using window_size from input in pixels
def pixels_to_degrees(pixels, screen_width, screen_resolution_width, viewing_distance):
    # Calculate the degrees of visual angle
    degrees = 2 * math.atan((pixels * screen_width) / (2 * viewing_distance * screen_resolution_width)) * (180 / math.pi)
    return degrees
#get distance from centre of the screen to top and bottom in degrees of visual angle
line_y = pixels_to_degrees(window_dimensions[1], monitor_width, monitor_resolution[0], viewing_distance) / 2
#define coordinates for centre line
line_coords = [(0.13, line_y), (0.13, -line_y), (-0.13, -line_y), (-0.13, line_y)]

line_shape = visual.ShapeStim(win=win,
                            units="deg",
                            vertices=line_coords,
                            fillColor='black',
                            lineColor='none',
                            closeShape=True)
square = visual.ShapeStim(win=win, units="deg",
                          vertices=square_coords,
                          fillColor='white',
                          closeShape=True)


# Before practice trials, make sure mouse is on the centre of the screen:

def touch_shape(mouse, shape):
    """checks for mouse touching shape.
        
        Args:
        mouse (Psychopy event.Mouse() object): defines the mouse to be tracked

        shape (Psychopy visual.ShapeStim() object): defines the shape whose boundaries we will
        consider.
    """
    while True:
        mouse_pos = mouse.getPos()

        # exit if 'q' is pressed
        if event.getKeys(keyList=["escape", "q"]):
            win.close()
            core.quit()

        # check if mouse is within square
        if shape.contains(mouse_pos):
            break
        else:
            shape.draw()
        win.flip()

def deviation_from_shape(mouse, shape):
    """checks for deviation from within the shape boundaries.
        
        Args:
        mouse (Psychopy event.Mouse() object): defines the mouse to be tracked

        shape (Psychopy visual.ShapeStim() object): defines the shape whose boundaries we will
        consider.

        Returns:
        True if mouse leaves shape boundaries

        False if mouse remains within shape boundaries (indicating no deviation from shape)
    """
    mouse_pos = mouse.getPos()
    if not shape.contains(mouse_pos):
        return True #return true for mouse leaving shape
    else:
        return False
        
# create mouse object
mouse = event.Mouse(win=win)

touch_shape(mouse, square)

#display practice trials
practice_results = []
line_shape.draw()
square.draw()
win.flip()

# for i, trial in enumerate(practice_trials):
#     trial_count = 0
#     correct_count = 0
#     (participant_choice, test_side, test_speed, response, _, _, deviation) = trial_display(trial, trial_duration,
#                                                                 pause_time)
 
#     if deviation:
#         message = visual.TextStim(win, text="Trial cancelled. Please keep your attention on the focal point.", pos=(0,0), color='white')
#         message.draw()
#         win.flip()
#         event.waitKeys()
#         touch_shape(mouse, square)
#     trial_count += 1
#     if response == "correct":
#         correct_count += 1
#     practice_results.append(participant_choice)

while practice_trials:
    trial = practice_trials.pop(0)
    

#introduce text between practice results and actual experiment
inter_text = [
    f"You have completed the {num_practice_runs} practice trials. Well done! \
That concludes the practice. Press any key to continue.",
    f"The experiment is divided into {num_blocks} blocks, and after each block you will \
have an opportunity to take a break until you are ready to proceed. During the experiment, \
you can exit at any time by pressing the 'q' key. Press any key to continue."
]

#display text between practice and trial runs
for text_ in inter_text:
    message = visual.TextStim(win, text=text_, pos=(0,0), color='white')
    message.draw()
    win.flip()
    event.waitKeys()

####run actual experiment

#create dictionary of results
results = {}
k = 1
#display trials in blocks
for i, block in enumerate(final_list):
    #create dictionary for results of current block
    block_results = {}
    #add key for current block to results dictionary which will
    #have values corresponding to each trial in this block
    results[f"Results for block {i + 1}"] = block_results
    #pre-block text
    if i > 0:
        block_text = f"You are now beginning block {i+1}. You're doing great! press any key to proceed."
    else:
        block_text = f"Get ready! Press any key to begin block {i+1}."
    block_message = visual.TextStim(win, text=block_text, pos=(0, 0), color='white')
    block_message.draw()
    win.flip()
    event.waitKeys()
    line_shape = visual.ShapeStim(win=win, units="deg",vertices=line_coords, fillColor='black',lineColor='none',closeShape=True)
    square = visual.ShapeStim(win=win, units="deg", vertices=square_coords, fillColor='white', closeShape=True)
    win.flip()
    #keep track of correct guesses in each block
    block_trial_count = 0
    block_correct_guesses = 0
    for j, trial in enumerate(block):
        (participant_choice, test_side, test_speed, response, ref_orientation, test_orientation) = trial_display(trial, trial_duration,
                                                                    pause_time)
        #add key to block dictionary corresponding to trial. each trial will be 
        #a dictionary and these will make up the values for each block where each
        #block is a key in the results dictionary.
        block_results[f"Trial {k}"] = {
            "test location": test_side,
            "participant choice": participant_choice,
            "speed of test": test_speed,
            "speed of reference": ref_speed,
            "selection": response,
            "reference orientation": ref_orientation,
            "test orientation": test_orientation
        }
        block_trial_count += 1
        if response == "correct":
            block_correct_guesses += 1
        k += 1

#thank you text
final_text = [
    "You completed the experiment! Thank you for your participation and for \
contributing towards our research. Your time and patience is greatly appreciated. \
Press any key to exit."
]

#display thank you text
for text_ in final_text:
    message = visual.TextStim(win, text=text_, pos=(0,0), color='white')
    message.draw()
    win.flip()
    event.waitKeys()

# export results to a json file within 'results' folder
folder = f"{folder_name}"
os.makedirs(folder, exist_ok=True)

file_path = os.path.join(folder, f'output_{participant_name}.json')

with open(file_path, 'w') as file:
    json.dump(results, file, indent=4)