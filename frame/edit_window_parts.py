"""This module contains the UI subcomponents inside the edit window.
"""

import Tkinter as tk
from copy import copy

from common.styles import (CELL_COLORS, CELL_TYPE_LABELS, EDIT_BODY_COLOR,
                           EDIT_BODY_FONT, EDIT_COLOR_FONT)
from common.tools import fit_into

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
