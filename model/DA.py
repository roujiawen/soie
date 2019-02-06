import numpy as np
from math import pi, cos, sin, ceil, sqrt
from collections import OrderedDict

if __name__ == "__main__":
    import c_code as c_model
else:
    import model.c_code as c_model

CORE_RADIUS = 0.1
FIELD_SIZE = 10.0
N_GLOBAL_STATS = 2

class Model(object):
    def __init__(self, params, scale_factor=2., periodic_boundary=False):
        self.order_parameters = []
        self.group_angular_momentum = []
        self.user_params = params

        # Periodic boundary settings
        if periodic_boundary is False:
            self.tick = self.fb_tick
        else:
            self.tick = self.pb_tick

        self.internal_params = self.gen_internal_params(scale_factor)

        self.pinned_num = np.sum(self.internal_params["pinned"])
        self.periodic_boundary = periodic_boundary

    def gen_internal_params(self, scale_factor):
        """
        Formatting user-provided parameters into internal parameters accepted
        by the C++ program.
        """
        # Name shortening for frequent variables
        uprm = self.user_params

        # FORMATTING INTERNAL PARAMS
        # Particle core radius
        r0_x_2 = CORE_RADIUS * 2
        # Calculate number of particles
        max_num_particles = 10**4/(2*sqrt(3)) / (scale_factor)**2
        nop = int(uprm['Cell Density'] * max_num_particles)
        # Calculate actual field size (scaled)
        xlim = ylim = FIELD_SIZE / float(scale_factor)
        # Calculate force and alignment radii
        r1 = uprm['Interaction Range'] * CORE_RADIUS
        ra = uprm['Alignment Range'] * CORE_RADIUS
        # Just copying
        inert = uprm['Angular Inertia']
        f0 = uprm['Interaction Force']
        fa = uprm['Alignment Force']
        nint = uprm['Noise Intensity']
        # Change type
        v0 = np.array(uprm["Velocity"])
        beta = np.array(uprm["Adhesion"])
        # Pinned = 0 (none) or 1 (fixed)
        pinned = np.array([0 if x == "none" else 1 for x in uprm["Pinned Cells"]]
                          ).astype(np.int32)
        # Convert ratio to cutoff
        counts = [int(round(nop*each)) for each in uprm["Cell Ratio"][:2]]
        counts.append(nop - sum(counts)) # Last type
        cutoff = np.array([sum(counts[:i+1]) for i in range(len(counts))]
                          ).astype(np.int32) # Cumulative
        # Gradient from polar to cartesian
        grad_x = np.array([np.cos(d*pi) * i for d, i
                in zip(uprm["Gradient Direction"], uprm["Gradient Intensity"])])
        grad_y = np.array([np.sin(d*pi) * i for d, i
                in zip(uprm["Gradient Direction"], uprm["Gradient Intensity"])])

        names = [
            'nop', 'xlim', 'ylim',
            'r0_x_2', 'r1', 'ra', # radii
            'inert', 'f0', 'fa','nint', # strengths
            'v0', 'pinned', 'cutoff', 'beta', 'grad_x', 'grad_y' # arrays
            ]
        internal_params = OrderedDict([(x, locals()[x]) for x in names])
        return internal_params

    def init_particles_state(self):
        """
        Initialize a system of particles given params
        """
        iprm, uprm = self.internal_params, self.user_params
        nop, xlim, ylim = iprm['nop'], iprm['xlim'], iprm['ylim']
        cutoff = iprm['cutoff']

        # Randomize position
        pos_x = np.random.random(nop) * xlim
        pos_y = np.random.random(nop) * ylim

        # Randomize velocity
        theta = np.random.random(nop) * 2 * pi
        dir_x = np.cos(theta)
        dir_y = np.sin(theta)

        # For different types
        bd = [0] + list(iprm['cutoff'])
        types = [slice(bd[i-1], bd[i]) for i in range(1, len(bd))]
        # for type_, v in zip(types, iprm["v0"]):
        #     x_velocity[type_] *= v
        #     y_velocity[type_] *= v

        # Randomize pinned shape
        for type_, pinned_shape in zip(types, uprm["Pinned Cells"]):
            if pinned_shape != "none":
                n = type_.stop - type_.start # length of the slice
                dir_x[type_] = 0.
                dir_y[type_] = 0.
                if pinned_shape == "ring":
                    # Radius = 30%-40% of field size
                    radius = xlim * (0.3+np.random.random(n)*0.1)
                    theta = 2 * np.random.random(n) * pi
                    pos_x[type_] = xlim/2. + np.cos(theta)*radius
                    pos_y[type_] = ylim/2. + np.sin(theta)*radius

                elif pinned_shape == "circle":
                    # 0-20% of field size
                    radius = xlim * 0.2 * np.random.power(2, n)
                    theta = 2 * np.random.random(n) * pi
                    pos_x[type_] = xlim/2. + np.cos(theta)*radius
                    pos_y[type_] = ylim/2. + np.sin(theta)*radius

                elif pinned_shape == "square":
                    # radius ~ 40-50% of field size
                    side = np.random.randint(0,4,n)
                    coord = np.random.random(n)* 0.9 * xlim
                    depth = np.random.random(n)* 0.1 * xlim
                    temp_x, temp_y = np.empty(n), np.empty(n)
                    is_0 = side == 0
                    temp_x[is_0], temp_y[is_0] = depth[is_0], coord[is_0]
                    is_1 = side == 1
                    temp_x[is_1], temp_y[is_1] = xlim-depth[is_1], coord[is_1]+0.1*ylim
                    is_2 = side == 2
                    temp_x[is_2], temp_y[is_2] = coord[is_2]+0.1*xlim, depth[is_2]
                    is_3 = side == 3
                    temp_x[is_3], temp_y[is_3] = coord[is_3], ylim - depth[is_3]
                    pos_x[type_] = temp_x
                    pos_y[type_] = temp_y

        self.x, self.y, self.dir_x, self.dir_y = pos_x, pos_y, dir_x, dir_y

    def fb_tick(self):
        c_model.fb_tick(*self.internal_params.values()+[self.x, self.y, self.dir_x, self.dir_y])
        self.calc_global_stats()

    def pb_tick(self):
        c_model.pb_tick(*self.internal_params.values()+[self.x, self.y, self.dir_x, self.dir_y])
        self.calc_global_stats()

    def calc_global_stats(self):
        """
        INPUT:  cparams: list of int/float/nparrays
                state : list of four arrays
        OUTPUT: global_stats_slice : np.array((N_GLOBAL_STATS))
                    #0: Group angular momentum
                    #1: Orderness
        """
        global_stats_slice = np.empty((N_GLOBAL_STATS))

        pos_x, pos_y, dir_x, dir_y = self.x, self.y, self.dir_x, self.dir_y
        iprm = self.internal_params
        nop, cutoff, v0 = iprm["nop"], iprm["cutoff"], iprm["v0"]
        xlim, ylim = iprm["xlim"], iprm["ylim"]

        # Group angular momentum

        # center of mass
        if self.periodic_boundary:
            theta_x = 2 * pi * pos_x / xlim
            theta_y = 2 * pi * pos_y / ylim
            theta_x_cos = np.mean(np.cos(theta_x))
            theta_x_sin = np.mean(np.sin(theta_x))
            theta_y_cos = np.mean(np.cos(theta_y))
            theta_y_sin = np.mean(np.sin(theta_y))
            rGr_x = (np.arctan2(-theta_x_sin, -theta_x_cos) + pi) * xlim / (2 * pi)
            rGr_y = (np.arctan2(-theta_y_sin, -theta_y_cos) + pi) * ylim / (2 * pi)
        else:
            rGr_x = np.sum(pos_x)/float(nop)
            rGr_y = np.sum(pos_y)/float(nop)
        r_x = pos_x - rGr_x
        r_y = pos_y - rGr_y
        product = np.cross([r_x, r_y], [dir_x, dir_y], axisa=0, axisb=0)
        global_stats_slice[0] = np.sum(product)/float(nop)

        # Orderness
        x_sum = np.sum(dir_x)
        y_sum = np.sum(dir_y)
        d = (x_sum*x_sum + y_sum*y_sum)**0.5
        global_stats_slice[1] = d/(float(nop) - self.pinned_num)

        self.group_angular_momentum.append(global_stats_slice[0])
        self.order_parameters.append(global_stats_slice[1])

    def set(self, state, properties):
        """
        coords, vlcty: [[[x],[y]],[blue], [green]]
        """
        ntypes = len(self.internal_params["cutoff"])
        coords, vlcty = state
        self.order_parameters, self.group_angular_momentum = properties

        self.x = np.concatenate([coords[i][0] for i in range(ntypes)])
        self.y = np.concatenate([coords[i][1] for i in range(ntypes)])
        self.dir_x = np.concatenate([vlcty[i][0] for i in range(ntypes)])
        self.dir_y = np.concatenate([vlcty[i][1] for i in range(ntypes)])

    def get(self):
        cutoff = self.internal_params["cutoff"]
        x, y, dir_x, dir_y = self.x, self.y, self.dir_x, self.dir_y
        coords = []
        vlcty = []

        start_index = 0
        for i, end_index in enumerate(cutoff):
            coords.append([list(x[start_index:end_index]), list(y[start_index:end_index])])
            vlcty.append([list(dir_x[start_index:end_index]), list(dir_y[start_index:end_index])])
            start_index = end_index

        return (coords, vlcty)

def main():
    import time
    import matplotlib.pyplot as plt
    start_time = time.time()

    params = {'Gradient Intensity': [0., 0.0, 1.52],
    'Cell Density': 0.5,
    'Angular Inertia': 1.,
    'Alignment Force': 0.,
    'Pinned Cells': ['none', 'none', 'none'],
    'Velocity': [0.085, 0.034, 0.086],
    'Gradient Direction': [0.79, 0.47, 1.83],
    'Alignment Range': 11.1,
    'Adhesion': [[3.25, 1.1300000000000001, 1.15], [1.1300000000000001, 1.36, 4.0], [1.15, 4.0, 1.48]],
    'Interaction Force': 5.,
    'Cell Ratio': [1.0, 0, 0],
    'Noise Intensity': 0.28,
    'Interaction Range': 50.2}

    sf = 1.0
    m = Model(params, scale_factor=sf, periodic_boundary=True)
    m.init_particles_state()
    for i in range(50):
        if i % 100 == 0:
            print "step", i
        m.tick()

    print("--- %s seconds ---" % (time.time() - start_time))

    coords, vlcty = m.get()
    plt.figure()
    colors = ["blue", "red", "green"]
    multiplier = 10
    for i, pair in enumerate(coords):
        """for j in range(len(pair[0])):
            x = pair[0][j]
            y = pair[1][j]
            plt.plot([x, x-vlcty[i][0][j]*multiplier],[y, y-vlcty[i][1][j]*multiplier], color ="grey")"""
        plt.scatter(pair[0], pair[1], s=5, color=colors[i])

    plt.xlim(0, 10./sf)
    plt.ylim(0, 10./sf)
    plt.show()


if __name__ == "__main__":
    import sys
    main()
