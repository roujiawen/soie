from common.styles import *
from common.tools import *
from common.parameters import *

class MainParamCheckbutton(Frame):
    def __init__(self, parent, text, command=None):
        Frame.__init__(self, parent, bg=parent.cget("bg"))
        self.parent = parent
        self.label = Label(self, text=text)
        self.intvar = IntVar()
        self.intvar.set(1) #be deleted
        if command is None:
            self.checkbutton = Checkbutton(self, variable=self.intvar,
            command=self.deselect)
        else:
            self.checkbutton = Checkbutton(self, variable=self.intvar,
            command=command)

        self.label.grid(row=0, column=0, sticky="w")
        self.checkbutton.grid(row=0, column=1, sticky="e")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        for each in [self.label, self.checkbutton]:
            each.config(bg=self.cget("bg"),fg=BODY_COLOR, font=BODY_FONT)

    def set(self, v):
        self.intvar.set(v)

    def get(self):
        return self.intvar.get()

    def deselect(self):
        if self.get() == 0:
            self.parent.check_all_button.set(0)
            self.parent.total_checks -= 1
        else:
            self.parent.total_checks += 1
            if self.parent.total_checks == len(self.parent.checkbuttons):
                self.parent.check_all_button.set(1)


class SingleEntry(Frame):
    """
    Validation:
        Real-time: Can enter "", ".", or float
        <Return> or <FocusOut>: If not float(empty), reverse; otherwise
            force input to be between ["from", "to"] and rounded
    """
    def __init__(self, parent, value=None):
        Frame.__init__(self, parent, bg=parent.cget("bg"))
        self.value = value
        self.roundto = 2
        self.from_, self.to = 0., 1.

        s = ttk.Style()
        s.configure('TEntry', fg=BODY_COLOR, font=BODY_FONT)
        vcmd = (self.register(self.is_okay),'%P')

        self.entry = ttk.Entry(self, width=4,
            textvariable=self.value, validate="all",
            validatecommand=vcmd)
        self.entry.grid()

        self.bind('<Return>',self.check_value)
        self.bind('<FocusOut>',self.check_value)

    def is_okay(self, value):
        if value in ["", "."]: return True
        try:
            if (is_within(float(value), self.from_, self.to)) and (len(value)<5):
                return True
            else:
                return False
        except:
            return False

    def check_value(self, event=None):
        try:
            v = float(self.entry.get())
            self.set(v)
        except:
            self.set(self.value)

    def set(self,v):
        self.value = round(fit_into(v, self.from_, self.to),self.roundto)
        self.entry.delete(0,END)
        self.entry.insert(0,self.value)

    def get(self):
        self.check_value()
        return self.value

class AdvancedMutateFrame(Frame):
    def __init__(self, parent, session):
        Frame.__init__(self, parent, width=260, height=700, background=ADVANCED_MUTATE_FRAME_COLOR)
        self.grid_propagate(0)
        self.total_checks = 0
        self.session = session
        session.bind("advanced_mutate", self.set)
        header_space = 30
        left_space = 8
        self.columnconfigure(0, weight=1)
        #title
        self.title = Label(self, text="Advanced Settings", bg=self.cget("bg"), fg=H2_COLOR, font=H2_FONT)
        self.title.grid(row=0, column=0, pady=5)

        # Mutation Rate
        temp = Frame(self, bg=self.cget("bg"))
        self.rate_label = Label(temp, text="Mutation rate:", bg=self.cget("bg"), fg=BODY_COLOR, font=BODY_FONT)
        self.rate_entry = SingleEntry(temp)
        temp.grid(padx=left_space, pady=(header_space/2,0), sticky="w")
        self.rate_label.grid(row=0,column=0, pady=0)
        self.rate_entry.grid(row=0,column=1, pady=0)

        #checkbuttons
        self.checkbuttons = {}
        self.main_label = Label(self, text="Choose parameters to mutate:",
            bg=self.cget("bg"), fg=HEADER_COLOR, font=HEADER_FONT)
        self.main_label.grid(sticky="w", padx=left_space,
            pady=(header_space/2, 10))
        self.check_all_button = MainParamCheckbutton(self, "All", command=self.check_all)
        self.check_all_button.grid(padx=30, sticky="we")

        ttk.Separator(self).grid(sticky="ew", pady=5, padx=30)

        param_names = PARAM["main"]+PARAM["cell"]+PARAM["interaction"]
        for name in param_names:
            self.checkbuttons[name] = MainParamCheckbutton(self, name)
            self.checkbuttons[name].grid(padx=30, sticky="we")

        self.widgets = {key:self.checkbuttons[key] for key in param_names}
        self.widgets["rate"] = self.rate_entry

    def set_rate(self, val):
        self.rate_entry.delete(0,END)
        self.rate_entry.insert(0,val)

    def check_all(self):
        if self.check_all_button.get() == 1:
            for each in self.checkbuttons.values():
                each.set(1)
            self.total_checks = len(self.checkbuttons)
        else:
            for each in self.checkbuttons.values():
                each.set(0)
            self.total_checks = 0

    def set(self):
        info = self.session.advanced_mutate
        self.total_checks = 0
        for name, val in info.items():
            self.widgets[name].set(val)
            if (val == 1) and (name != "rate"):
                self.total_checks += 1

        # Check check_all_button if all buttons are checked
        self.check_all_button.set(1 if self.total_checks == len(self.checkbuttons) else 0)

    def get(self):
        info = {}
        for name, each in self.widgets.items():
            info[name] = each.get()
        return info
