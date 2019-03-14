"""This module contains the EditWindow and the EditFrame classes.
"""

import Tkinter as tk
from copy import copy

from common.parameters import PARAM
from common.plotting import PropertyPlotWidget, SimPlotWidget
from common.styles import (BODY_COLOR, BODY_FONT, BUTTON_X_MARGIN,
                           HEADER_COLOR, HEADER_FONT)

from frame.edit_window_parts import (EWRatioEditor, EWQualitativeEditor,
                                     EWMainParamEditor, EWCellParamEditor,
                                     EWInteractionParamEditor)
from frame.top import AddStepsWidget


class EditFrame(tk.Frame):
    """A edit panel for the user to manually adjust the parameters of a
    simulation.

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
