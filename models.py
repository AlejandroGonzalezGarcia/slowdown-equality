import random
import time
import numpy as np
import json
import time, math, os

class Trial:
    def __init__(self, test_params, ref_params,
                 test_vertex, ref_vertex, test_speed,
                 ref_speed, test_config, ref_config):
        """
         Initialize a single trial instance.

        Parameters:
        - ref_params (dict): Reference parameters (copied for safety)
        - test_params (dict): Test parameters (copied for safety)
        - test_vertex: Vertex for the test condition
        - ref_vertex: Vertex for the reference condition
        - test_speed: Speed for the test condition
        - ref_speed: Speed for the reference condition
        - test_config: Orientation/configuration for test
        - ref_config: Orientation/configuration for reference
        """

        self.ref_params = ref_params.copy()
        self.test_params = test_params.copy()
    
        self.test_params["vertex"] = test_vertex
        self.ref_params["vertex"] = ref_vertex

        self.test_params["speed"] = test_speed
        self.ref_params["speed"] = ref_speed

        self.test_params["orientation"] = test_config
        self.ref_params["orientation"] = ref_config

        # Establish location of test
        if self.test_params['vertex'] == [-6,0]: #degrees of visual angle
            self.test_side = "left"
        else:
            self.test_side = "right"

        # Initialize participant choice to none
        self.participant_choice = None

        # Initialize answer
        self.answer = None

        # Initialize deviation
        self.deviation = False # Flag for deviation tracking

    
    
    def __str__(self):
        return f"TRIAL OBJECT WITH DEVIATION = {self.deviation}\n\
TEST PARAMETERS: {self.test_params}\n\
REFERENCE PARAMETERS: {self.ref_params}"
        
