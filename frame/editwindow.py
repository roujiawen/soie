"""This module contains EditWindow and its UI subcomponents.
"""

import Tkinter as tk
from copy import copy

from common.parameters import PARAM
from common.plotting import PropertyPlotWidget, SimPlotWidget
from common.styles import (BODY_COLOR, BODY_FONT, BUTTON_X_MARGIN,
                           CELL_COLORS, CELL_TYPE_LABELS, EDIT_BODY_COLOR,
                           EDIT_BODY_FONT, EDIT_COLOR_FONT, HEADER_COLOR,
                           HEADER_FONT)
from common.tools import fit_into
from frame.top import AddStepsWidget


class EWSingleEntry(tk.Entry):
    """A UI component containing a single entry widget with validation.

    Methods:
        set_value: Set the value (float) associated with the entry box.
        get_value: Get the value from the entry box.

    Validation:
        Real-time: Can enter "", ".", or float
        <Return> or <FocusOut>: If not float, revert; otherwise
            force input to be between ["from", "to"] and rounded
    """
    def __init__(self, parent, info, value):
        """
        Parameters:
            parent (tk.Frame): The Tkinter parent of this widget.
            info (dict): Contains specifications for the model parameter.
            value: Initial value for the entry box.

        """
        tk.Entry.__init__(self, parent, width=6)
        # Set the maximally allowed input length for before and after decimal
        if info["range"][1] != float("inf"):
            self.maxlen = [len(str(int(info["range"][1]))), info["roundto"]]
        else:
            self.maxlen = [float("inf"), info["roundto"]]

        def is_okay(value):
            """Validate whether entered value is permissible."""
            if value in ["", "."]:
                # Allow empty string and single decimal point
                return True
            try:
                # Make sure the value can be converted to a valid float
                float(value)
            except ValueError:
                return False
            # Restrict the length of input before and after decimal
            splitted = value.split(".")
            if any(len(splitted[i]) > self.maxlen[i]
                   for i in range(len(splitted))):
                return False
            return True
        # Register validation function
        vcmd = (self.register(is_okay), '%P')
        self.config(validate="all", validatecommand=vcmd)
        # If no range restriction is specified, at least must be possitive
        if "range" in info:
            self.fit_n_round = lambda x: round(fit_into(x, *info["range"]),
                                               info["roundto"])
        else:
            self.fit_n_round = lambda x: round(fit_into(x, 0., float("inf")),
                                               info["roundto"])
        # Check and update value following these actions
        self.bind('<Return>', self._check_value)
        self.bind('<FocusOut>', self._check_value)
        # Initiate value
        self.value = 0.
        self.set_value(value)

    def _check_value(self, event=None):
        """Make sure the newly entered value is a valid float, otherwise
        revert to the last stored value."""
        try:
            # If input is a valid float, update stored value
            value = float(self.get())
            self.set_value(value)
        except ValueError:
            # Otherwise revert back
            self.set_value(self.value)

    def set_value(self, value):
        """Update stored value and refresh display."""
        self.value = self.fit_n_round(value)
        self.delete(0, tk.END)
        self.insert(0, self.value)

    def get_value(self):
        """Return stored value after checking its validity."""
        self._check_value()
        return self.value


class EWRatioEditor(tk.Frame):
    """A UI component containing three entry widgets that allow the editing
    of ratio parameters.

    Methods:
        set_value: Set values (a list of three floats) for the entry boxes.
        get_value: Get values from the entry boxes.

    """
    def __init__(self, parent, name, info, values):
        """
        Parameters:
            parent (tk.Frame): The Tkinter parent of this widget.
            name (str): Name of the parameter to be displayed.
            info (dict): Contains specifications for this model parameter.
            values: Initial values for the entry boxes

        """
        tk.Frame.__init__(self, parent)
        # Set the maximally allowed input length for before and after decimal
        if info["range"][1] != float("inf"):
            self.maxlen = [len(str(int(info["range"][1]))), info["roundto"]]
        else:
            self.maxlen = [float("inf"), info["roundto"]]
        # Create rounding function
        self.round = lambda x: round(x, info["roundto"])
        # Set restrictions on the ratios
        self.limits = info["range"]
        # Make label
        self.label = tk.Label(self, text=name, font=EDIT_BODY_FONT,
                              fg=EDIT_BODY_COLOR, width=18)
        self.label.grid(row=0, column=0)
        # Register validation function
        vcmd = (self.register(self._is_okay), '%P')
        # Make entry boxes and colons between each pair
        self.widgets = []
        for i in range(5):
            if i % 2 == 0:
                # Create entry boxes when i is an even number
                widget = tk.Entry(
                    self, width=6, validate="all", validatecommand=vcmd,
                    font=EDIT_BODY_FONT, fg=CELL_COLORS[i/2])
                widget.grid(row=0, column=i+1)
                # Check and update value following these actions
                widget.bind('<Return>', self._update_entries)
                widget.bind('<FocusOut>', self._if_editing)
                self.widgets.append(widget)
            else:
                # Create colons when i is odd
                colon = tk.Label(self, text=":",
                                 font=EDIT_BODY_FONT, fg=EDIT_BODY_COLOR)
                colon.grid(row=0, column=i+1)
        # Set layout
        for i, size in enumerate([60, 2, 60, 2, 60]):
            self.columnconfigure(i+1, minsize=size)
        # Initiate values
        self.values = [0]*3
        self.set_value(values)

    def _is_okay(self, value):
        """Validate whether entered value is permissible."""
        if value in ["", "."]:
            # Allow empty string and single decimal point
            return True
        try:
            # Make sure the value can be converted to a valid float
            float(value)
        except ValueError:
            return False
        # Restrict the length of input before and after decimal
        splitted = value.split(".")
        if any(len(splitted[i]) > self.maxlen[i]
               for i in range(len(splitted))):
            return False
        return True

    @property
    def _widget_values(self):
        try:
            return [float(_.get()) for _ in self.widgets]
        except ValueError:
            return False

    def _revert(self):
        self.set_value(self.values)

    def _first_step_check(self):
        wvalues = self._widget_values
        if not wvalues:
            self._revert()
            return "skip"
        return None

    def _if_editing(self, event=None):
        if self.focus_get() not in self.widgets:
            self._update_entries()
        else:
            self._first_step_check()

    def _update_entries(self, event=None):
        if self._first_step_check() == "skip":
            return
        wvalues = self._widget_values
        sum_ = float(sum(wvalues))
        if sum_ == 0:
            self._revert()
            return
        # Normalize
        wvalues = [_/sum_ for _ in wvalues]
        # Fit green ratio into limits
        green_min, green_max = self.limits[2], self.limits[3]
        wvalues[2] = self.round(fit_into(wvalues[2], green_min, green_max))

        if wvalues[1] == 0:
            ratio = self.limits[1]
        else:
            ratio = fit_into(wvalues[0]/wvalues[1],
                             self.limits[0], self.limits[1])
        # Normalize the rest
        rest = 1 - wvalues[2]
        if ratio == float("inf"):
            wvalues[0] = rest
            wvalues[1] = 0
        else:
            wvalues[1] = self.round(rest/(1.0+ratio))
            wvalues[0] = rest - wvalues[1]
        self.set_value(wvalues)

    def set_value(self, values):
        """Update stored values and refresh display."""
        for i in range(3):
            self.values[i] = self.round(values[i])
            self.widgets[i].delete(0, tk.END)
            self.widgets[i].insert(0, self.values[i])

    def get_value(self):
        """Return stored value after checking that its validity."""
        self._update_entries()
        return self.values


class EWQualitativeEditor(tk.Frame):
    """A UI component containing three dropdown menu widgets that allow the
    user to edit parameters that are qualitative/categorical.

    Methods:
        set_value: Set values (a list of three strings) for the dropdown
            menus.
        get_value: Get values from the dropdown menus.

    """
    def __init__(self, parent, name, info, values):
        """
        Parameters:
            parent (tk.Frame): The Tkinter parent of this widget.
            name (str): Name of the parameter to be displayed.
            info (dict): Contains specifications for this model parameter.
            values: Initial values for the dropdown menus.

        """
        tk.Frame.__init__(self, parent)
        # Get allowed choices
        choices = info["range"]
        # Make label
        self.name = name
        self.label = tk.Label(self, text=name, font=EDIT_BODY_FONT,
                              fg=EDIT_BODY_COLOR, width=18)
        self.label.grid(row=0, column=0)
        # Initiate Tkinter control variable for chosen option
        self.choice = [tk.StringVar() for _ in range(3)]
        self.menu = [tk.OptionMenu(self, _, *__)
                     for _, __ in zip(self.choice, choices)]
        # Set layout
        for i, each in enumerate(self.menu):
            each.config(width=7, font=EDIT_BODY_FONT)
            each.grid(row=0, column=i+1, padx=0)
        # Initiate values
        self.set_value(values)

    def set_value(self, values):
        """Update chosen options with given values."""
        for each, value in zip(self.choice, values):
            each.set(value)

    def get_value(self):
        """Return stored chosen options."""
        return [_.get() for _ in self.choice]


class EWMainParamEditor(tk.Frame):
    """A UI component group that contains an entry box and a slider, allowing
    the edit of a main parameter.

    Methods:
        set_value: Set the value (float) associated with the main parameter.
        get_value: Get the value from the main parameter.

    """
    def __init__(self, parent, text, info, value, small_size=False):
        """
        Parameters:
            parent (tk.Frame): The Tkinter parent of this widget.
            text (str): Name of the parameter to be displayed.
            info (dict): Contains specifications for the main parameter.
            value: Initial value for the main parameter.

        """
        if small_size:
            length = 100
            width = 9
            font = EDIT_COLOR_FONT
        else:
            length = 150
            width = 20
            font = None
        tk.Frame.__init__(self, parent)
        # Set the maximally allowed input length for before and after decimal
        if info["range"][1] != float("inf"):
            self.maxlen = [len(str(int(info["range"][1]))), info["roundto"]]
        else:
            self.maxlen = [float("inf"), info["roundto"]]
        # Make label widget
        label = tk.Label(self, text=text, width=width)
        label.grid(row=0, column=0)
        if font is not None:
            label.config(font=font)
        # Set rounding, resolution of scale widget, lower and upper bounds
        self.round = lambda x: round(x, info["roundto"])
        resolution = info["resolution"]
        from_, to = info["range"]
        self.fit_into = lambda x: fit_into(x, from_, to)
        # Register validation function
        vcmd = (self.register(self._is_okay), '%P')
        # Make entry widget
        self.entry = tk.Entry(self, width=6, validate="all",
                              validatecommand=vcmd)
        self.entry.grid(row=0, column=1)
        # Make scale (slider) widget
        self.scale = tk.Scale(
            self, from_=from_, to=to, resolution=resolution,
            orient=tk.HORIZONTAL, sliderlength=15, width=15, length=length,
            command=self._update_entry, showvalue=0)
        self.scale.grid(row=0, column=2, padx=5)
        # Check and update value following these actions
        self.entry.bind('<Return>', self._update_scale)
        self.entry.bind('<FocusOut>', self._update_scale)
        # Group widgets and set layout
        self.widgets = [label, self.entry]
        for each in self.widgets:
            each.config(fg=EDIT_BODY_COLOR, font=EDIT_BODY_FONT)
        # Initiate value
        self.set_value(value)

    def _is_okay(self, value):
        """Validate whether entered value is permissible."""
        if value in ["", "."]:
            # Allow empty string and single decimal point
            return True
        try:
            # Make sure the value can be converted to a valid float
            float(value)
        except ValueError:
            return False
        # Restrict the length of input before and after decimal
        splitted = value.split(".")
        if any(len(splitted[i]) > self.maxlen[i]
               for i in range(len(splitted))):
            return False
        return True

    def _update_entry(self, event=None):
        """Peg the entry widget's value to the scale value."""
        scale_value = float(self.scale.get())
        self.set_value(scale_value)

    def _update_scale(self, event=None):
        try:
            # If input is a valid float, update stored value
            entry_value = float(self.entry.get())
            self.set_value(entry_value)
        except ValueError:
            # Otherwise revert back
            self._update_entry()

    def set_value(self, value):
        """Update stored value and refresh display."""
        self.value = self.round(self.fit_into(value))
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.value)
        self.scale.set(self.value)

    def get_value(self):
        """Return stored value after checking its validity."""
        self._update_scale()
        return self.value


class EWCellParamEditor(tk.Frame):
    """A UI component group that contains an entry box and a slider for each
    cell species (three in total), allowing the edit of parameters specific
    to each cell type.

    Methods:
        set_value: Propagate given values (a list of three floats) to
            parameter widgets.
        get_value: Get values from the parameter widgets.

    """
    def __init__(self, parent, text, info, values):
        """
        Parameters:
            parent (tk.Frame): The Tkinter parent of this widget.
            text (str): Name of the parameter to be displayed.
            info (dict): Contains specifications for this parameter.
            value: Initial values for this parameter.

        """
        tk.Frame.__init__(self, parent)
        # Make label
        self.label = tk.Label(self, text=text, fg=EDIT_BODY_COLOR,
                              font=EDIT_BODY_FONT, width=18)
        self.label.grid(column=0, row=0, padx=0)
        # Make one param entry box for each cell type
        info_copy = copy(info)
        self.widgets = []
        for i, name in enumerate(CELL_TYPE_LABELS):
            info_copy["range"] = info["range"][i]
            widget = EWMainParamEditor(self, name, info_copy,
                                       values[i], small_size=True)
            widget.grid(column=1, row=i, padx=0)
            self.widgets.append(widget)

    def set_value(self, values):
        """Propagate given values to widgets."""
        for each, value in zip(self.widgets, values):
            each.set_value(value)

    def get_value(self):
        """Return a list of values from widgets."""
        return [_.get_value() for _ in self.widgets]


class EWInteractionParamEditor(tk.Frame):
    """A UI component group that contains an entry box for each pair-wise
    interaction among cell species, allowing the edit of parameters specific
    to each cell species pair.

    Methods:
        set_value: Propagate given values (3x3 items) to parameter
            widgets (3+2+1 items).
        get_value: Get values from the parameter widgets.

    Data structure for the parameter is a symmetrical 3x3 matrix (representing
        symmetrical interactions):
        [F_11  F_12  F_13]
        [F_21  F_22  F_23]
        [F_31  F_32  F_33]
    However, there are only 3+2+1 widgets for the purpose of editing these
        values:
        [F_11  F_12  F_13]
              [F_22  F_23]
                    [F_33]

    """
    def __init__(self, parent, text, info, values):
        """
        Parameters:
            parent (tk.Frame): The Tkinter parent of this widget.
            text (str): Name of the parameter to be displayed.
            info (dict): Contains specifications for this parameter.
            value: Initial values for this parameter.

        """
        tk.Frame.__init__(self, parent)
        self.info = info
        # Make label
        self.label = tk.Label(self, text=text)
        self.label.grid(row=0, column=0, columnspan=4, sticky="w")
        # Make header
        cell_types = CELL_TYPE_LABELS
        self.header = [tk.Label(self, text=_, fg=EDIT_BODY_COLOR,
                                font=EDIT_COLOR_FONT)
                       for _ in [""]+cell_types]
        for i, each in enumerate(self.header):
            each.grid(row=1, column=i, sticky="w")

        # Make table body
        self.row_headers = [tk.Label(self, text=_, fg=EDIT_BODY_COLOR,
                                     font=EDIT_COLOR_FONT) for _ in cell_types]
        self.entries = [[], [], []]
        info_copy = copy(info)
        for i in range(3):
            for j in range(3-i):
                info_copy["range"] = info["range"][i][j]
                self.entries[i].append(
                    EWSingleEntry(self, info_copy, values[i][i+j]))
        for i in range(3):
            self.row_headers[i].grid(row=2+i, column=0, sticky="w")
            for j in range(3-i):
                self.entries[i][j].grid(row=2+i, column=1+i+j, sticky="w")
        # Set layout
        for i in range(4):
            self.columnconfigure(i, minsize=50)
        # Set color and font
        widgets = [self.label]+self.entries[0]+self.entries[1]+self.entries[2]
        for each in widgets:
            each.config(bg=parent.cget("bg"), fg=EDIT_BODY_COLOR,
                        font=EDIT_BODY_FONT)

    def set_value(self, matrix):
        """Propagate values in the given matrix to widgets."""
        for i in range(3):
            for j in range(3-i):
                self.entries[i][j].set_value(matrix[i][i+j])

    def get_value(self):
        """Return a symmetrical matrix from values of widgets."""
        mtrx = [[0]*3 for _ in range(3)]
        for i in range(3):
            for j in range(3-i):
                mtrx[i][i+j] = mtrx[i+j][i] = self.entries[i][j].get_value()
        return mtrx


class EditFrame(tk.Frame):
    """A panel for the user to manually adjust the parameters of a simulation.

    Methods:
        update_params: Update the display of parameters in edit widgets.
        update_step: Update the display of the current time step in the
            simulation.
        unbind_: Untie the link between changes in model data and display
            update. Used when the frame gets destroyed.
    """
    def __init__(self, parent, session, sim):
        """
        Parameters:
            parent (tk.Frame): The Tkinter parent of this widget.
            session (SessionData): The object that stores application-level
                data, parameters and settings.
            sim (Simulation): The Simulation object associated with this
                EditWindow.
        """
        tk.Frame.__init__(self, parent)
        self.sim = sim
        self.session = session
        sim.bind("params", self.update_params, first=True)
        sim.bind("step", self.update_step, first=True)
        params = copy(sim.params)
        param_info = session.param_info
        total_columns = 2
        header_space = 7
        left_space = 8
        # Display current time step
        self.steps_strvar = tk.StringVar()
        self.update_step()
        temp = tk.Frame(self)
        self.steps_label = tk.Label(
            temp, textvariable=self.steps_strvar, anchor="w",
            bg=self.cget("bg"), fg=BODY_COLOR, font=BODY_FONT)
        self.restart_button = tk.Button(
            temp, text=u"\u21ba", command=self._restart, padx=5)
        self.steps_label.grid(row=0, column=0, sticky="e")
        self.restart_button.grid(row=0, column=1, sticky="w")
        temp.grid(row=0, column=0, ipady=3, padx=(10, 0), sticky="w")
        self.steps_widget = AddStepsWidget(self, sim.add_steps, text="+", )
        self.steps_widget.grid(row=0, column=1, padx=(0, 10), sticky="e")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        # Make widgets for main params
        self.widgets = {}
        self.main_label = tk.Label(self, text="Main Parameters")
        self.main_label.grid(columnspan=total_columns, sticky="w",
                             padx=left_space, pady=(header_space, 0))
        for name in PARAM["main"]:
            self.widgets[name] = EWMainParamEditor(
                self, name, param_info[name], params[name])
            self.widgets[name].grid(columnspan=total_columns, padx=0)
        # Make widgets for cell params
        self.cell_label = tk.Label(self, text="Cell Parameters")
        self.cell_label.grid(columnspan=total_columns, sticky="w",
                             pady=(header_space, 0), padx=left_space)
        for name in PARAM["cell"]:
            info = param_info[name]
            if "type" not in info:
                self.widgets[name] = EWCellParamEditor(
                    self, name, info, params[name])
                self.widgets[name].grid(columnspan=total_columns, sticky="w")
            elif info["type"] == "ratio":
                self.widgets[name] = EWRatioEditor(
                    self, name, info, params[name])
                self.widgets[name].grid(columnspan=total_columns, sticky="w")
            elif info["type"] == "qualitative":
                self.widgets[name] = EWQualitativeEditor(
                    self, name, info, params[name])
                self.widgets[name].grid(columnspan=total_columns, sticky="w")
        # Make widgets for interaction params
        self.interaction_label = tk.Label(self, text="Interaction Parameters")
        self.interaction_label.grid(columnspan=total_columns, sticky="w",
                                    pady=(header_space, 0), padx=left_space)
        name = PARAM["interaction"][0]
        self.widgets[name] = EWInteractionParamEditor(
            self, name, param_info[name], params[name])
        self.widgets[name].grid(columnspan=total_columns)
        self.headers = [self.main_label,
                        self.cell_label,
                        self.interaction_label]
        for each in self.headers:
            each.config(bg=self.cget("bg"), fg=HEADER_COLOR, font=HEADER_FONT)
        # Randomize and apply
        temp = tk.Frame(self)
        self.randomize_button = tk.Button(temp, text="Randomize",
                                          command=self._randomize,
                                          padx=BUTTON_X_MARGIN)
        self.apply_button = tk.Button(temp, text="Apply", command=self._apply,
                                      padx=BUTTON_X_MARGIN)
        self.randomize_button.grid(row=0, column=0, padx=(0, 20))
        self.apply_button.grid(row=0, column=1)
        temp.grid(columnspan=2, pady=(20, 4))

    def update_step(self):
        """Get current time step from the Simulation object and update the
        Tkinter StringVar for display."""
        step = self.sim.step
        self.steps_strvar.set("Step = {}".format(step))

    def update_params(self):
        """Get model parameters from the Simulation object and propagate values
        to each widget """
        params = self.sim.params
        for name, widget in self.widgets.items():
            widget.set_value(params[name])

    def unbind_(self):
        """Disocciate methods of this class from session data changes."""
        self.sim.unbind("params", self.update_params)
        self.sim.unbind("step", self.update_step)

    def _restart(self):
        self.steps_strvar.set("Step = 0")
        self.sim.restart()

    def _randomize(self):
        self.sim.randomize()

    def _retrieve_params(self):
        params = {}
        for name, widget in self.widgets.items():
            params[name] = widget.get_value()
        return params

    def _apply(self):
        new_params = self._retrieve_params()
        self.sim.insert_new_param(new_params)


class EditWindow(tk.Frame):
    """A window for the user to view large size simulation and global property
    plots and manually adjust the parameters of the simulation.

    Methods:
        update_graph: Update simulation graph.
        update_global_stats: Update global property plots.

    """
    def __init__(self, parent, master, session, sim):
        """
        Parameters:
            parent (tk.Frame): The logical parent of this object.
            master (tk.Toplevel): The Tkinter master of this window.
            session (SessionData): The object that stores application-level
                data, parameters and settings.
            sim (Simulation): The simulation associated with this window.

        """
        tk.Frame.__init__(self, master, height=693, width=844)
        self.grid_propagate(False)
        self.grid()
        self.master = master
        self.parent = parent
        self.session = session
        # Bind methods to data changes
        session.bind("vt", self.update_graph)
        session.bind("global_stats_display", self.update_global_stats)
        sim.bind("global_stats", self.update_global_stats, first=True)
        sim.bind("state", self.update_graph, first=True)
        self.sim = sim
        # Set window title
        master.wm_title("Edit Simulation")
        # Set actions when closing the window
        master.protocol('WM_DELETE_WINDOW', self._close)
        # Make edit panel
        self.edit_frame = EditFrame(self, session, sim)
        # Make simulation graph panel
        self.graph_widget = SimPlotWidget(self, large_size=True)
        self.update_graph()
        # Make global property plot panel
        property_label = tk.Label(self, text="Global Properties",
                                  fg=HEADER_COLOR, font=HEADER_FONT)
        self.property_widget = PropertyPlotWidget(self, large_size=True)
        self.update_global_stats()
        # Set layout
        self.edit_frame.grid(column=0, row=0, rowspan=3)
        self.graph_widget.grid(column=1, row=0, padx=(0, 8), pady=(8, 0))
        property_label.grid(column=1, row=1, sticky="w", padx=(5, 0), pady=0)
        self.property_widget.grid(column=1, row=2)

    def update_graph(self):
        """Update simulation graph."""
        self.graph_widget.plot_sim(self.session, self.sim)

    def update_global_stats(self):
        """Update global property plots."""
        self.property_widget.plot_global_stats(self.session, self.sim)

    def _close(self):
        self.session.unbind("vt", self.update_graph)
        self.session.unbind("global_stats_display", self.update_global_stats)
        self.sim.unbind("state", self.update_graph)
        self.sim.unbind("global_stats", self.update_global_stats)
        self.edit_frame.unbind_()
        self.master.destroy()
        self.parent.unfreeze()
