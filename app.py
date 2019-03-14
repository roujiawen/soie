"""This module contains the core parts of the GUI.

``App`` is the top-level application window frame.
``SessionData`` is a data management and binding system.

"""

import datetime
import os
import tkFileDialog
import Tkinter as tk
import tkMessageBox
from argparse import Namespace
from copy import copy, deepcopy

from common.io_utils import (delete_all_genes, load_session_data,
                             save_session_data)
from common.parameters import (ADVANCED_MUTATE, EVOLVE_PROPERTY_SETTINGS,
                               GENERAL_SETTINGS, GLOBAL_STATS_DISPLAY,
                               GLOBAL_STATS_NAMES, PARAM_INFO)
from common.styles import APP_COLOR
from common.tools import is_within
from frame.advanced_mutate import AdvancedMutateFrame
from frame.sim_info import SimInfoFrame
from frame.simulations import SimsFrame
from frame.top import (ButtonsFrame, CrossFrame, EvolvingFrame, InsertLibFrame,
                       MutateFrame)
from menu.menu_bar import MenuBar
from model.genetic import Population


class SessionData(object):
    """

    GENERAL_SETTINGS = {
        "show_tail" : 0,
        "show_tail_value" : [5.0, 0.3],
        "show_movement" : 0,
        "show_movement_value" : 5,
        "zoom_in" : 1, #0
        "zoom_in_value" : 5.0, #2.0
        "periodic_boundary" : 0
    }

    GLOBAL_STATS_DISPLAY = [1, 1, 1, 1, 1, 1]

    set(attr, *args)
    value
    subattr, which, value

    bind(attr, *args)
    func
    which, func
    """
    def __init__(self):
        self.data_names = ["general_settings", "param_info", "advanced_mutate",
                           "global_stats_display", "evolve_property_settings"]
        self.param_info = deepcopy(PARAM_INFO)
        self.general_settings = deepcopy(GENERAL_SETTINGS)
        self.global_stats_display = deepcopy(GLOBAL_STATS_DISPLAY)
        self.evolve_property_settings = deepcopy(EVOLVE_PROPERTY_SETTINGS)
        self.advanced_mutate = deepcopy(ADVANCED_MUTATE)
        self.bindings = {"general_settings": [], "param_info": [], "vt": [],
                         "advanced_mutate": [], "global_stats_display": [],
                         "evolve_property_settings": []}

    def unbind(self, attr, func):
        self.bindings[attr].remove(func)

    def bind(self, attr, func):
        self.bindings[attr].append(func)

    def update(self, attr):
        for each in self.bindings[attr]:
            each()

    def set(self, attr, *args):
        if len(args) == 0:
            self.update(attr)
            return

        if len(args) == 1:
            setattr(self, attr, args[0])
            self.update(attr)

    @property
    def movement(self):
        return False if self.general_settings["show_movement"] == 0\
            else self.general_settings["show_movement_value"]

    @property
    def vt(self):
        if self.general_settings["show_tail"] == 0:
            return [0, 0]
        else:
            return self.general_settings["show_tail_value"]

    @property
    def sf(self):
        if self.general_settings["zoom_in"] == 0:
            return 1.0
        else:
            return self.general_settings["zoom_in_value"]

    @property
    def pb(self):
        if self.general_settings["periodic_boundary"] == 1:
            return True
        else:
            return False

    @property
    def pheno_settings(self):
        return self.sf, self.pb, self.vt


class App(tk.Frame):
    """A Tkinter frame that contains all UI components inside the main
    application window. It is the first things that users see when they
    run the application.


    """
    def __init__(self, master):
        tk.Frame.__init__(self, master, background=APP_COLOR,
                          width=978, height=727)
        self.master = master
        self.title = "Self-Organization Interactive Evolution"
        master.title(self.title)
        # Prevents frame size change
        self.grid_propagate(False)
        self.grid()
        # Initiate SessionData object
        self.session = session = SessionData()
        # Initiate Population object
        self.population = Population(session)
        # Make GUI parts
        self._init_frames()
        self._init_menu_bar()
        self._set_layout()
        # Generate first population
        self.new_pop()
        # Update session data
        for each in session.data_names:
            session.update(each)

    def _init_frames(self):
        session = self.session
        sims = self.population.simulations

        self.frames = Namespace()
        # Make frames located on the RIGHT
        advanced_mutate_frame = AdvancedMutateFrame(self, session)
        info_default_steps_strvar = tk.StringVar()
        sim_info_frames = [
            SimInfoFrame(self, session, sims[_],
                         info_default_steps_strvar) for _ in range(9)]
        self.frames.right = sim_info_frames + [advanced_mutate_frame]

        # Make frames located on the LEFT
        self.frames.sims = SimsFrame(
            self, session, sims, sim_info_frames, self.get_top_frame)

        # Linking add_steps function from interface to model
        for sim, graph in zip(
                self.population.simulations, self.frames.sims.graphs):
            graph.info_frame.steps_widget.func = sim.add_steps

        # Make frames located on the TOP
        self.frames.buttons = ButtonsFrame(
            self, session, new_pop_command=self.new_pop,
            mutate_command=self.mutate, cross_command=self.cross,
            add_command=self.population.add_steps_all)

        self.frames.mutate = MutateFrame(
            self, session, mutate_func=self.population.mutate,
            advanced_frame=advanced_mutate_frame)
        self.frames.cross = CrossFrame(
            self, cross_func=self.population.crossover)
        self.frames.insert_lib = InsertLibFrame(
            self, insert_func=self.population.insert_from_lib)
        self.frames.evolving = EvolvingFrame(self)
        self.frames.top = [self.frames.mutate, self.frames.cross,
                           self.frames.insert_lib, self.frames.evolving]
        self.current_top_frame = self.frames.buttons

    def _init_menu_bar(self):
        session = self.session

        def save_current_session():
            """Save session data including general_settings, param_info,
            advanced_mutate and model_data.

            Format of model_data:
            [
                {"params": sim1.params,
                 "state": sim1.state,
                 "global_stats": sim1.global_stats,
                 "step": sim1.step},

                {"params": sim2.params,
                 "state": sim2.state,
                 "global_stats": sim2.global_stats,
                 "step": sim2.step},

                ...... x 9
            ]

            """
            # Open dialog and ask the user to input filename to save as
            output_file_name = tkFileDialog.asksaveasfilename(
                filetypes=[("JSON", "json")],
                initialdir=os.path.join(os.path.dirname(__file__), 'sessions'),
                initialfile=datetime.datetime.now()
                .strftime("Session_%m-%d-%Y_at_%I.%M%p")  # Default name
            )
            # If filename not empty (or when dialog is cancelled)
            if output_file_name != "":
                # Collect various settings from SessionData
                session_data = {name: getattr(session, name)
                                for name in session.data_names}
                # Collect data related to currently running simulations
                model_data = [
                    {
                        "params": each_sim.params,
                        "state": [_.tolist() for _ in each_sim.state],
                        "global_stats": each_sim.global_stats.tolist(),
                        "step": each_sim.step
                    }
                    for each_sim in self.population.simulations
                ]
                session_data["model_data"] = model_data
                # Export
                save_session_data(output_file_name, session_data)
                # Show success message
                tkMessageBox.showinfo("", "Current session has been saved!")

        """The following is a set of functions that link the shortcut buttons
        on the menu bar to the update of ``general_settings``.
        """
        def _set_general(which, value):
            def _func():
                new_settings = self.session.general_settings
                new_settings[which] = value
                self.update_general_settings(new_settings)
            return _func

        def _set_double(which, affect, value):
            def _func():
                new_settings = self.session.general_settings
                new_settings[which] = value
                new_settings[affect] = 1
                self.update_general_settings(new_settings)
            return _func

        def _toggle_general(which):
            def _func():
                new_settings = self.session.general_settings
                new_settings[which] = 1 - new_settings[which]
                self.update_general_settings(new_settings)
            return _func

        def _set_ratio(range_):
            which = "Cell Ratio"

            def _func():
                param_info = self.session.param_info
                param_info[which]["range"] = range_
                self.update_range_settings(param_info)
            return _func

        def _toggle_forces(nonzeros, zeros):
            def _func():
                param_info = self.session.param_info
                for each in zeros:
                    param_info[each]["range"] = [0, 0]
                for each in nonzeros:
                    if param_info[each]["range"][1] == 0:
                        param_info[each]["range"] = copy(
                            PARAM_INFO[each]["range"])
                self.update_range_settings(param_info)
            return _func

        def _toggle_range():
            which = "Gradient Intensity"
            param_info = self.session.param_info
            # if isinstance(param_info[which]["range"][0], list):
            if all(param_info[which]["range"][i][1] == 0 for i in range(3)):
                param_info[which]["range"] = [[0., 2.], [0., 2.], [0., 2.]]
            else:
                param_info[which]["range"] = [[0., 0.], [0., 0.], [0., 0.]]

            self.update_range_settings(param_info)

        def _toggle_pinned_cells():
            which = "Pinned Cells"
            param_info = self.session.param_info
            if all((len(param_info[which]["range"][i]) == 1) and
                    (param_info[which]["range"][i][0] == "none")
                    for i in range(3)):
                param_info[which]["range"] = [
                    ["none", "random", "square", "circle", "ring"]
                    for _ in range(3)]
            else:
                param_info[which]["range"] = ["none"] * 3
            self.update_range_settings(param_info)

        def _toggle_global_stats(which):
            def _func():
                new_settings = self.session.global_stats_display
                new_settings["show"][which] = 1 - new_settings["show"][which]
                self.session.set("global_stats_display", new_settings)
            return _func

        # Specify the actions associated with each menubar button, and pass
        # into the construction MenuBar frame.
        menu_bar_commands = {
            # Under "File" menu
            "Save Current Session": save_current_session,
            "Save All Genes to Library": self.frames.sims.save_all,
            "Clear Library": delete_all_genes,
            # Under "Control" menu
            "Show Velocity Trace": _toggle_general("show_tail"),
            "Every 1 Step": _set_double("show_movement_value",
                                        "show_movement", 1),
            "Every 5 Step": _set_double("show_movement_value",
                                        "show_movement", 5),
            "Every 10 Step": _set_double("show_movement_value",
                                         "show_movement", 10),
            "Turn Off": _set_general("show_movement", 0),
            "Zoom 0.5x": _set_double("zoom_in_value", "zoom_in", 0.5),
            "Zoom 1.0x": _set_double("zoom_in_value", "zoom_in", 1.0),
            "Zoom 2.0x": _set_double("zoom_in_value", "zoom_in", 2.0),
            "Periodic Boundary": _toggle_general("periodic_boundary"),
            # Under "Parameters" menu
            "Interaction Force Only": _toggle_forces(["Interaction Force"],
                                                     ["Alignment Force"]),
            "Alignment Force Only": _toggle_forces(["Alignment Force"],
                                                   ["Interaction Force"]),
            "Enable Both Forces": _toggle_forces(["Alignment Force",
                                                  "Interaction Force"], []),
            "Allow Gradient": _toggle_range,
            "Allow Pinned Cells": _toggle_pinned_cells,
            "Single Cell Type": _set_ratio([float('inf'), float('inf'),
                                            0., 0.]),
            "Two Cell Types": _set_ratio([0., float('inf'), 0., 0.]),
            "Three Cell Types": _set_ratio([0., float('inf'), 0., 1.]),
            "Restore Default Settings": self.default_range_settings
        }
        # Under "Global Properties" menu
        for i, each_name in enumerate(GLOBAL_STATS_NAMES):
            menu_bar_commands["Show "+each_name] = _toggle_global_stats(i)
        # Make menu bar frame
        MenuBar(self, session, self.master, menu_bar_commands)

    def _set_layout(self):
        """Set the positions of frames and hide certain frames that are not
        used at the start."""
        for each in self.frames.top:
            each.grid(row=0, column=0, sticky="we")
            each.grid_remove()
        for each in self.frames.right:
            each.grid(row=0, column=1, rowspan=2, padx=10)
            each.grid_remove()
        self.frames.sims.grid(row=1, column=0)
        self.frames.buttons.grid(row=0, column=0)
        self.rowconfigure(0, minsize=28)

    def _change_top_frame(self, new):
        new.grid_()
        if self.current_top_frame != new:
            self.current_top_frame.grid_remove()
            self.current_top_frame = new
        self.update_idletasks()

    def _change_title(self, new_title=None):
        if new_title is None:
            self.master.title(self.title)
        else:
            self.master.title(new_title)

    def get_top_frame(self):
        """Answer the question: which one of the top frames are currently
        shown?"""
        return self.current_top_frame

    def back_to_home_topframe(self):
        """Show ButtonsFrame and hide all other top frames."""
        self.frames.sims.to_view_mode()
        self._change_top_frame(self.frames.buttons)
        self._change_title()

    def new_pop(self):
        """Define actions to be taken when 'New Population' button is
        clicked."""
        self.population.new_population()

    def mutate(self):
        """Define actions to be taken when 'Mutate' button is clicked."""
        self._change_title("Mutate")
        self.frames.sims.to_choose_mode(multiple=False)
        self._change_top_frame(self.frames.mutate)

    def cross(self):
        """Define actions to be taken when 'Crossover' button is clicked."""
        self._change_title("Crossover")
        self.frames.sims.to_choose_mode(multiple=True)
        self._change_top_frame(self.frames.cross)

    def evolve_by_property(self, new_settings):
        """Define actions to be taken when evolve command is called, i.e.,
        Menu Bar >> Global Properties >> Evolve by Property... >> Evolve! """
        # Disable show_movement
        general_settings = self.session.general_settings
        general_settings["show_movement"] = 0
        self.update_general_settings(general_settings)
        # Change title, top frame and sim frame mode
        self._change_title("Evolving...")
        self.frames.sims.to_evolving_mode()
        self._change_top_frame(self.frames.evolving)
        # Push new settings to SessionData
        self.session.set("evolve_property_settings", new_settings)
        # Evolve!
        which_prop = new_settings["which_prop"]
        num_gen = new_settings["num_gen"]
        equi_range = new_settings["equi_range"]
        self.population.evolve_by_property(which_prop, num_gen, equi_range,
                                           self.frames.evolving.display_text,
                                           self.frames.sims.highlight)
        # When done, show 'Back' button
        self._change_title("Done!")
        self.frames.evolving.done()

    def insert_lib(self, params):
        """Define actions to be taken when open-gene-from-library commmand
        is called, i.e., Menu Bar >> File >> Open Gene from Library...
        >> Open."""
        self.frames.insert_lib.chosen_gene = params
        self._change_title("Insert from Library")
        self.frames.sims.to_choose_mode(multiple=True)
        self._change_top_frame(self.frames.insert_lib)

    def default_range_settings(self):
        """Define actions to be taken when the user calls Menu Bar >>
        Parameters >> Restore Default Settings."""
        self.update_range_settings(PARAM_INFO)

    def update_general_settings(self, new_settings):
        """Push updates in general_settings to SessionData."""
        self.session.set("general_settings", new_settings)

    def update_range_settings(self, param_info):
        """Push updates in range_settings to SessionData."""
        self.session.set("param_info", param_info)

    def expand_range_settings(self, gene):
        """Expand range_settings to accomodate genes inserted from the library
        that exceed current range settings."""
        exceed_range = [False]

        def _recursive_fit(item, range_):
            if isinstance(item, list):
                return [_recursive_fit(i, r) for i, r in zip(item, range_)]

            assert (isinstance(range_, list) and (len(range_) == 2)
                    and (not isinstance(range_[0], list)))
            if is_within(item, *range_):
                return range_

            exceed_range[0] = True
            return [min(range_[0], item), max(range_[1], item)]

        param_info = deepcopy(self.session.param_info)
        for name in param_info:
            if name == "Pinned Cells":
                for i in range(3):
                    if gene[name][i] not in param_info[name]["range"][i]:
                        exceed_range[0] = True
                        param_info[name]["range"][i].append(gene[name][i])
            elif name == "Cell Ratio":
                blue, red, green = gene[name]
                if red == 0:
                    blue_red_ratio = float("inf")
                else:
                    blue_red_ratio = blue/float(red)
                param_info[name]["range"][:2] = _recursive_fit(
                    blue_red_ratio, param_info[name]["range"][:2])
                param_info[name]["range"][2:] = _recursive_fit(
                    green, param_info[name]["range"][2:])
            else:
                param_info[name]["range"] = _recursive_fit(
                    gene[name], param_info[name]["range"])
        self.update_range_settings(param_info)

    def load_session(self, input_file_name):
        """Define actions to be taken when load-session command is called,
        i.g., Menu Bar >> File >> Open Session... >> Open.
        """
        session_data = load_session_data(input_file_name)
        for each in self.session.data_names:
            setattr(self.session, each, session_data[each])
        self.population.load_prev_session(session_data["model_data"])
        for each in self.session.data_names:
            self.session.update(each)

# Launch a Tkinter application
root = tk.Tk()
app = App(root)
root.mainloop()
