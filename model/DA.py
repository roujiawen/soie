"""This module contains a class, Model, that represents the agent-based models.
It interfaces the C++ simulation code with the rest of the software application
which is in Python. """

from collections import OrderedDict

import numpy as np

from common.parameters import CORE_RADIUS, FIELD_SIZE, N_GLOBAL_STATS
from common.tools import counts2slices
import model.c_code as c_model


class Model(object):
    """A model for a system of self-propelled particles.

    Methods:
        gen_internal_params: Convert user-input parameters to internal format
            convenient for the C++ program.
        init_particles_state: Initialize the state of a system.
        tick: Run the simulation for a given number of steps.
        set: Set the model to a given state, used when loading saved genes or
            sessions.

    Attributes:
        state (tuple): Positions and directions of all particles.
        global_stats (numpy.ndarray): Global properties (group angular
            momentum, segregation, etc.) of the system over time.
        user_params (dict): The parameters of the system as seen and written
            by users.
        internal_params (OrderedDict): The parameters of the system in an
            internal format.
    """
    def __init__(self, params, scale_factor=1., periodic_boundary=False):
        """
        Parameters:
            params (dict): The parameters of the model as seen by the users.
            scale_factor (float): Specifies the scale of the simulation. The
                default arena size is 10x10. For a scale factor (zoom) of 2.0,
                the arena size is effectively 20x20.
            periodic_boundary (bool): Whether to use periodic boundary
                conditions.
        """
        # Initialize empty array to store global properties
        self.global_stats = np.zeros([N_GLOBAL_STATS, 0])
        self.user_params = params
        # Periodic boundary settings
        if periodic_boundary is False:
            self.tick = self.fb_tick
        else:
            self.tick = self.pb_tick
        # Generate internal parameters from user input
        self.internal_params = self.gen_internal_params(scale_factor)
        self.periodic_boundary = periodic_boundary

    @property
    def state(self):
        """Return a tuple of four arrays, representing the state of the
        particle system: positions and directions. """
        return self.pos_x, self.pos_y, self.dir_x, self.dir_y

    def gen_internal_params(self, scale_factor):
        """Format user-provided parameters into internal parameters accepted
        by the C++ program. """
        # Name shortening for frequent variables
        uprm = self.user_params
        # FORMATTING INTERNAL PARAMS
        # Particle core radius
        r0_x_2 = CORE_RADIUS * 2
        # Calculate actual field size (scaled)
        xlim = ylim = FIELD_SIZE / float(scale_factor)
        # Calculate number of particles
        max_num_particles = (np.sqrt(3)/6.) * (xlim*ylim) / (CORE_RADIUS**2)
        nop = int(uprm['Cell Density'] * max_num_particles)
        # Calculate force and alignment radii
        r1 = uprm['Interaction Range'] * CORE_RADIUS
        ra = uprm['Alignment Range'] * CORE_RADIUS
        # Just copying
        iner_coef = uprm['Angular Inertia']
        f0 = uprm['Interaction Force']
        fa = uprm['Alignment Force']
        noise_coef = uprm['Noise Intensity']
        # Change type
        v0 = np.array(uprm["Velocity"])
        beta = np.array(uprm["Adhesion"])
        # Pinned = 0 (none) or 1 (fixed)
        pinned = np.array([0 if x == "none" else 1
                           for x in uprm["Pinned Cells"]]).astype(np.int32)
        # Convert ratio to number of cells in each species
        ratios = uprm["Cell Ratio"][:2]
        cumu_ratios = [sum(ratios[:i+1]) for i in range(len(ratios))] + [1.0]
        cumu_n_per_species = [0] + [int(nop*each) for each in cumu_ratios]
        n_per_species = np.array(
            [cumu_n_per_species[i] - cumu_n_per_species[i - 1]
             for i in range(1, len(cumu_n_per_species))]).astype(np.int32)
        # Gradient from polar to cartesian
        grad_x = np.array(
            [np.cos(d*np.pi) * i for d, i in zip(
                uprm["Gradient Direction"], uprm["Gradient Intensity"])])
        grad_y = np.array(
            [np.sin(d*np.pi) * i for d, i in zip(
                uprm["Gradient Direction"], uprm["Gradient Intensity"])])

        # Effective number of particles (excluding pinned)
        eff_nop = float(
            np.sum([n_per_species[i] for i in range(len(n_per_species))
                    if pinned[i] == 0]))

        names = [
            'nop', 'eff_nop', 'xlim', 'ylim',
            'r0_x_2', 'r1', 'ra',  # radii
            'iner_coef', 'f0', 'fa', 'noise_coef',  # strengths
            'v0', 'pinned', 'n_per_species', 'beta', 'grad_x', 'grad_y'  # arr
            ]
        internal_params = OrderedDict([(x, locals()[x]) for x in names])
        return internal_params

    def init_particles_state(self):
        """Initialize a system of particles given params."""
        iprm, uprm = self.internal_params, self.user_params
        nop, xlim, ylim = iprm['nop'], iprm['xlim'], iprm['ylim']
        n_per_species = iprm['n_per_species']

        # Randomize position
        pos_x = np.random.random(nop) * xlim
        pos_y = np.random.random(nop) * ylim

        # Randomize velocity
        theta = np.random.random(nop) * 2 * np.pi
        dir_x = np.cos(theta)
        dir_y = np.sin(theta)

        # Randomize pinned shape
        # For different types
        types = counts2slices(n_per_species)
        for type_, pinned_shape in zip(types, uprm["Pinned Cells"]):
            if pinned_shape != "none":
                n = type_.stop - type_.start  # length of the slice
                dir_x[type_] = 0.
                dir_y[type_] = 0.
                if pinned_shape == "ring":
                    # Radius = 30%-40% of field size
                    radius = xlim * (0.3+np.random.random(n)*0.1)
                    theta = 2 * np.random.random(n) * np.pi
                    pos_x[type_] = xlim/2. + np.cos(theta)*radius
                    pos_y[type_] = ylim/2. + np.sin(theta)*radius

                elif pinned_shape == "circle":
                    # 0-20% of field size
                    radius = xlim * 0.2 * np.random.power(2, n)
                    theta = 2 * np.random.random(n) * np.pi
                    pos_x[type_] = xlim/2. + np.cos(theta)*radius
                    pos_y[type_] = ylim/2. + np.sin(theta)*radius

                elif pinned_shape == "square":
                    # radius ~ 40-50% of field size
                    side = np.random.randint(0, 4, n)
                    coord = np.random.random(n) * 0.9 * xlim
                    depth = np.random.random(n) * 0.1 * xlim
                    temp_x, temp_y = np.empty(n), np.empty(n)
                    is_0 = side == 0
                    temp_x[is_0], temp_y[is_0] = depth[is_0], coord[is_0]
                    is_1 = side == 1
                    temp_x[is_1], temp_y[is_1] = (xlim - depth[is_1],
                                                  coord[is_1] + 0.1 * ylim)
                    is_2 = side == 2
                    temp_x[is_2], temp_y[is_2] = (coord[is_2] + 0.1 * xlim,
                                                  depth[is_2])
                    is_3 = side == 3
                    temp_x[is_3], temp_y[is_3] = (coord[is_3],
                                                  ylim - depth[is_3])
                    pos_x[type_] = temp_x
                    pos_y[type_] = temp_y

        self.pos_x, self.pos_y, self.dir_x, self.dir_y = (
            pos_x, pos_y, dir_x, dir_y)

    def fb_tick(self, steps):
        """Run the simulation for a given number of steps under fixed
        boundary conditions."""
        global_stats_slice = np.zeros(N_GLOBAL_STATS * steps)
        c_model.fb_tick(
            *self.internal_params.values()
            + [self.pos_x, self.pos_y, self.dir_x, self.dir_y,
               global_stats_slice, steps])
        self.global_stats = np.hstack(
            [self.global_stats,
             global_stats_slice.reshape(N_GLOBAL_STATS, steps)])

    def pb_tick(self, steps):
        """Run the simulation for a given number of steps under periodic
        boundary conditions."""
        global_stats_slice = np.zeros(N_GLOBAL_STATS * steps)
        c_model.pb_tick(
            *self.internal_params.values()
            + [self.pos_x, self.pos_y, self.dir_x, self.dir_y,
               global_stats_slice, steps])
        self.global_stats = np.hstack(
            [self.global_stats,
             global_stats_slice.reshape(N_GLOBAL_STATS, steps)])

    def set(self, state, global_stats):
        """Load given global properties and state into the Model."""
        self.global_stats = np.array(global_stats)
        self.pos_x, self.pos_y, self.dir_x, self.dir_y = [
            np.array(_) for _ in state]

def main():
    # TEST: python -m model.DA
    import time
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection

    def test_model(params, scale_factor, velocity_trace,
                   periodic_boundary, steps):
        """Plot the results of the simulation given parameters."""
        # Track time it takes to run the model
        start_time = time.time()
        alpha = 0.8
        m = Model(params, scale_factor=scale_factor,
                  periodic_boundary=periodic_boundary)
        m.init_particles_state()
        # Run model
        m.tick(steps)
        print("--- %s seconds ---" % (time.time() - start_time))
        # Prepare for making plots
        x, y, dir_x, dir_y = m.state
        species_velocity = m.user_params["Velocity"]
        n_per_species = m.internal_params["n_per_species"]
        colors = ["blue", "red", "green"]
        # Set up plot parameters
        figsize = (5,5)
        dpi = 100
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        dots = (figsize[0]*dpi)**2
        circle_size = dots/100. * 3.14 * (0.08 * scale_factor)**2
        multiplier = velocity_trace
        # Plot particle system
        for k, s in enumerate(counts2slices(n_per_species)):
            if multiplier > 0:
                segs = []
                for j in range(s.start, s.stop):
                    segs.append(
                        ((x[j], y[j]),
                         (x[j]-dir_x[j]*multiplier*species_velocity[k],
                          y[j]-dir_y[j]*multiplier*species_velocity[k])))
                ln_coll = LineCollection(segs, colors=colors[k],
                                         linewidths=1, alpha=alpha)
                ax.add_collection(ln_coll)
            ax.scatter(x[s], y[s], s=circle_size, color=colors[k],
                       linewidths=0, alpha=alpha)
        # Set plot limits
        adjusted_limit = 10. / scale_factor
        plt.xlim([0, adjusted_limit])
        plt.ylim([0, adjusted_limit])
        plt.show()
    # ----------------------SVM----------------------
    params = {
        "Alignment Range": 10.0,
        "Pinned Cells": [
            "none",
            "none",
            "none"
        ],
        "Interaction Force": 0.0,
        "Gradient Intensity": [
            0.0,
            0.0,
            0.0
        ],
        "Cell Ratio": [
            1.0,
            0.0,
            0.0
        ],
        "Alignment Force": 1.0,
        "Noise Intensity": 0.016,
        "Angular Inertia": 0.01,
        "Adhesion": [
            [
                0.01,
                0.01,
                0.01
            ],
            [
                0.01,
                0.01,
                0.01
            ],
            [
                0.01,
                0.01,
                0.01
            ]
        ],
        "Gradient Direction": [
            0.0,
            0.0,
            0.0
        ],
        "Cell Density": 0.42,
        "Velocity": [
            0.03,
            0.03,
            0.03
        ],
        "Interaction Range": 10.0
    }
    scale_factor = 1.0
    velocity_trace = 15.
    periodic_boundary = True
    steps = 100
    test_model(params, scale_factor, velocity_trace, periodic_boundary, steps)
    # ----------------------SDA----------------------
    params = {
        "Alignment Range": 2.01,
        "Alignment Force": 0.0,
        "Interaction Force": 0.005,
        "Gradient Intensity": [
            0.0,
            0.0,
            0.0
        ],
        "Cell Ratio": [
            0.5,
            0.5,
            0.0
        ],
        "Pinned Cells": [
            "none",
            "none",
            "none"
        ],
        "Noise Intensity": 0.3,
        "Angular Inertia": 0.05,
        "Adhesion": [
            [
                1.2,
                1.4,
                0.01
            ],
            [
                1.4,
                1.8,
                0.01
            ],
            [
                0.01,
                0.01,
                0.01
            ]
        ],
        "Velocity": [
            0.05,
            0.05,
            0.05
        ],
        "Cell Density": 0.07,
        "Gradient Direction": [
            0.0,
            0.0,
            0.0
        ],
        "Interaction Range": 10.0
        }
    scale_factor = 0.5
    velocity_trace = 0.
    periodic_boundary = False
    steps = 500
    test_model(params, scale_factor, velocity_trace, periodic_boundary, steps)


if __name__ == "__main__":
    main()
