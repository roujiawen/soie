import numpy as np
from math import pi, cos, sin, ceil
if __name__ == "__main__":
    import c_code as c_model
else:
    import model.c_code as c_model

class Model(object):
    def __init__(self, params, scaling_factor=0.66, periodic_boundary=False):
        self.order_parameters = []
        self.group_angular_momentum = []
        self.params = params

        # Periodic boundary settings
        if periodic_boundary is False:
            self.tick = self.fb_tick
        else:
            self.tick = self.pb_tick

        # Adjust for scaling factor
        sf = self.scaling_factor = scaling_factor
        params["core_radius"] = 0.15 * sf
        params["Interaction Range"] *= params["core_radius"]
        params["Alignment Range"] *= params["core_radius"]

        ntypes = params['num_of_types'] = len(params["Cell Ratio"])
        for i in range(ntypes):
            params["Velocity"][i] *=sf

        # Set simulation field and grid size
        params['xlim'] = 10.
        params['ylim'] = 10.

        nop = params['num_of_particles'] = int(params["Cell Density"]*
            (params['xlim']/float(2*params["core_radius"]))*
            (params['ylim']/float(np.sqrt(3)*params["core_radius"])))

        ### Set cell types

        counts = [int(round(nop*params["Cell Ratio"][i])) for i in xrange(3)]
        counts[2] = nop - counts[0] - counts[1]
        self.type_counts = counts
        cutoff = np.array([sum(counts[:i]) for i in xrange(4)]).astype(np.int32)
        self.type_slice = [slice(cutoff[i], cutoff[i+1]) for i in xrange(3)]

        ### Set gradient values
        grad_x = np.array([np.cos(d*np.pi) * i for d, i in zip(params["Gradient Direction"], params["Gradient Intensity"])])
        grad_y = np.array([np.sin(d*np.pi) * i for d, i in zip(params["Gradient Direction"], params["Gradient Intensity"])])

        # Fix cell
        pinned = np.array([0 if x == "none" else 1 for x in params["Pinned Cells"]]).astype(np.int32)

        v0 = np.array(params["Velocity"])
        beta = np.array(params["Adhesion"])

        self.cparams = [nop, params['xlim'], params['ylim'],
            params["core_radius"], params["Interaction Range"], params["Alignment Range"], params["Angular Inertia"],
            params["Interaction Force"], params["Alignment Force"], params["Noise Intensity"],
            v0, pinned, cutoff[1:3], beta, grad_x, grad_y]

    def random_initialization(self):
        params = self.params
        nop, ntypes = params["num_of_particles"], params["num_of_types"]
        xlim, ylim = params["xlim"], params["ylim"]
        # Randomize position
        self.x = np.random.random(nop) * xlim
        self.y = np.random.random(nop) * ylim

        # Randomize velocity
        theta = np.random.random(nop) * 2 * pi
        self.dir_x = np.cos(theta)
        self.dir_y = np.sin(theta)
        # For different types
        for i in range(ntypes):
            self.dir_x[self.type_slice[i]] *= params["Velocity"][i]
            self.dir_y[self.type_slice[i]] *= params["Velocity"][i]

        # Randomize pinned shape
        for i, pinned_shape in enumerate(params["Pinned Cells"]):
            if pinned_shape != "none":
                slice_, n = self.type_slice[i], self.type_counts[i]
                if pinned_shape == "ring":
                    radius = xlim * (0.3+np.random.random(n)*0.1) # Radius = 30%-40% of field size
                    theta = 2 * np.random.random(n) * pi
                    self.x[slice_] = xlim/2. + np.cos(theta)*radius
                    self.y[slice_] = ylim/2. + np.sin(theta)*radius

                elif pinned_shape == "circle":
                    radius = xlim * 0.2 * np.random.power(2, n) # 0-20% of field size
                    theta = 2 * np.random.random(n) * pi
                    self.x[slice_] = xlim/2. + np.cos(theta)*radius
                    self.y[slice_] = ylim/2. + np.sin(theta)*radius

                elif pinned_shape == "square":
                    # radius ~ 40-50% of field size
                    side = np.random.randint(0,4,n)
                    coord = np.random.random(n)* 0.9 * xlim
                    depth = np.random.random(n)* 0.1 * xlim
                    temp_x, temp_y = np.empty(n), np.empty(n)
                    is_0 = side == 0
                    temp_x[is_0], temp_y[is_0] = depth[is_0], coord[is_0]
                    is_1 = side == 1
                    temp_x[is_1], temp_y[is_1] = xlim - depth[is_1], coord[is_1] + 0.1*ylim
                    is_2 = side == 2
                    temp_x[is_2], temp_y[is_2] = coord[is_2] + 0.1*xlim, depth[is_2]
                    is_3 = side == 3
                    temp_x[is_3], temp_y[is_3] = coord[is_3], ylim - depth[is_3]
                    self.x[slice_] = temp_x
                    self.y[slice_] = temp_y

    def fb_tick(self):
        c_model.fb_tick(*self.cparams+[self.x, self.y, self.dir_x, self.dir_y])
        self.update_global_parameters()

    def pb_tick(self):
        c_model.pb_tick(*self.cparams+[self.x, self.y, self.dir_x, self.dir_y])
        self.update_global_parameters()

    def update_global_parameters(self):
        params = self.params
        nop, ntypes, v0 = params['num_of_particles'], params["num_of_types"], params["Velocity"]
        rGr_x = np.sum(self.x)/float(nop)
        rGr_y = np.sum(self.y)/float(nop)
        r_x = self.x - rGr_x
        r_y = self.y - rGr_y
        v_x = np.empty(nop)
        v_y = np.empty(nop)
        for i in range(ntypes):
            v_x[self.type_slice[i]] = self.dir_x[self.type_slice[i]]/v0[i]
            v_y[self.type_slice[i]] = self.dir_y[self.type_slice[i]]/v0[i]
        product = np.cross([r_x, r_y], [v_x, v_y], axisa=0, axisb=0)
        self.group_angular_momentum.append(np.sum(product)/float(nop))

        x_sum = np.sum(v_x)
        y_sum = np.sum(v_y)
        d = (x_sum*x_sum + y_sum*y_sum)**0.5
        self.order_parameters.append(d/float(nop))

    def set(self, state, properties):
        """
        coords, vlcty: [[[x],[y]],[blue], [green]]
        """
        ntypes = self.params["num_of_types"]
        coords, vlcty = state
        self.order_parameters, self.group_angular_momentum = properties

        self.x = np.concatenate([coords[i][0] for i in range(ntypes)])
        self.y = np.concatenate([coords[i][1] for i in range(ntypes)])
        self.dir_x = np.concatenate([vlcty[i][0] for i in range(ntypes)])
        self.dir_y = np.concatenate([vlcty[i][1] for i in range(ntypes)])

    def get(self):
        ntypes = self.params["num_of_types"]
        x, y, dir_x, dir_y = self.x, self.y, self.dir_x, self.dir_y
        slices = self.type_slice
        coords = []
        vlcty = []

        for i in xrange(ntypes):
            coords.append([list(x[slices[i]]), list(y[slices[i]])])
            vlcty.append([list(dir_x[slices[i]]), list(dir_y[slices[i]])])

        return (coords, vlcty)

def main():
    import time
    import matplotlib.pyplot as plt
    start_time = time.time()

    params = {'Gradient Intensity': [0.0, 0.0, 1.52],
    'Cell Density': 0.5,
    'Angular Inertia': 1.,
    'Alignment Force': 2.5284,
    'Pinned Cells': ['none', 'none', 'none'],
    'Velocity': [0.085, 0.034, 0.086],
    'Gradient Direction': [0.79, 0.47, 1.83],
    'Alignment Range': 11.1,
    'Adhesion': [[3.25, 1.1300000000000001, 1.15], [1.1300000000000001, 1.36, 4.0], [1.15, 4.0, 1.48]],
    'Interaction Force': 4.7298,
    'Cell Ratio': [0.33, 0.33, 0.34],
    'Noise Intensity': 0.28,
    'Interaction Range': 10.2}

    m = Model(params)
    m.random_initialization()
    for i in range(25):
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

    plt.show()


if __name__ == "__main__":
    import sys
    main()
