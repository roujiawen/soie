"""This module contains the plotting widgets used across different components
of the software.

SimPlotWidget: plots the states of the agent-based simulation itself.

PropertyPlotWidget: plots the global property statistics across time.

"""

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.collections import LineCollection
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from common.parameters import FIELD_SIZE
from common.styles import CELL_ALPHA, CELL_COLORS
from common.tools import counts2slices


class SimPlotWidget(object):
    """A class for creating and updating simulation plots.

    Methods:
        plot_sim: Plot simulation given a state.
        grid, bind, unbind: Pass function calls to the Tkinter widget object.

    Attributes:
        figure: the matplotlib.figure.Figure object containing the plot.

    """
    def __init__(self, parent, large_size=False):
        """
        Parameters:
            parent (tk.Frame): The Tkinter parent of the plot widget.
            large_size (bool): If True, configure the figure to be large,
                suitable for being displayed in EditWindow. Defaults to False.

        """
        figsize = (5, 5) if large_size else (2.15, 2.15)
        figure = Figure(figsize=figsize)
        # Leave no margins
        figure.subplots_adjust(left=0, bottom=0, right=1, top=1)
        self.ax = figure.add_subplot(111)
        # Don't display axis frame
        self.ax.axis("off")
        # Integrate matplotlib Figure with Tkinter widget
        self.canvas = FigureCanvasTkAgg(figure, master=parent)
        self.canvas.show()
        self.widget = self.canvas.get_tk_widget()
        # Calculate the display size of particles
        self.part_size = (figsize[0]*100)**2  # MAYBETODO

    def plot_sim(self, session, sim):
        """Plot simulation given particle state.

        Parameters:
            session (SessionData): The object that stores application-level
                data, parameters and settings.
            sim (Simulation): The Simulation object with state data to be
                plotted.

        """
        # High-level display parameters
        scale_factor = session.sf
        multiplier, alpha = session.vt
        # Positions and directions of particles
        x_pos, y_pos, x_dir, y_dir = sim.state
        # Velocity magnitudes for each species
        species_velocity = sim.params["Velocity"]
        # Display size of particles adjusted by scale factor
        adjusted_size = self.part_size/100. * 3.14 * (0.08 * scale_factor)**2
        # Clear plot
        self.ax.cla()
        # For each species
        for k, each_slice in enumerate(counts2slices(sim.n_per_species)):
            # Plot velocity traces
            if multiplier > 0:
                segs = []
                # Add each particle's trace to the line collection
                for j in range(each_slice.start, each_slice.stop):
                    segs.append(
                        # Start coordinates
                        ((x_pos[j], y_pos[j]),
                         # End coordinates
                         (x_pos[j] - x_dir[j]*multiplier*species_velocity[k],
                          y_pos[j] - y_dir[j]*multiplier*species_velocity[k]))
                    )
                    ln_coll = LineCollection(
                        segs, colors=CELL_COLORS[k], linewidths=1, alpha=alpha
                    )
                self.ax.add_collection(ln_coll)
            # Plot particles themselves
            self.ax.scatter(
                x_pos[each_slice], y_pos[each_slice], s=adjusted_size,
                color=CELL_COLORS[k], linewidths=0, alpha=CELL_ALPHA[k]
            )
        self.update_axis_limits(scale_factor)
        self.ax.axis('off')
        self.canvas.draw()

    def update_axis_limits(self, scale_factor):
        """Adjust limits of the plot according to scale factor."""
        adjusted_limit = FIELD_SIZE / scale_factor
        xlim = ylim = (0, adjusted_limit)
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)

    def grid(self, *args, **kwargs):
        """Pass .grid() function call to the Tkinter widget to simplify code.
        """
        self.widget.grid(*args, **kwargs)

    def bind(self, *args, **kwargs):
        """Pass .bind() function call to the Tkinter widget to simplify code.
        """
        self.widget.bind(*args, **kwargs)

    def unbind(self, *args, **kwargs):
        """Pass .unbind() function call to the Tkinter widget to simplify code.
        """
        self.widget.unbind(*args, **kwargs)


class PropertyPlotWidget(object):
    """A class for creating and updating global property plots.

    Methods:
        plot_global_stats: Plot the trajectories of global properties of a
            simulation over time.
        grid: Pass function calls to the Tkinter widget object.

    """
    def __init__(self, parent, large_size=False, bg=None):
        """
        Parameters:
            parent (tk.Frame): The Tkinter parent of the plot widget.
            large_size (bool): If True, configure the figure to be large,
                suitable for being displayed in EditWindow. Defaults to False.
            bg (string): The background color of the plot.
        """
        figsize = (5, 1.6) if large_size else (2.5, 1.3)
        figure = Figure(figsize=figsize)
        # Set plot background color
        figure.patch.set_facecolor(bg if bg is not None else "white")
        ax = figure.add_subplot(111)
        ax.set_ylim([-1., 1])
        ax.set_xlim([0, 100])

        if large_size:
            # Set plot margins
            figure.subplots_adjust(left=0.1, bottom=0.15, right=0.98, top=0.80)
            # Adjust tick size
            ax.tick_params(axis='both', which='major', length=2, labelsize=6)
        else:
            # Set plot margins
            figure.subplots_adjust(left=0.1, bottom=0.12, right=0.98, top=0.78)
            # Hide axis spines
            for each_side in ["top", "right", "bottom", "left"]:
                ax.spines[each_side].set_visible(False)
            # Adjust tick size and interval
            ax.tick_params(axis='both', which='major', length=0, labelsize=6)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        # Integrate matplotlib Figure and Tkinter canvas widget
        self.canvas = FigureCanvasTkAgg(figure, master=parent)
        self.canvas.show()
        self.widget = self.canvas.get_tk_widget()
        self.ax = ax

    def plot_global_stats(self, session, sim):
        """Plot global properties over time.

        Parameters:
            session (SessionData): The object that stores application-level
                data, parameters and settings.
            sim (Simulation): The object with global property data
                to be plotted.

        """
        global_stats = sim.global_stats
        display_setting = session.global_stats_display
        ax = self.ax
        # Clear plot
        ax.cla()

        def process(values):
            """Process raw data and return x, y pairs for line plot. Truncate
            data so that only 200 time steps are displayed.
            """
            x_coords = range(len(values))
            if len(values) > 200:
                values = values[-200:]
                x_coords = x_coords[-200:]
            return x_coords, values
        linewidth = 1
        # Colors and labels for different global properties
        colors = ["orange", "grey", "blue", "red", "green", "purple"]
        labels = ["angmomen", "align", "segreg-b", "segreg-r", "segreg-g",
                  "cluster"]
        # For each global property
        for i, color, label in zip(range(6), colors, labels):
            # If setting says that the specific property should be displayed
            if display_setting["show"][i] == 1:
                ax.plot(*process(global_stats[i, :]), linewidth=linewidth,
                        color=color, label=label)
        # Adjust legend position
        ax.legend(bbox_to_anchor=(0., 1.01, 1., .3), loc=3, ncol=3,
                  mode="expand", borderaxespad=0., fontsize=6, frameon=False)
        # If nothing displayed, defaults to reasonable axis limit
        if not global_stats[0, :]:
            ax.set_ylim([-1., 1])
        self.canvas.draw()

    def grid(self, *args, **kwargs):
        """Pass .grid() function call to the Tkinter widget to simplify code.
        """
        self.widget.grid(*args, **kwargs)
