from common.styles import *
from common.tools import *
from common.parameters import *
from common.plotting import PlotWidget
from frame.top import AddStepsWidget
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from copy import copy

class SingleEntry(Entry):
    """
    For Interaction Parameter
    Validation:
        Real-time: Can enter "", ".", or float
        <Return> or <FocusOut>: If not float(empty), reverse; otherwise
            force input to be between ["from", "to"] and rounded
    """
    def __init__(self, parent, info, value):
        Entry.__init__(self, parent, width=6)
        if info["range"][1] != float("inf"):
            self.maxlen = [len(str(int(info["range"][1]))), info["roundto"]]
        else:
            self.maxlen = [float("inf"), info["roundto"]]
        self.round = lambda x: round(x, info["roundto"])
        vcmd = (self.register(self.is_okay),'%P')
        self.config(validate="all", validatecommand=vcmd)

        self.value = None
        if "range" in info:
            self.fit_into = lambda x: fit_into(x, *info["range"])
        else:
            self.fit_into = lambda x: fit_into(x, 0., float("inf"))
        self.bind('<Return>',self.check_value)
        self.bind('<FocusOut>',self.check_value)
        self.set_value(value)

    def update_range(self, from_, to):
        self.fit_into = lambda x: fit_into(x, from_, to)

    def is_okay(self, value):
        if value in ["", "."]: return True
        try:
            float(value)
            splitted = value.split(".")
            if any(len(splitted[i])>self.maxlen[i] for i in range(len(splitted))):
                return False
            return True
        except:
            return False

    def check_value(self, event=None):
        try:
            v = float(self.get())
            self.set_value(v)
        except:
            self.set_value(self.value)

    def set_value(self,v):
        self.value = self.round(self.fit_into(v))
        self.delete(0,END)
        self.insert(0,self.value)

    def get_value(self):
        self.check_value()
        return self.value

class RatioEditor(Frame):
    """
    Validation:
        Real-time: allows "" or "." or float

    set_value : list

    """
    def __init__(self, parent, name, info, values):
        Frame.__init__(self, parent)
        if info["range"][1] != float("inf"):
            self.maxlen = [len(str(int(info["range"][1]))), info["roundto"]]
        else:
            self.maxlen = [float("inf"), info["roundto"]]
        self.round = lambda x : round(x, info["roundto"])
        self.limits = info["range"]
        self.values = [0]*3
        self.pair_widgets = []

        """self.headers = [Label(self, text=_, font=EDIT_BODY_FONT, fg=EDIT_BODY_COLOR)
            for _ in [" ", "Blue"," ", "Red"," ", "Green"]]
        for i, each in enumerate(self.headers):
            each.grid(row=0, column=i)"""

        self.label = Label(self, text=name, font=EDIT_BODY_FONT, fg=EDIT_BODY_COLOR, width=18)
        self.label.grid(row=0, column=0)

        vcmd = (self.register(self.is_okay),'%P')
        for i in range(5):
            if i % 2 == 0:
                w = Entry(self, width=6, validate="all", validatecommand=vcmd, font=EDIT_BODY_FONT, fg=CELL_COLORS[i/2])
                w.grid(row=0, column=i+1)
                w.bind('<Return>', self.update_entries)
                w.bind('<FocusOut>', self.if_editing)
                self.pair_widgets.append(w)
            else:
                colon = Label(self,text=":", font=EDIT_BODY_FONT, fg=EDIT_BODY_COLOR)
                colon.grid(row=0, column=i+1)

        for i, size in enumerate([60,2,60,2,60]):
            self.columnconfigure(i+1, minsize=size)

        self.set_value(values)

    def is_okay(self, value):
        if value in ["", "."]: return True
        try:
            float(value)
            splitted = value.split(".")
            if any(len(splitted[i])>self.maxlen[i] for i in range(len(splitted))):
                return False
            return True
        except:
            return False

    def update_range(self, limits):
        self.limits = limits

    @property
    def widget_values(self):
        try:
            return [float(_.get()) for _ in self.pair_widgets]
        except:
            return False

    def reverse(self):
        self.set_value(self.values)

    def first_step_check(self):
        wvalues = self.widget_values
        if not wvalues:
            self.reverse()
            return "skip"

    def if_editing(self, event):
        if self.focus_get() not in self.pair_widgets:
            self.update_entries()
        else:
            self.first_step_check()

    def update_entries(self,event=None):
        if self.first_step_check() == "skip":
            return
        wvalues = self.widget_values
        s = float(sum(wvalues))
        if s == 0:
            self.reverse()
            return
        # Normalize
        wvalues = [_/s for _ in wvalues]
        # Fit green ratio into limits
        green_min, green_max = self.limits[2], self.limits[3]
        wvalues[2] = self.round(fit_into(wvalues[2], green_min, green_max))

        if wvalues[1] == 0:
            ratio = self.limits[1]
        else:
            ratio = fit_into(wvalues[0]/wvalues[1], self.limits[0], self.limits[1])
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
        for i in range(3):
            self.values[i] = self.round(values[i])
            self.pair_widgets[i].delete(0,END)
            self.pair_widgets[i].insert(0,self.values[i])

    def get_value(self):
        self.update_entries()
        return self.values

class QualitativeEditor(Frame):
    """
    set_value : list
    """
    def __init__(self, parent, name, info, values):
        Frame.__init__(self, parent)
        choices = info["range"]
        self.name = name
        self.label = Label(self,text=name, font=EDIT_BODY_FONT, fg=EDIT_BODY_COLOR, width=18)
        self.label.grid(row=0, column=0)

        self.choice = [StringVar() for _ in range(3)]
        self.choices = choices
        self.menu = [OptionMenu(self, _, *__) for _, __ in zip(self.choice, choices)]

        for i, each in enumerate(self.menu):
            each.config(width=7, font=EDIT_BODY_FONT)
            each.grid(row=0, column=i+1, padx=0)

        # self.columnconfigure(1, minsize=47)
        # self.columnconfigure(2, minsize=47)
        # self.columnconfigure(3, minsize=47)
        self.set_value(values)


    def set_value(self, v):
        for each, val in zip(self.choice,v):
            each.set(val)

    def update_range(self, choices):
        self.menu["menu"].delete(0, 'end')
        for choice in choices:
            self.menu["menu"].add_command(label=choice, command=lambda v=choice: self.choice.set(v))

    def get_value(self):
        return [_.get() for _ in self.choice]

class MainParamEditor(Frame):
    """
    set_value(v) : float
    """
    def __init__(self, parent, text, info, value, length=150, width=20, font=None):
        Frame.__init__(self, parent)
        self.info = info
        if info["range"][1] != float("inf"):
            self.maxlen = [len(str(int(info["range"][1]))), info["roundto"]]
        else:
            self.maxlen = [float("inf"), info["roundto"]]
        self.round = lambda x: round(x, info["roundto"])
        resolution = info["resolution"]
        from_, to = info["range"]
        self.fit_into = lambda x: fit_into(x, from_, to)
        self.scale = Scale(self, from_=from_, to=to,
            resolution = resolution, orient=HORIZONTAL,
            sliderlength=15,
            width=15,
            length=length,
            command=self.update_entry,
            showvalue=0)
        self.scale.grid(row=0, column=2,padx=5)

        self.label = Label(self,text=text, width=width)
        self.label.grid(row=0, column=0)

        vcmd = (self.register(self.is_okay),'%P')
        self.entry = Entry(self,width=6, validate="all", validatecommand=vcmd)
        self.entry.grid(row=0, column=1)
        self.entry.bind('<Return>',self.update_scale)
        self.entry.bind('<FocusOut>',self.update_scale)

        self.widgets = [self.label, self.entry]
        for each in self.widgets: each.config(fg=EDIT_BODY_COLOR, font=EDIT_BODY_FONT)
        if font is not None:
            self.label.config(font=font)

        self.set_value(value)

    def is_okay(self, value):
        if value in ["", "."]: return True
        try:
            float(value)
            splitted = value.split(".")
            if any(len(splitted[i])>self.maxlen[i] for i in range(len(splitted))):
                return False
            return True
        except:
            return False

    def update_range(self, from_, to):
        self.fit_into = lambda x: fit_into(x, from_, to)
        self.scale["from_"] = from_
        self.scale["to"] = to

    def update_entry(self,event=None):
        f = float(self.scale.get())
        self.set_value(f)

    def update_scale(self,event=None):
        try:
            f = float(self.entry.get())
            self.set_value(f)
        except:
            self.update_entry()

    def set_value(self,v):
        self.value = self.round(self.fit_into(v))
        self.entry.delete(0,END)
        self.entry.insert(0,self.value)
        self.scale.set(self.value)

    def get_value(self):
        self.update_scale()
        return self.value

class CellParamEditor(Frame):
    """
    set_value(vals) : list
    """
    def __init__(self, parent, text, info, values):
        Frame.__init__(self, parent)
        self.cwidgets = [] #widgets for each color
        self.label = Label(self, text=text, fg=EDIT_BODY_COLOR, font=EDIT_BODY_FONT, width=18)
        self.label.grid(column=0, row=0, padx=0)
        info_copy = copy(info)
        for i, name in enumerate(CELL_TYPE_LABELS):
            info_copy["range"] = info["range"][i]
            w = MainParamEditor(self, name, info_copy, values[i], length=100, width=9, font=EDIT_COLOR_FONT)
            w.grid(column=1, row=i, padx=0)
            self.cwidgets.append(w)

    def set_value(self, vals):
        for each, v in zip(self.cwidgets, vals):
            each.set_value(v)

    def get_value(self):
        return [_.get_value() for _ in self.cwidgets]

class InteractionParamEditor(Frame):
    def __init__(self, parent, text, info, values):
        Frame.__init__(self, parent)
        self.info = info

        #label
        self.label = Label(self, text=text)
        self.label.grid(row=0, column=0, columnspan=4, sticky="w")

        #header
        cell_types = CELL_TYPE_LABELS
        self.header = [Label(self, text=_, fg=EDIT_BODY_COLOR, font=EDIT_COLOR_FONT) for _ in [""]+cell_types]
        for i, each in enumerate(self.header): each.grid(row=1, column=i, sticky="w")

        #body
        self.row_headers = [Label(self, text=_, fg=EDIT_BODY_COLOR, font=EDIT_COLOR_FONT) for _ in cell_types]
        self.entries = [[],[],[]]
        info_copy = copy(info)
        for i in range(3):
            for j in range(3-i):
                info_copy["range"] = info["range"][i][j]
                self.entries[i].append(SingleEntry(self, info_copy, values[i][i+j]))

        for i in range(3):
            self.row_headers[i].grid(row=2+i, column=0, sticky="w")
            for j in range(3-i):
                self.entries[i][j].grid(row=2+i, column=1+i+j, sticky="w")

        self.columnconfigure(0, minsize=50)
        self.columnconfigure(1, minsize=50)
        self.columnconfigure(2, minsize=50)
        self.columnconfigure(3, minsize=50)

        temp = [self.label]+self.entries[0]+self.entries[1]+self.entries[2]
        for each in temp:
            each.config(bg=parent.cget("bg"), fg=EDIT_BODY_COLOR, font=EDIT_BODY_FONT)

    def set_value(self, v):
        for i in range(3):
            for j in range(3-i):
                self.entries[i][j].set_value(v[i][i+j])

    def get_value(self):
        values = [[0]*3 for _ in range(3)]
        for i in range(3):
            for j in range(3-i):
                values[i][i+j] = values[i+j][i] = self.entries[i][j].get_value()

        return values

class EditFrame(Frame):
    def __init__(self, parent, session, sim):
        Frame.__init__(self, parent)
        self.sim = sim
        self.session = session
        session.priority_bind("params", sim, self.update_params)
        session.priority_bind("step", sim, self.update_step)
        params = copy(session.models["params"][sim])
        param_info = session.param_info
        total_columns = 2
        header_space = 7
        left_space = 8

        #Add Steps
        self.steps_strvar = StringVar()
        self.update_step()
        temp = Frame(self)
        self.steps_label = Label(temp, textvariable=self.steps_strvar,
            anchor="w", bg=self.cget("bg"), fg=BODY_COLOR, font=BODY_FONT)
        self.restart_button = Button(temp, text=u"\u21ba", command=self.restart, padx=5)
        self.steps_label.grid(row=0, column=0, sticky="e")
        self.restart_button.grid(row=0, column=1, sticky="w")
        temp.grid(row=0, column=0, ipady=3, padx=(10,0), sticky="w")

        self.steps_widget = AddStepsWidget(self, sim.add_steps, text="+", )
        self.steps_widget.grid(row=0, column=1, padx=(0,10), sticky="e")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        #main params
        self.pwidgets = {}
        self.main_label = Label(self, text="Main Parameters")
        self.main_label.grid(columnspan=total_columns, sticky="w", padx=left_space,
            pady=(header_space,0))

        for name in PARAM["main"]:
            #if name == "Angular Inertia":
            self.pwidgets[name] = MainParamEditor(self, name, param_info[name], params[name])
            self.pwidgets[name].grid(columnspan=total_columns, padx=0)

        #cell params
        self.cell_label = Label(self, text="Cell Parameters")
        self.cell_label.grid(columnspan=total_columns, sticky="w",
            pady=(header_space,0), padx=left_space)

        for name in PARAM["cell"]:
            info = param_info[name]
            if "type" not in info:
                self.pwidgets[name] = CellParamEditor(self, name, info, params[name])
                self.pwidgets[name].grid(columnspan=total_columns, sticky="w")
            elif info["type"] == "ratio":
                self.pwidgets[name] = RatioEditor(self, name, info, params[name])
                self.pwidgets[name].grid(columnspan=total_columns, sticky="w")
            elif info["type"] == "qualitative":
                self.pwidgets[name] = QualitativeEditor(self, name, info, params[name])
                self.pwidgets[name].grid(columnspan=total_columns, sticky="w")

        #interaction params
        self.interaction_label = Label(self, text="Interaction Parameters")
        self.interaction_label.grid(columnspan=total_columns, sticky="w",
            pady=(header_space,0), padx=left_space)
        name = PARAM["interaction"][0]
        self.pwidgets[name] = InteractionParamEditor(self, name, param_info[name], params[name])
        self.pwidgets[name].grid(columnspan=total_columns)


        self.headers = [self.main_label, self.cell_label, self.interaction_label]
        for each in self.headers:
            each.config(bg=self.cget("bg"),fg=HEADER_COLOR, font=HEADER_FONT)

        # Randomize and apply
        temp = Frame(self)
        self.randomize_button = Button(temp, text="Randomize", command=self.randomize, padx=BUTTON_X_MARGIN)
        self.apply_button = Button(temp, text="Apply", command=self.apply, padx=BUTTON_X_MARGIN)
        self.randomize_button.grid(row=0,column=0, padx=(0,20))
        self.apply_button.grid(row=0, column=1)
        temp.grid(columnspan=2, pady=(20,4))

    def update_step(self):
        step = self.session.models["step"][self.sim]
        self.steps_strvar.set("Step = {}".format(step))

    def update_params(self):
        params = self.session.models["params"][self.sim]
        for name, w in self.pwidgets.items():
            w.set_value(params[name])

    def restart(self):
        self.steps_strvar.set("Step = 0")
        self.sim.restart()

    def randomize(self):
        self.sim.randomize()

    def retrieve_params(self):
        params = {}
        for name, widget in self.pwidgets.items():
            params[name] = widget.get_value()
        return params

    def apply(self):
        new_params = self.retrieve_params()
        self.sim.insert_new_param(new_params)
    def unbind(self):
        self.session.unbind("params", self.sim, self.update_params)
        self.session.unbind("step", self.sim, self.update_step)

class EditWindow(Frame):
    def __init__(self, parent, master, session, sim, graph_figsize=(5,5), property_figsize=(5,1.6), dpi=100):
        Frame.__init__(self, master, height=693, width=844)
        self.grid_propagate(0)
        self.grid()
        self.master = master
        self.parent = parent
        self.session = session
        session.bind("vt", self.update_graph)
        session.priority_bind("properties", sim, self.update_properties)
        session.priority_bind("state", sim, self.update_graph)
        self.sim = sim
        master.wm_title("Edit Simulation")
        master.protocol('WM_DELETE_WINDOW', self.close)

        #edit
        self.edit_frame = EditFrame(self, session, sim)

        #graph
        self.graph_widget = PlotWidget(self, figsize=graph_figsize, dpi=dpi, no_edge=True, axis="off", xlim=[0, AXIS_LIMIT], ylim=[0, AXIS_LIMIT])
        self.dots = (graph_figsize[0]*dpi)**2
        self.update_graph()

        #property
        self.property_label = Label(self, text="Global Properties", fg=HEADER_COLOR, font=HEADER_FONT)

        self.property_widget = PlotWidget(self, figsize=property_figsize, dpi=dpi)
        self.property_widget.large_plot()
        self.update_properties()
        self.property_widget.large_legend()


        self.edit_frame.grid(column=0, row=0, rowspan=3)
        self.graph_widget.grid(column=1, row=0, padx=(0,8), pady=(8,0))
        self.property_label.grid(column=1, row=1, sticky="w", padx=(5,0), pady=0)
        self.property_widget.grid(column=1, row=2)



    def update_graph(self):
        self.graph_widget.plot_sim(self.session, self.sim, self.dots)

    def update_properties(self):
        self.property_widget.plot_properties(self.session, self.sim)

    def close(self):
        self.session.unbind("vt", self.update_graph)
        self.session.unbind("state", self.sim, self.update_graph)
        self.session.unbind("properties", self.sim, self.update_properties)
        self.edit_frame.unbind()
        self.master.destroy()
        self.parent.unfreeze()


if __name__ == "__main__":
    root = Tk()
    from model.genetic import *
    from common.parameters import PARAM_INFO
    geno = GenoGenerator(PARAM_INFO)
    pheno = PhenoGenerator()
    simulation = Simulation(geno, pheno)
    simulation.randomize()
    class Nothing(object):
        def __getattr__(self, key):
            def do_nothing(*args):
                pass
            if key in ["inc_dpi"]:
                return do_nothing
    frame = EditWindow(None, root, Nothing(), Nothing(), simulation)
    root.mainloop()
