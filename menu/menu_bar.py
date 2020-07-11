import os
import tkFileDialog
import Tkinter as tk
from copy import deepcopy

from common.io_utils import load_from_files
from common.parameters import GLOBAL_STATS_NAMES
from menu.evolve_property import EvolvePropertyWindow
from menu.general import GeneralSettingsWindow
from menu.library import LibraryWindow
from menu.range import RangeSettingsWindow


class MenuBar(tk.Menu):
    def __init__(self, parent, session, master, menu_bar_commands):
        tk.Menu.__init__(self, master)
        self.parent = parent
        self.session = session
        session.bind("general_settings", self.update_general_options)
        session.bind("param_info", self.update_range_options)
        session.bind("global_stats_display", self.update_global_stats_options)
        options = [
            "Save Current Session",
            "Save All Genes to Library",
            "Save Global Properties",
            "Clear Library",
            ##########
            "Show Velocity Trace",
            "Every 1 Step",
            "Every 5 Step",
            "Every 10 Step",
            "Turn Off",
            "Zoom 0.5x",
            "Zoom 1.0x",
            "Zoom 2.0x",
            "Periodic Boundary",
            ##########
            "Interaction Force Only",
            "Alignment Force Only",
            "Enable Both Forces",
            "Allow Gradient",
            "Allow Pinned Cells",
            "Single Cell Type",
            "Two Cell Types",
            "Three Cell Types",
            "Restore Default Settings"
        ]
        options += ["Show "+each_name for each_name in GLOBAL_STATS_NAMES]
        options = [options[i/2] for i in range(len(options)*2-1,-1,-1)]
        menu = tk.Menu(self, tearoff=0)
        self.add_cascade(label="File", menu=menu)
        menu.add_command(label="Open Session...", command=self.open_session)
        menu.add_command(label="Open Gene from Library...", command=self.open_library)
        menu.add_command(label="Open Gene from Files...", command=self.open_from_files)
        menu.add_separator()
        for i in range(3):
            menu.add_command(label=options.pop(), command=menu_bar_commands[options.pop()])
        menu.add_separator()
        menu.add_command(label=options.pop(), command=menu_bar_commands[options.pop()])

        ##################GENERAL SETTINGS#######################
        ints = self.general_intvars = {name:tk.IntVar() for name in
            ["show_tail", "show_movement_value", "periodic_boundary", "zoom_in_value"]}

        menu = tk.Menu(self, tearoff=0)
        self.add_cascade(label="Control", menu=menu)
        menu.add_checkbutton(label=options.pop(), variable=ints["show_tail"], command=menu_bar_commands[options.pop()])

        menu.add_separator()

        # Show movement
        submenu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Show Movement", menu=submenu)
        steps=[1,5,10]
        for i in xrange(3):
            submenu.add_radiobutton(
                label=options.pop(),
                variable=ints["show_movement_value"],
                value=steps.pop(0),
                command=menu_bar_commands[options.pop()]
            )
        submenu.add_separator()
        # Turn off
        submenu.add_command(label=options.pop(), command=menu_bar_commands[options.pop()])
        menu.add_separator()
        # Zoom in
        sf=[5,10,20]
        for i in xrange(3,6):
            menu.add_radiobutton(
                label=options.pop(),
                variable=ints["zoom_in_value"],
                value=sf.pop(0),
                command=menu_bar_commands[options.pop()]
            )
        menu.add_separator()
        # Periodic boundary
        menu.add_checkbutton(label=options.pop(), variable=ints["periodic_boundary"], command=menu_bar_commands[options.pop()])
        menu.add_separator()
        menu.add_command(label="Advanced...", command=self.open_general_settings)

        ############### Range Settings ################
        ints = self.range_intvars = {name:tk.IntVar() for name in
            ["force", "gradient", "pinned", "ntype"]}

        menu = tk.Menu(self, tearoff=0)
        self.add_cascade(label="Parameters", menu=menu)
        # Force Only
        for i in [0,1,-1]:
            menu.add_radiobutton(label=options.pop(), variable=ints["force"], value=i+1, command=menu_bar_commands[options.pop()])
        menu.add_separator()
        # Gradient
        menu.add_checkbutton(label=options.pop(), variable=ints["gradient"], command=menu_bar_commands[options.pop()])
        menu.add_separator()
        # Pinned Cells
        menu.add_checkbutton(label=options.pop(), variable=ints["pinned"], command=menu_bar_commands[options.pop()])
        menu.add_separator()
        # Number of Cell Types
        for i in range(3):
            menu.add_radiobutton(label=options.pop(), variable=ints["ntype"], value=i+1, command=menu_bar_commands[options.pop()])
        menu.add_separator()
        # Default
        menu.add_command(label=options.pop(), command=menu_bar_commands[options.pop()])
        menu.add_separator()
        menu.add_command(label="Adjust Ranges...", command=self.open_range_settings)

        ############### Global Stats Display ################
        ints = self.global_stats_intvars = [tk.IntVar() for _ in range(6)]

        menu = tk.Menu(self, tearoff=0)
        self.add_cascade(label="Global Properties", menu=menu)
        for i in range(6):
            menu.add_checkbutton(label=options.pop(), variable=ints[i], command=menu_bar_commands[options.pop()])

        menu.add_separator()
        menu.add_command(label="Evolve by Property...", command=self.open_evolve_by_property)
        ############### Help & About ################
        menu = tk.Menu(self, tearoff=0)
        self.add_cascade(label="Help", menu=menu)
        menu.add_command(label="Help")
        menu.add_separator()
        menu.add_command(label="About")

        master.config(menu=self)

    def open_from_files(self):
        input_file_name = tkFileDialog.askopenfilename(
            filetypes=[("JSON", "json")]
            )
        if input_file_name != "":
            params = load_from_files(input_file_name)
            self.parent.insert_lib(params)

    def open_library(self):
        t = tk.Toplevel(self.parent)
        self.library_window = LibraryWindow(self.parent, t, self.parent.insert_lib)
        self.library_window.grid(padx=10, pady=5)

    def open_session(self):
        input_file_name = tkFileDialog.askopenfilename(
            filetypes=[("JSON", "json")],
            initialdir=os.path.join(os.path.dirname(os.path.dirname(__file__)),'sessions')
            )
        if input_file_name != "":
            self.parent.load_session(input_file_name)

    def open_general_settings(self):
        t = tk.Toplevel(self.parent)
        self.general_settings_window = GeneralSettingsWindow(t, deepcopy(self.session.general_settings), self.parent.update_general_settings)
        self.general_settings_window.grid(padx=(40,10), pady=(20,5))

    def update_general_options(self):
        new = self.session.general_settings
        for each in ["show_tail", "periodic_boundary"]:
            if self.general_intvars[each].get() != new[each]:
                self.general_intvars[each].set(new[each])

        if new["show_movement"]== 1:
            self.general_intvars["show_movement_value"].set(int(new["show_movement_value"]))
        else:
            self.general_intvars["show_movement_value"].set(0)

        # Zoom in Value
        temp = int(round(new["zoom_in_value"]*10))
        if new["zoom_in"] == 0:
            # deselect all except = 1.0
            self.general_intvars["zoom_in_value"].set(10)
        else:
            # If match
            self.general_intvars["zoom_in_value"].set(temp)

    def open_range_settings(self):
        t = tk.Toplevel(self.parent)
        self.range_settings_window = RangeSettingsWindow(t, self.session)
        self.range_settings_window.grid(padx=10,pady=5)

    def update_range_options(self):
        """
        ints = self.range_intvars = {name:tk.IntVar() for name in
            ["force", "gradient", "pinned", "ntype"]}
        """
        param_info = self.session.param_info
        force = 0
        if param_info["Interaction Force"]["range"][1] == 0:
            force += 2
        if param_info["Alignment Force"]["range"][1] == 0:
            force += 1
        self.range_intvars["force"].set(force)

        which = "Gradient Intensity"
        gradient_zero = all(param_info[which]["range"][i][1]==0 for i in xrange(3))
        self.range_intvars["gradient"].set(0 if gradient_zero else 1)

        which = "Pinned Cells"
        no_pinned = all((len(param_info[which]["range"][i])==1) and
            param_info[which]["range"][i][0]=="none" for i in xrange(3))
        self.range_intvars["pinned"].set(0 if no_pinned else 1)

        which = "Cell Ratio"
        ratio = param_info[which]["range"]
        if (ratio[0] == ratio[1]) and ((ratio[0]==0) or (ratio[0]==float("inf"))):
            both = 0
        else:
            both = 1
        if ratio[3]>0:
            if ratio[2]<1:
                ntype = 2 + both # at least 3rd type and another
            else:
                ntype = 1 # only 3rd type
        else:
            ntype = 1 + both # no 3rd type
        self.range_intvars["ntype"].set(ntype)
    def update_global_stats_options(self):
        """
        ints = self.global_stats_intvars = [tk.IntVar() for _ in range(6)]
        """
        new = self.session.global_stats_display["show"]
        for i in range(6):
            if self.global_stats_intvars[i].get() != new[i]:
                self.global_stats_intvars[i].set(new[i])
    def open_evolve_by_property(self):
        t = tk.Toplevel(self.parent)
        self.evolve_property_window = EvolvePropertyWindow(t, deepcopy(self.session.evolve_property_settings), self.parent.evolve_by_property)
        self.evolve_property_window.grid(padx=(40,10), pady=(20,5))
