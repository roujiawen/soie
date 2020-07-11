"""This module contains C++ code that underlies the simulation as well as
Python commands to compile the C++ code through scipy.weave.
"""
import os

import numpy as np
from weave import ext_tools

from common.parameters import N_GLOBAL_STATS

CODE_PATH = os.path.join(os.path.dirname(__file__), "_c_code")

def weave_compile():
    """Compile C++ simulation code using numpy.weave so that it can be used in
    the Python program. Generate c_code.so file.
    """
    # ---------------------Specify variable types--------------------
    # The parameters below are used only to specify the types of variables
    # when compiling the C++ code, and does not affect the actual application
    # when it's run.
    params = {
        'Gradient Intensity': [0.0, 0.0, 1.52],
        'Cell Density': 0.5,
        'Angular Inertia': 2.5284,
        'Alignment Strength': 1.5284,
        'Pinned Cells': ['none', 'none', 'none'],
        'Gradient Angle': [0.79, 0.47, 1.83],
        'Alignment Range': 11.1,
        'Affinity': [[3.25, 1.13, 1.15],
                     [1.13, 1.36, 4.0],
                     [1.15, 4.0, 1.48]],
        'Attraction-Repulsion Strength': 4.7298,
        'Cell Ratio': [0.5, 0.5, 0.],
        'Noise Intensity': 0.28,
        'Velocity': [0.034, 0.016, 0.169],
        'Attraction-Repulsion Range': 10.2
    }
    steps = 1  # Number of steps
    # Empty list for storing global properties
    global_stats = np.zeros(N_GLOBAL_STATS * steps)
    sf = 1.  # Scale factor
    size_x = 10./sf  # Size of arena
    size_y = 10./sf  # Size of arena
    r0 = 0.1  # Core radius
    r0_x_2 = r0 * 2 # Diameter of a particle
    # Number of particles
    n = int(params["Cell Density"]*(size_x*size_y)/(2*(3**0.5)*r0*r0))
    eff_nop = float(n)  # Effective number of particles
    noise_coef=params["Noise Intensity"]
    iner_coef = params["Angular Inertia"]
    r1 = params["Attraction-Repulsion Range"]*r0
    rv = params["Alignment Range"]*r0
    f0 = params["Attraction-Repulsion Strength"]
    fa = params["Alignment Strength"]
    v0 = np.array(params["Velocity"])
    beta = np.array(params["Affinity"])
    n_per_species = np.array([n/2, n+1]).astype(np.int32)
    grad_x = np.array([np.cos(d*np.pi) * i for d, i in
                       zip(params["Gradient Angle"],
                           params["Gradient Intensity"])])
    grad_y = np.array([np.sin(d*np.pi) * i for d, i in
                       zip(params["Gradient Angle"],
                           params["Gradient Intensity"])])
    pinned = np.array([0 if x == "none" else 1 for x in
                       params["Pinned Cells"]]).astype(np.int32)
    # Particles positions and velocities
    pos_x = np.random.random(n)*size_x
    pos_y = np.random.random(n)*size_y
    dir_x = np.zeros(n)
    dir_y = np.zeros(n)

    # ---------------------C file name---------------------
    mod = ext_tools.ext_module('c_code')

    # ---------------------Main code: fixed boundary---------------------
    # Measure distance for fixed boundary condition
    with open(os.path.join(CODE_PATH, "fb_dist.cpp"), "r") as infile:
        fb_dist = infile.read()

    # Fit coordinates into the arena for fixed boundary condition
    with open(os.path.join(CODE_PATH, "fb_fit.cpp"), "r") as infile:
        fb_fit = infile.read()

    # Run simulation for a give number of steps under fixed boundary
    with open(os.path.join(CODE_PATH, "fb_main_code.cpp"), "r") as infile:
        fb_main_code = infile.read()

    # ---------------------Main code: periodic boundary---------------------
    # Measure distance for periodic boundary condition
    with open(os.path.join(CODE_PATH, "pb_dist.cpp"), "r") as infile:
        pb_dist = infile.read()
    # Fit coordinates into the arena for periodic boundary condition
    with open(os.path.join(CODE_PATH, "pb_fit.cpp"), "r") as infile:
        pb_fit = infile.read()

    # Run simulation for a give number of steps under periodic boundary
    with open(os.path.join(CODE_PATH, "pb_main_code.cpp"), "r") as infile:
        pb_main_code = infile.read()

    # ---------------------Fixed boundary---------------------
    # Create main function from C++ code and specify input
    fb_tick_func = ext_tools.ext_function(
        'fb_tick', fb_main_code,
        ["n", "eff_nop", "size_x", "size_y", "r0_x_2", "r1", "rv", "iner_coef",
         "f0", "fa", "noise_coef", "v0", "pinned", "n_per_species", "beta",
         "grad_x", "grad_y", "pos_x", "pos_y", "dir_x", "dir_y",
         "global_stats", "steps"])
    # Add helper functions to main function
    fb_tick_func.customize.add_support_code(fb_dist)
    fb_tick_func.customize.add_support_code(fb_fit)
    fb_tick_func.customize.add_header("<math.h>")
    # Add main function to module
    mod.add_function(fb_tick_func)

    # ---------------------Periodic boundary---------------------
    # Create main function from C++ code and specify input
    pb_tick_func = ext_tools.ext_function(
        'pb_tick', pb_main_code,
        ["n", "eff_nop", "size_x", "size_y", "r0_x_2", "r1", "rv", "iner_coef",
         "f0", "fa", "noise_coef", "v0", "pinned", "n_per_species", "beta",
         "grad_x", "grad_y", "pos_x", "pos_y", "dir_x", "dir_y",
         "global_stats", "steps"])
    # Add helper functions to main function
    pb_tick_func.customize.add_support_code(pb_dist)
    pb_tick_func.customize.add_support_code(pb_fit)
    pb_tick_func.customize.add_header("<math.h>")
    # Add main function to module
    mod.add_function(pb_tick_func)
    # Compile
    mod.compile(compiler="gcc", verbose=1)

if __name__ == "__main__":
    weave_compile()
