from Tkinter import *
import ttk
import os
from copy import copy, deepcopy
from common.styles import *
from common.tools import is_within
from common.io_utils import delete_all_genes
from frame.top import ButtonsFrame, MutateFrame, CrossFrame, InsertLibFrame
from frame.siminfo import SimInfoFrame
from frame.advancedmutate import AdvancedMutateFrame
from frame.simulations import SimsFrame
from menu.menubar import MenuBar
from model.genetic import Population, GenoGenerator
from common.parameters import PARAM_INFO

RECORD_PATH = os.path.join(os.path.dirname(__file__), "customdata/record.py")

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

    set(attr, *args)
    value
    subattr, which, value

    bind(attr, *args)
    func
    which, func
    """
    def __init__(self):
        self.param_info = {}
        self.general_settings = {}
        self.bindings = {"general_settings":[], "param_info":[], "vt":[],
        "advanced_mutate":[]}
        self.advanced_mutate = {}

    def unbind(self, attr, func):
        self.bindings[attr].remove(func)

    def bind_first(self, attr, func):
        self.bindings[attr].insert(0,func)

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

        #self.write()

    def write(self):
        #TODO: fix writing record
        # combined = {"models":self.models,
        # "general_settings":self.general_settings,
        # "param_info":self.param_info,
        # "advanced_mutate":self.advanced_mutate}
        with open(RECORD_PATH, "w") as f:
           f.write("inf=float('inf')\nRECORD_DATA="+str(combined))

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


class App(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master, background=APP_COLOR, width=978, height=727)
        self.master = master
        self.title = "Self-Organization Interactive Evolution"
        master.title(self.title)
        self.grid_propagate(0)
        self.grid()

        session = SessionData()
        self.session = session

        flag=False
        # Read record data
        if os.path.exists(RECORD_PATH):
            from customdata.record import RECORD_DATA
            for each in ["param_info","general_settings", "advanced_mutate"]:
                setattr(session, each, RECORD_DATA[each])
            flag=True
        else:
            from common.parameters import GENERAL_SETTINGS, ADVANCED_MUTATE
            session.param_info = deepcopy(PARAM_INFO)
            session.general_settings = deepcopy(GENERAL_SETTINGS)
            session.advanced_mutate = ADVANCED_MUTATE

        #Population
        self.population = Population(session)
        sims = self.population.simulations

        #RIGHT
        self.advanced_mutate_frame = AdvancedMutateFrame(self, session)
        self.info_default_steps_strvar = StringVar()
        self.sim_info_frames = [SimInfoFrame(self, session, sims[_], self.info_default_steps_strvar) for _ in range(9)]
        self.right_frames = self.sim_info_frames + [self.advanced_mutate_frame]

        #BOTTOMLEFT
        self.sims_frame = SimsFrame(self, session, sims, self.sim_info_frames, self.get_top_frame)

        # Linking add_steps function
        for sim, gframe in zip(self.population.simulations, self.sims_frame.graphs):
            gframe.info_frame.steps_widget.func = sim.add_steps

        #TOP
        self.buttons_frame = ButtonsFrame(self, session, new_pop_command=self.new_pop,
                             mutate_command=self.mutate,
                             cross_command=self.cross,
                             add_command=self.population.add_steps_all)

        self.mutate_frame = MutateFrame(self, session,
            mutate_func=self.population.mutate, advanced_frame=self.advanced_mutate_frame)
        self.cross_frame = CrossFrame(self, cross_func=self.population.crossover)
        self.insert_lib_frame = InsertLibFrame(self, insert_func=self.population.insert_from_lib)
        self.top_frames = [self.mutate_frame, self.cross_frame, self.insert_lib_frame]
        self.current_top_frame = self.buttons_frame

        #TODO: fix loading prev session
        # try:
        #     if flag==True:
        #         for subattr, model_info in RECORD_DATA["models"].items():
        #             for sim, i in zip(sims, range(9)):
        #                 session.set("models", subattr, sim, model_info[i])
        #         self.population.load_prev_session()
        # except:
        #     print "ERROR when restoring previous session"

        # menu bar
        def set_general(which, value):
            def func():
                new_settings = self.session.general_settings
                new_settings[which] = value
                self.update_general_settings(new_settings)
            return func
        def set_double(which, affect, value):
            def func():
                new_settings = self.session.general_settings
                new_settings[which] = value
                new_settings[affect] = 1
                self.update_general_settings(new_settings)
            return func

        def toggle_general(which):
            def func():
                new_settings = self.session.general_settings
                new_settings[which] = 1 - new_settings[which]
                self.update_general_settings(new_settings)
            return func

        def set_ratio(range_):
            which = "Cell Ratio"
            def func():
                param_info = self.session.param_info
                param_info[which]["range"] = range_
                self.update_range_settings(param_info)
            return func

        def toggle_forces(nonzeros, zeros):
            def func():
                param_info = self.session.param_info
                for each in zeros:
                    param_info[each]["range"] = [0, 0]
                for each in nonzeros:
                    if param_info[each]["range"][1] == 0:
                        param_info[each]["range"] = copy(PARAM_INFO[each]["range"])
                self.update_range_settings(param_info)
            return func

        def toggle_range():
            which = "Gradient Intensity"
            param_info = self.session.param_info
            #if isinstance(param_info[which]["range"][0], list):
            if all(param_info[which]["range"][i][1]==0 for i in xrange(3)):
                param_info[which]["range"] = [[0.0, 2.0],[0.0, 2.0],[0.0, 2.0]]
            else:
                param_info[which]["range"] = [[0, 0],[0, 0],[0, 0]]

            self.update_range_settings(param_info)

        def toggle_pinned_cells():
            which = "Pinned Cells"
            param_info = self.session.param_info
            if all((len(param_info[which]["range"][i])==1) and
                param_info[which]["range"][i][0]=="none" for i in xrange(3)):
                param_info[which]["range"] = [["none", "random", "square", "circle", "ring"] for _ in xrange(3)]
            else:
                param_info[which]["range"] = [["none"],["none"],["none"]]
            self.update_range_settings(param_info)

        menu_bar_commands = {
        "Save All to Library": self.sims_frame.save_all,
        "Clear Library": delete_all_genes,
        ##############
        "Show Velocity Trace": toggle_general("show_tail"),
        "Every 1 Step":set_double("show_movement_value", "show_movement", 1),
        "Every 5 Step":set_double("show_movement_value", "show_movement", 5),
        "Every 10 Step":set_double("show_movement_value", "show_movement", 10),
        "Turn Off":set_general("show_movement", 0),
        "Zoom 0.5x":set_double("zoom_in_value", "zoom_in", 0.5),
        "Zoom 1.0x":set_double("zoom_in_value", "zoom_in", 1.0),
        "Zoom 2.0x":set_double("zoom_in_value", "zoom_in", 2.0),
        "Periodic Boundary":toggle_general("periodic_boundary"),
        ##############
        "Interaction Force Only":toggle_forces(["Interaction Force"], ["Alignment Force"]),
        "Alignment Force Only":toggle_forces(["Alignment Force"], ["Interaction Force"]),
        "Enable Both Forces":toggle_forces(["Alignment Force", "Interaction Force"], []),
        "Allow Gradient":toggle_range,
        "Allow Pinned Cells":toggle_pinned_cells,
        "Single Cell Type":set_ratio([float('inf'), float('inf'), 0., 0.]),
        "Two Cell Types":set_ratio([0., float('inf'), 0., 0.]),
        "Three Cell Types":set_ratio([0., float('inf'), 0., 1.]),
        "Restore Default Settings":self.default_range_settings
        }
        self.menu_bar = MenuBar(self, session, master, menu_bar_commands)

        for each in ["param_info","general_settings", "advanced_mutate"]:
            session.update(each)

        for each in self.top_frames:
            each.grid(row=0, column=0, sticky="we")
            each.grid_remove()
        for each in self.right_frames:
            each.grid(row=0, column=1, rowspan=2, padx=10)
            each.grid_remove()
        self.sims_frame.grid(row=1, column=0)
        self.buttons_frame.grid(row=0, column=0)
        self.rowconfigure(0, minsize=28)

    def get_top_frame(self):
        return self.current_top_frame

    def new_pop(self):
        self.population.new_population()

    def change_top_frame(self, new):
        new.grid_()
        if self.current_top_frame != new:
            self.current_top_frame.grid_remove()
            self.current_top_frame = new

        self.update_idletasks()

    def change_title(self, new_title=None):
        if new_title is None:
            self.master.title(self.title)
        else:
            self.master.title(new_title)

    def cancel_choose_mode(self):
        self.sims_frame.to_view_mode()
        self.change_top_frame(self.buttons_frame)
        self.change_title()

    def click_choose_mode(self, frame):
        self.change_top_frame(frame)

    def mutate(self):
        self.change_title("Mutate")
        self.sims_frame.to_choose_mode(multiple=False)
        self.click_choose_mode(self.mutate_frame)

    def cross(self):
        self.change_title("Crossover")
        self.sims_frame.to_choose_mode(multiple=True)
        self.click_choose_mode(self.cross_frame)

    def insert_lib(self, params):
        self.insert_lib_frame.chosen_gene = params
        self.change_title("Insert from Library")
        self.sims_frame.to_choose_mode(multiple=True)
        self.click_choose_mode(self.insert_lib_frame)

    def default_range_settings(self):
        self.update_range_settings(PARAM_INFO)

    def update_general_settings(self, new_settings):
        self.session.set("general_settings", new_settings)

    def update_range_settings(self, param_info):
        self.session.set("param_info", param_info)

    def expand_range_settings(self, chosen_gene):
        exceed_range = [False]
        def recursive_fit(item, range_):
            if isinstance(item, list):
                return [recursive_fit(i, r) for i, r in zip(item, range_)]
            else:
                assert isinstance(range_, list) and (len(range_)==2) and (not isinstance(range_[0], list))
                if is_within(item, *range_):
                    return range_
                else:
                    exceed_range[0] = True
                    return [min(range_[0], item), max(range_[1], item)]
        param_info = deepcopy(self.session.param_info)
        for name in param_info:
            if name == "Pinned Cells":
                for i in range(3):
                    if chosen_gene[name][i] not in param_info[name]["range"][i]:
                        exceed_range[0] = True
                        param_info[name]["range"][i].append(chosen_gene[name][i])
            elif name =="Cell Ratio":
                blue, red, green = chosen_gene[name]
                if red == 0:
                    blue_red_ratio = float("inf")
                else:
                    blue_red_ratio = blue/float(red)
                param_info[name]["range"][:2] = recursive_fit(blue_red_ratio, param_info[name]["range"][:2])
                param_info[name]["range"][2:] = recursive_fit(green, param_info[name]["range"][2:])
            else:
                param_info[name]["range"] = recursive_fit(chosen_gene[name], param_info[name]["range"])
        self.update_range_settings(param_info)

root = Tk()
app = App(root)
root.mainloop()
