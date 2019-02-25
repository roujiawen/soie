from Tkinter import *
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.ticker import MaxNLocator
from common.styles import *
from common.tools import counts2slices

class PlotWidget(object):
    """
    Methods
        grid
        subplots_adjust
        axis
        set_axis_limits
        plot
        scatter
        add_collection
        clear
        show

    """
    def __init__(self, parent, figsize=(5,5), dpi=100,
            xlim=None, ylim=None, axis=None, no_edge=False, bg=None):
        self.parent = parent

        self.figure = Figure(figsize=figsize)

        if no_edge:
            self.figure.subplots_adjust(left=0, bottom=0, right=1, top=1)

        self.ax = self.figure.add_subplot(111)
        if axis is not None: self.ax.axis(axis)
        if xlim is not None: self.ax.set_xlim(xlim)
        if ylim is not None: self.ax.set_ylim(ylim)
        if bg is not None:
            self.figure.patch.set_facecolor(bg)
        #self.ax.plot([0.1,19.9,19.9],[0.1,19.9,0.1],color="black")

        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.show()

        self.widget = self.canvas.get_tk_widget()

    def plot_sim(self, session, sim, dots):
        scale_factor, velocity_trace = session.sf, session.vt
        x, y, dir_x, dir_y = sim.state
        species_velocity = sim.params["Velocity"]
        n_per_species = sim.n_per_species
        colors = CELL_COLORS
        self.clear()
        circle_size = dots/100. * 3.14 * (0.08 * scale_factor)**2
        multiplier = velocity_trace[0]
        alpha = velocity_trace[1]

        for k, s in enumerate(counts2slices(n_per_species)):
            if multiplier > 0:
                segs = []
                for j in range(s.start, s.stop):
                    segs.append(((x[j], y[j]), (x[j]-dir_x[j]*multiplier*species_velocity[k],
                                          y[j]-dir_y[j]*multiplier*species_velocity[k])))
                ln_coll = LineCollection(segs, colors=colors[k], linewidths=1, alpha=alpha)
                self.add_collection(ln_coll)
            self.scatter(x[s], y[s], s=circle_size, color=colors[k],linewidths=0, alpha=CELL_ALPHA[k])

        self.axis('off')
        adjusted_limit = AXIS_LIMIT / scale_factor
        self.set_axis_limits([0, adjusted_limit], [0, adjusted_limit])
        self.draw()

    def plot_global_stats(self, session, sim):
        global_stats = sim.global_stats
        display_setting = session.global_stats_display
        self.clear()

        def process(values):
            x = range(len(values))
            if len(values)>200:
                values = values[-200:]
                x = x[-200:]
            return x, values

        linewidth = 1
        colors = ["orange","grey","blue","red","green","purple"]
        labels = ["angmomen","align","segreg-b","segreg-r","segreg-g","cluster"]
        for i, color, label in zip(range(6), colors, labels):
            if display_setting["show"][i] == 1:
                self.plot(*process(global_stats[i,:]), linewidth=linewidth,
                            color=color, label=label)
        self.legend()
        self.draw()

    def small_plot(self):
        self.figure.subplots_adjust(left=0.1, bottom=0.12, right=0.98, top=0.78)
        self.ax.set_ylim([-1.,1])
        self.ax.set_xlim([0,100])
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_visible(False)
        self.ax.spines['left'].set_visible(False)
        self.ax.tick_params(axis='both', which='major', length=0, labelsize=6)
        self.ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    def large_plot(self):
        self.figure.patch.set_facecolor("white")
        self.figure.subplots_adjust(left=0.1, bottom=0.15, right=0.98, top=0.80)
        self.ax.set_ylim([-1.,1])
        self.ax.set_xlim([0,100])
        ax = self.ax
        ax.spines['top'].set_visible(True)
        ax.spines['right'].set_visible(True)
        ax.spines['bottom'].set_visible(True)
        ax.spines['left'].set_visible(True)
        ax.tick_params(axis='both', which='major', length=2, labelsize=6)

    def legend(self):
        self.ax.legend(bbox_to_anchor=(0., 1.01, 1., .3), loc=3,
            ncol=3, mode="expand", borderaxespad=0., fontsize=6, frameon=False)

    def bind(self, *args, **kwargs):
        self.widget.bind(*args, **kwargs)

    def unbind(self, *args, **kwargs):
        self.widget.unbind(*args, **kwargs)

    def grid(self, *args, **kwargs):
        self.widget.grid(*args, **kwargs)

    def subplots_adjust(self, *args, **kwargs):
        self.figure.subplots_adjust(*args, **kwargs)

    def axis(self, *args, **kwargs):
        self.ax.axis(*args, **kwargs)

    def set_axis_limits(self, xlim, ylim):
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)

    def plot(self, *args, **kwargs):
        self.ax.plot(*args, **kwargs)

    def scatter(self, *args, **kwargs):
        self.ax.scatter(*args, **kwargs)

    def add_collection(self, *args, **kwargs):
        self.ax.add_collection(*args, **kwargs)

    def clear(self):
        self.ax.cla()

    def show(self):
        self.canvas.show()

    def draw(self):
        self.canvas.draw()
