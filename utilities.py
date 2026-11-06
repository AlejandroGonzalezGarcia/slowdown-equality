import random
import time
import numpy as np
import json
import time, math, os
from models import Trial

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
    """
    Rotates coordinates of L
    """

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

def get_trial_list(num_reps, num_blocks, test_speeds, configurations,
                   ref_speed, square_size, l_num):
    """
    Generates list of trials.

    Parameters:
    num_reps (int): Number of repetitions per speed, per condition
    num_blocks (int): Number of blocks that experiment is broken up into
    test_speeds (float array): Array of test speeds
    configurations (list of lists): List where each index is a 2-length list
                    of configurations to compare in order [reference, test]
    ref_speed (float): Reference speed
    square_size (list of floats): Dimensions of each square formed by vertices
                                  of rotation [width, height]
    l_num (int): Number of Ls rotating around vertex of rotation.

    Output:
    final_list (array): An array of length num_blocks, where each index corresponds
    to an array of Trial objects of length
                len(configurations) * len(test_speeds) * num_reps / num_blocks
    """
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
    for _ in range(num_blocks):
        #create empty list for block
        block_list = []
        #iterate over each speed
        for test_speed in test_speeds:
            #generate array of locations of length equal to even number of reps
            #to be in the block
            test_location = possible_locations * int(reps_per_block / 2)
            #iterate over test locations
            for loc in test_location:
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
                    ref_config = configuration[0]
                    test_config = configuration[1]
                    if (test_config == "global") and (ref_config == "global"):
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
                    elif (test_config == "local") and (ref_config == "local"):
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
                    elif (test_config == "global") and (ref_config == "local"):
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
                    elif (test_config == "local") and (ref_config == "global"):
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
                    # add a trial to block list
                    block_list.append(Trial(test_params, ref_params,
                                            test_vertex, ref_vertex,
                                            test_speed, ref_speed,
                                            test_config, ref_config))
        # once block is compelte, add it to final list 
        random.shuffle(block_list)
        final_list.append(block_list)
    return final_list

def get_practice_trials(num_trials, sample_list):
    """
    Generates list of practice trials.

    Parameters:
    num_trials (int): Number of practice trials to be generated.
    sample_list (list of Trial objects): list to extract practice trials from.

    Output:
    practice_trials (list of Trial objects): A list of practice trials of 
    length num_trials.
    """
    practice_trials = []
    while len(practice_trials) < num_trials:
        random_index = random.randint(0, len(sample_list) - 1)
        random_block = sample_list[random_index]
        random_trial = random.choice(random_block)
        practice_trials.append(random_trial)
    return practice_trials

