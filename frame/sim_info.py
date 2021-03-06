import Tkinter as tk
import ttk

from common.parameters import PARAM
from common.plotting import PropertyPlotWidget
from common.styles import (BODY_COLOR, BODY_FONT, CELL_TYPE_HEADER_COLOR,
                           CELL_TYPE_HEADER_FONT, CELL_TYPE_LABELS, H2_COLOR,
                           H2_FONT, HEADER_COLOR, HEADER_FONT,
                           SIM_INFO_FRAME_COLOR, SIM_INFO_HEADER_SPACE,
                           SIM_INFO_LEFT_SPACE)
from common.tools import is_within


class AddStepsWidget2(tk.Frame):
    def __init__(self, parent, strvar):
        tk.Frame.__init__(self, parent, bg=parent.cget("bg"))
        self.parent = parent
        self.func = None
        self.label = tk.Label(self, text="+", bg=self.cget("bg"), fg=BODY_COLOR, font=BODY_FONT)

        vcmd = (self.register(self.is_okay),'%P')
        self.value = strvar
        self.value.set('20')

        s = ttk.Style()
        s.configure('TEntry', fg=BODY_COLOR, font=BODY_FONT)
        self.entry = ttk.Entry(self, width=4,
            textvariable=self.value, validate="all",
            validatecommand=vcmd)

        self.entry.bind("<Command-a>", self.entry_select_all)

        s.configure('TButton', ipadx=0, padx=0, fg=BODY_COLOR, font=BODY_FONT)
        self.button = ttk.Button(self, text="Go!", width=3, command=self.go)

        self.widgets = [self.label, self.entry, self.button]

        for i, each in enumerate(self.widgets):
            each.grid(row=0, column=i)

        self.widgets = [self.label, self.entry, self.button]


    def is_okay(self, value):
        if value == "": return True
        if (len(value) > 4): return False
        try:
            if is_within(int(value), 0, 9999): return True
        except:
            pass
        return False

    def entry_select_all(self, event):
        self.entry.select_range(0, tk.END)

    def go(self):
        v = self.value.get()
        if v == "":
            return
        v = int(v)
        self.func(v)

class MainParamWidget(tk.Frame):
    def __init__(self, parent, text):
        tk.Frame.__init__(self, parent, bg=parent.cget("bg"))
        self.label = tk.Label(self, text=text+" :")
        #self.divider = tk.Label(self, text=":")
        self.strvar = tk.StringVar()
        self.strvar.set("0.01") #be deleted
        self.value = tk.Label(self, textvariable=self.strvar, width=8)

        self.label.grid(row=0, column=0, sticky="w")
        #self.divider.grid(row=0, column=1)
        self.value.grid(row=0, column=1, sticky="w")
        self.columnconfigure(0, minsize=150)

        for each in [self.label, self.value]:
            each.config(bg=parent.cget("bg"), fg=BODY_COLOR, font=BODY_FONT)

    def set(self, v):
        self.strvar.set(str(v))

class CellParamWidget(tk.Frame):
    def __init__(self, parent, text):
        tk.Frame.__init__(self, parent, bg=parent.cget("bg"))

        self.label = tk.Label(self, text=text, bg=parent.cget("bg"))
        self.label.grid(row=0, column=0, sticky="w", padx=(8,0))
        self.strvars = [tk.StringVar() for _ in range(3)]
        self.values = []
        for i, each in enumerate(self.strvars):
            each.set("0.001") #be deleted
            self.values.append(tk.Label(self, textvariable=each, bg=parent.cget("bg")))
            self.values[-1].grid(row=0, column=i+1, sticky="w")
        self.columnconfigure(0, minsize=109)
        self.columnconfigure(1, minsize=45)
        self.columnconfigure(2, minsize=45)
        self.columnconfigure(3, minsize=45)

        for each in [self.label]+self.values:
            each.config(bg=parent.cget("bg"), fg=BODY_COLOR, font=BODY_FONT)

    def set(self, v):
        for i, each in enumerate(v):
            self.strvars[i].set(str(each))

class InteractionParamWidget(tk.Frame):
    def __init__(self, parent, text):
        tk.Frame.__init__(self, parent, bg=parent.cget("bg"))

        #label
        self.label = tk.Label(self, text=text)
        self.label.grid(row=0, column=0, columnspan=4, sticky="w")

        #header
        self.header = [tk.Label(self, text=_) for _ in [""]+CELL_TYPE_LABELS]

        for i, each in enumerate(self.header):
            each.config(bg=parent.cget("bg"), font=CELL_TYPE_HEADER_FONT, fg=CELL_TYPE_HEADER_COLOR)
            each.grid(row=1, column=i, sticky="w")

        #body
        self.strvars = [[tk.StringVar() for _ in range(3)] for __ in range(3)]
        self.row_headers = [tk.Label(self, text=_, bg=parent.cget("bg"), font=CELL_TYPE_HEADER_FONT, fg=CELL_TYPE_HEADER_COLOR) for _ in CELL_TYPE_LABELS]
        self.values = [[tk.Label(self, textvariable=_) for _ in __]
            for __ in self.strvars]

        for i, each_row in enumerate(self.strvars):
            self.row_headers[i].grid(row=2+i, column=0, sticky="w")
            for j in range(3):
                self.values[i][j].grid(row=2+i, column=1+j, sticky="w")

        self.columnconfigure(0, minsize=50)
        self.columnconfigure(1, minsize=50)
        self.columnconfigure(2, minsize=50)
        self.columnconfigure(3, minsize=50)

        self.widgets = ([self.label]+
            self.values[0]+self.values[1]+self.values[2])

        for each in self.widgets:
            each.config(bg=parent.cget("bg"), fg=BODY_COLOR, font=BODY_FONT)

    def set(self, v):
        for i, each_row in enumerate(v):
            for j, each in enumerate(each_row):
                self.strvars[i][j].set(str(each))

class SimInfoFrame(tk.Frame):
    def __init__(self, parent, session, sim, strvar):
        tk.Frame.__init__(self, parent, background=SIM_INFO_FRAME_COLOR,
            highlightbackground="black", highlightcolor="black",
            highlightthickness=0, width=260, height=700)
        import numpy as np
        self.session = session
        self.sim = sim
        session.bind("global_stats_display", self.update_global_stats)
        sim.bind("params", self.update_params)
        sim.bind("global_stats", self.update_global_stats)
        sim.bind("step", self.update_step)

        self.default_steps_strvar = strvar
        self.grid_propagate(False)

        total_columns = 2
        #title
        self.title = tk.Label(self, text="Model Information", bg=self.cget("bg"), fg=H2_COLOR, font=H2_FONT)
        self.title.grid(row=0, column=0, columnspan=total_columns, pady=0)

        #steps
        self.steps_strvar = tk.StringVar()
        self.steps_strvar.set("Step = 0")
        self.steps_label = tk.Label(self, textvariable=self.steps_strvar, width=13,
            anchor="w", bg=self.cget("bg"), fg=BODY_COLOR, font=BODY_FONT)
        self.steps_widget = AddStepsWidget2(self, self.default_steps_strvar)
        self.steps_label.grid(row=1, column=0, ipady=5, padx=(20,0), sticky="w")
        self.steps_widget.grid(row=1, column=1, padx=(0,20), sticky="e")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        #property
        self.property_label = tk.Label(self, text="Global Properties")
        self.property_label.grid(columnspan=total_columns, sticky="w", padx=SIM_INFO_LEFT_SPACE,
            pady=(SIM_INFO_HEADER_SPACE,0))

        self.property_plot = PropertyPlotWidget(self, bg=self.cget("bg"))
        self.property_plot.grid(columnspan=total_columns)

        #main params
        self.params = {}
        self.main_label = tk.Label(self, text="Main Parameters")
        self.main_label.grid(columnspan=total_columns, sticky="w", padx=SIM_INFO_LEFT_SPACE,
            pady=(SIM_INFO_HEADER_SPACE,0))
        for name in PARAM["main"]:
            self.params[name] = MainParamWidget(self, name)
            self.params[name].grid(columnspan=total_columns, padx=0)

        #cell params
        self.cell_label = tk.Label(self, text="Cell Parameters")
        self.cell_label.grid(columnspan=total_columns, sticky="w",
            pady=(SIM_INFO_HEADER_SPACE,0), padx=SIM_INFO_LEFT_SPACE)
        self.cell_table_header = CellParamWidget(self, " ")
        self.cell_table_header.set(CELL_TYPE_LABELS)
        for each in self.cell_table_header.values:
            each.config(font=CELL_TYPE_HEADER_FONT, fg=CELL_TYPE_HEADER_COLOR)
        self.cell_table_header.grid(columnspan=total_columns)
        for name in PARAM["cell"]:
            self.params[name] = CellParamWidget(self, name)
            self.params[name].grid(columnspan=total_columns)

        #interaction params
        self.interaction_label = tk.Label(self, text="Interaction Parameters")
        self.interaction_label.grid(columnspan=total_columns, sticky="w",
            pady=(SIM_INFO_HEADER_SPACE,0), padx=SIM_INFO_LEFT_SPACE)
        name = PARAM["interaction"][0]
        self.params[name] = InteractionParamWidget(self, name)
        self.params[name].grid(columnspan=total_columns)
        self.params[name].set([[1,2,3],[4,5,6],[7,8,9]])


        self.headers = [self.property_label, self.main_label, self.cell_label,
            self.interaction_label]
        for each in self.headers:
            each.config(bg=self.cget("bg"),fg=HEADER_COLOR, font=HEADER_FONT)

        self.widgets = [self.steps_widget]

    def update_step(self):
        #update step
        step = self.sim.step
        self.steps_strvar.set("Step = {}".format(step))

    def update_global_stats(self):
        #update global_stats
        self.property_plot.plot_global_stats(self.session, self.sim)

    def update_params(self):
        new_params = self.sim.params
        #update params
        for name, value in new_params.items():
            self.params[name].set(value)
