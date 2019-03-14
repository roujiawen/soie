"""This module contains AdvancedMutateFrame and its UI subcomponents.
"""

import Tkinter as tk
import ttk

from common.parameters import PARAM
from common.styles import (ADVANCED_MUTATE_FRAME_COLOR, BODY_COLOR, BODY_FONT,
                           H2_COLOR, H2_FONT, HEADER_COLOR, HEADER_FONT)
from common.tools import fit_into, is_within


class AMCheckbutton(tk.Frame):
    """A UI group including a parameter name label and a checkbutton.

    Methods:
        set: Set the value (either 0 or 1) associated with the checkbutton.
        get: Get the value associated with the checkbutton.

    """
    def __init__(self, parent, text, command=None):
        """
        Parameters:
            parent (tk.Frame): The Tkinter parent of this widget.
            text (str): Text to be displayed next to the checkbutton.
            command (func): Function to be called when checkbutton is toggled.

        """
        # Same background color as the parent widget
        tk.Frame.__init__(self, parent, bg=parent.cget("bg"))
        self.parent = parent
        self.label = tk.Label(self, text=text)
        # Tkinter control variable associated with the checkbutton
        self.intvar = tk.IntVar()
        if command is None:
            # If command is not provided, defaults to the deselect method
            self.checkbutton = tk.Checkbutton(self, variable=self.intvar,
                                              command=self._deselect)
        else:
            self.checkbutton = tk.Checkbutton(self, variable=self.intvar,
                                              command=command)

        self.label.grid(row=0, column=0, sticky="w")
        self.checkbutton.grid(row=0, column=1, sticky="e")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        for each in [self.label, self.checkbutton]:
            each.config(bg=self.cget("bg"), fg=BODY_COLOR, font=BODY_FONT)

    def set(self, value):
        """Pass the function call to the Tkinter IntVar object.
        """
        self.intvar.set(value)

    def get(self):
        """Pass the function call to the Tkinter IntVar object.
        """
        return self.intvar.get()

    def _deselect(self):
        """Turn the checkbutton off and update the 'All' button when
            necessary."""
        if self.get() == 0:
            self.parent.check_all_button.set(0)
            self.parent.total_checks -= 1
        else:
            self.parent.total_checks += 1
            # If all buttons are checked, automatically turn 'All' button on
            if self.parent.total_checks == len(self.parent.checkbuttons):
                self.parent.check_all_button.set(1)


class AMEntry(tk.Frame):
    """A UI component containing an entry widget with validation.

    Methods:
        set: Set the value (float) associated with the entry box.
        get: Get the value from the entry box.

    Validation:
        Real-time validation: allows "", ".", or float
        On <Return> or <FocusOut>: If not float, revert; otherwise force input
            to be between [lower, upper] and rounded.

    """

    def __init__(self, parent):
        """
        Parameters:
            parent (tk.Frame): The Tkinter parent of this widget.

        """
        # Same background color as parent widget
        tk.Frame.__init__(self, parent, bg=parent.cget("bg"))
        self.value = 0.
        # Set number of decimal places and lower and upper bounds
        self.roundto = 2
        self.lower, self.upper = 0., 1.
        # Configure ttk.entry widget style
        widget_style = ttk.Style()
        widget_style.configure('TEntry', fg=BODY_COLOR, font=BODY_FONT)

        def is_okay(value):
            """Validate whether entered value is permissibleself."""
            if value in ["", "."]:
                # Allow empty string and single decimal point
                return True
            try:
                # True if value lies within range and reasonable length
                return (is_within(float(value), self.lower, self.upper)
                        and (len(value) < 5))
            except ValueError:
                # False if cannot convert value to float
                return False

        # Register validation function
        vcmd = (self.register(is_okay), '%P')
        # Create Entry widget
        self.entry = ttk.Entry(self, width=4, textvariable=self.value,
                               validate="all", validatecommand=vcmd)
        self.entry.grid()
        # Check and update value following these actions
        self.bind('<Return>', self._check_value)
        self.bind('<FocusOut>', self._check_value)

    def _check_value(self):
        """Make sure the newly entered value is a valid float, otherwise
        revert to the last stored value."""
        try:
            # If input is a valid float, update stored value
            value = float(self.entry.get())
            self.set(value)
        except ValueError:
            # Otherwise revert back
            self.set(self.value)

    def set(self, value):
        """Update stored value and refresh display."""
        self.value = round(fit_into(value, self.lower, self.upper),
                           self.roundto)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.value)

    def get(self):
        """Return stored value after checking that its validity."""
        self._check_value()
        return self.value


class AdvancedMutateFrame(tk.Frame):
    """A frame that contains an input form allowing the user to configure the
    advanced mutate settings."""
    def __init__(self, parent, session):
        tk.Frame.__init__(self, parent, width=260, height=700,
                          background=ADVANCED_MUTATE_FRAME_COLOR)
        self.session = session
        # Prevent resizing
        self.grid_propagate(False)
        # Count number of checkbuttons turned on
        self.total_checks = 0
        # Call .set() whenever ``advanced_mutate`` data changes
        session.bind("advanced_mutate", self.set)
        # Set layout
        v_space = 15
        h_space = 30
        left_space = 8
        self.columnconfigure(0, weight=1)
        # Make title of the frame
        title = tk.Label(self, text="Advanced Settings",
                         bg=self.cget("bg"),
                         fg=H2_COLOR, font=H2_FONT)
        title.grid(row=0, column=0, pady=5)
        # Make subframe containing mutation rate label and entry widgets
        temp = tk.Frame(self, bg=self.cget("bg"))
        rate_label = tk.Label(temp, text="Mutation rate:",
                              bg=self.cget("bg"),
                              fg=BODY_COLOR, font=BODY_FONT)
        rate_entry = AMEntry(temp)
        temp.grid(padx=left_space, pady=(v_space, 0), sticky="w")
        rate_label.grid(row=0, column=0, pady=0)
        rate_entry.grid(row=0, column=1, pady=0)
        # Make label for the checkbuttons group
        self.checkbuttons = {}
        main_label = tk.Label(self, text="Choose parameters to mutate:",
                              bg=self.cget("bg"), fg=HEADER_COLOR,
                              font=HEADER_FONT)
        main_label.grid(sticky="w", padx=left_space, pady=(v_space, 10))
        # Make check-all button
        self.check_all_button = AMCheckbutton(self, "All",
                                              command=self._check_all)
        self.check_all_button.grid(padx=h_space, sticky="we")
        ttk.Separator(self).grid(sticky="ew", pady=5, padx=h_space)
        # One checkbutton for each parameter name in order
        param_names = PARAM["main"]+PARAM["cell"]+PARAM["interaction"]
        for name in param_names:
            self.checkbuttons[name] = AMCheckbutton(self, name)
            self.checkbuttons[name].grid(padx=h_space, sticky="we")
        # Collect all widgets into a dictionary
        self.widgets = {key: self.checkbuttons[key] for key in param_names}
        self.widgets["rate"] = rate_entry

    def _check_all(self):
        """Define logic for check-all button"""
        if self.check_all_button.get() == 1:
            # If turned on, check all other buttons and update total count
            for each in self.checkbuttons.values():
                each.set(1)
            self.total_checks = len(self.checkbuttons)
        else:
            # If turned off, uncheck all other buttons and update total count
            for each in self.checkbuttons.values():
                each.set(0)
            self.total_checks = 0

    def set(self):
        """Retrieve settings from session data and propagate the values to all
        subcomponents"""
        settings = self.session.advanced_mutate
        self.total_checks = 0
        for name, value in settings.items():
            # Set the values of each widget
            self.widgets[name].set(value)
            # Update total count of checkbuttons that are turned on
            if (value == 1) and (name != "rate"):
                self.total_checks += 1
        # Check the ``All`` button if all other buttons are checked
        self.check_all_button.set(
            1 if self.total_checks == len(self.checkbuttons) else 0)

    def get(self):
        """Get current settings from the UI components and return a dictionary
        containing all their values."""
        settings = {}
        for name, each in self.widgets.items():
            settings[name] = each.get()
        return settings
