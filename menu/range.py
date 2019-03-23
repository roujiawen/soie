import Tkinter as tk
from copy import copy, deepcopy

from common.parameters import PARAM
from common.styles import (BODY_COLOR, BODY_FONT, CELL_TYPE_HEADER_COLOR,
                           CELL_TYPE_HEADER_FONT, CELL_TYPE_LABELS,
                           HEADER_COLOR, HEADER_FONT)

BODY_LEFT_MARGIN = 30
LABEL_WIDTH = 160


class QualitativeRangeEditor(tk.Frame):
    def __init__(self, parent, name, info):
        tk.Frame.__init__(self, parent)
        self.name = name
        self.info = info
        self.all_choices = info["all_choices"]
        self.label = tk.Label(self, text=name, font=BODY_FONT, fg=BODY_COLOR)
        self.label.grid(row=0, column=0, padx=(BODY_LEFT_MARGIN, 0), sticky="w")

        self.checks = [[],[],[]]
        self.variables = [[tk.IntVar() for _ in self.all_choices] for __ in range(3)]

        for i in range(3):
            for j, text in enumerate(self.all_choices):
                self.checks[i].append(tk.Checkbutton(self, text=text, font=BODY_FONT, fg=BODY_COLOR, variable=self.variables[i][j]))
                if text in info["range"][i]:
                    self.checks[i][j].select()
                self.checks[i][j].grid(row=j, column=i+1, sticky="w", padx=(50,3))
        self.columnconfigure(0, minsize=LABEL_WIDTH)
        self.columnconfigure(1, minsize=170)
        self.columnconfigure(2, minsize=170)
        self.columnconfigure(3, minsize=170)

    def set(self, new_range):
        for i in range(3):
            for j, each in enumerate(self.checks[i]):
                if self.all_choices[j] in new_range[i]:
                    each.select()
                else:
                    each.deselect()
    def get(self):
        new_range = [[],[],[]]
        for i in range(3):
            for val, name in zip(self.variables[i], self.all_choices):
                if val.get() == 1:
                    new_range[i].append(name)
        return new_range

class RatioRangeEditor(tk.Frame):
    def __init__(self, parent, info, roundto=2):
        tk.Frame.__init__(self, parent)
        self.roundto = roundto
        self.maxlen=[float("inf"), roundto]
        values = info["range"]
        self.values1 = values[:2]
        self.values2 = values[2:]
        vcmd = (self.register(self.is_okay),'%P')

        self.label1 = tk.Label(self,text="Blue-Red Cell Ratio", font=BODY_FONT, fg=BODY_COLOR)
        self.label1.grid(row=0, column=0, padx=(BODY_LEFT_MARGIN, 0), sticky="w")
        self.columnconfigure(0, minsize=LABEL_WIDTH)

        self.min_label1 = tk.Label(self, text="min:", font=BODY_FONT, fg=BODY_COLOR, width=10)
        self.min_label1.grid(row=0, column=1)

        self.min_entry1 = tk.Entry(self, width=6, validate="all", validatecommand=vcmd, font=BODY_FONT, fg=BODY_COLOR)
        self.min_entry1.grid(row=0, column=2)
        self.min_entry1.bind('<Return>',self.min_update_entries1)
        self.min_entry1.bind('<FocusOut>',self.min_if_editing1)

        self.max_label1 = tk.Label(self, text="max:", font=BODY_FONT, fg=BODY_COLOR, width=10)
        self.max_label1.grid(row=0, column=3)

        self.max_entry1 = tk.Entry(self, width=6, validate="all", validatecommand=vcmd, font=BODY_FONT, fg=BODY_COLOR)
        self.max_entry1.grid(row=0, column=4)
        self.max_entry1.bind('<Return>',self.max_update_entries1)
        self.max_entry1.bind('<FocusOut>',self.max_if_editing1)

        self.label2 = tk.Label(self,text="Green-Total Cell Ratio", font=BODY_FONT, fg=BODY_COLOR)
        self.label2.grid(row=1, column=0, padx=(BODY_LEFT_MARGIN, 0), sticky="w")

        self.min_label2 = tk.Label(self, text="min:", font=BODY_FONT, fg=BODY_COLOR, width=10)
        self.min_label2.grid(row=1, column=1)

        self.min_entry2 = tk.Entry(self, width=6, validate="all", validatecommand=vcmd, font=BODY_FONT, fg=BODY_COLOR)
        self.min_entry2.grid(row=1, column=2)
        self.min_entry2.bind('<Return>',self.min_update_entries2)
        self.min_entry2.bind('<FocusOut>',self.min_if_editing2)

        self.max_label2 = tk.Label(self, text="max:", font=BODY_FONT, fg=BODY_COLOR, width=10)
        self.max_label2.grid(row=1, column=3)

        self.max_entry2 = tk.Entry(self, width=6, validate="all", validatecommand=vcmd, font=BODY_FONT, fg=BODY_COLOR)
        self.max_entry2.grid(row=1, column=4)
        self.max_entry2.bind('<Return>',self.max_update_entries2)
        self.max_entry2.bind('<FocusOut>',self.max_if_editing2)

        self.set_values1(self.values1)
        self.set_values2(self.values2)


    def is_okay(self, value):
        if value in ["", ".", "i", "in"]: return True
        try:
            float(value)
            splitted = value.split(".")
            if any(len(splitted[i])>self.maxlen[i] for i in range(len(splitted))):
                return False
            return True
        except:
            return False

    def min_if_editing1(self, event):
        if self.focus_get() != self.max_entry1:
            self.min_update_entries1()
            return

        temp = self.min_entry1.get()
        try:
            temp = float(temp)
            if temp < 0:
                self.set_values1([0, self.values1[1]])
        except:
            self.set_values1(self.values1)

    def min_update_entries1(self, event=None):
        min_ = self.min_entry1.get()
        max_ = float(self.max_entry1.get())

        try:
            min_ = float(min_)
            if min_ < 0:
                min_ = 0
        except:
            self.set_values1(self.values1)
            return

        if min_ > max_:
            self.set_values1((min_, min_))
        else:
            self.set_values1((min_, max_))

    def max_if_editing1(self, event):
        if self.focus_get() != self.min_entry1:
            self.max_update_entries1()
            return

        temp = self.max_entry1.get()
        try:
            temp = float(temp)
            if temp < 0:
                self.set_values1([self.values1[0], 0])
        except:
            self.set_values1(self.values1)

    def max_update_entries1(self, event=None):
        min_ = float(self.min_entry1.get())
        max_ = self.max_entry1.get()

        try:
            max_ = float(max_)
            if max_ < 0:
                max_ = 0
        except:
            self.set_values1(self.values1)
            return

        if min_ > max_:
            self.set_values1((max_, max_))
        else:
            self.set_values1((min_, max_))

    def set_values1(self, v):
        min_, max_ = v[0], v[1]
        self.values1[0] = min_
        self.values1[1] = max_
        self.min_entry1.delete(0,tk.END)
        self.min_entry1.insert(0, str(round(min_,self.roundto)))
        self.max_entry1.delete(0,tk.END)
        self.max_entry1.insert(0, str(round(max_,self.roundto)))

    def min_if_editing2(self, event):
        if self.focus_get() != self.max_entry2:
            self.min_update_entries2()
            return

        temp = self.min_entry2.get()
        try:
            temp = float(temp)
            if temp < 0:
                self.set_values2([0, self.values2[1]])
            elif temp > 1:
                self.set_values2([1, self.values2[1]])
        except:
                self.set_values2(self.values2)

    def min_update_entries2(self, event=None):
        min_ = self.min_entry2.get()
        max_ = float(self.max_entry2.get())

        try:
            min_ = min(max(0, float(min_)), 1)
        except:
            self.set_values2(self.values2)
            return

        if min_ > max_:
            self.set_values2((min_, min_))
        else:
            self.set_values2((min_, max_))

    def max_if_editing2(self, event):
        if self.focus_get() != self.min_entry2:
            self.max_update_entries2()
            return

        temp = self.max_entry2.get()
        try:
            temp = float(temp)
            if temp < 0:
                self.set_values2([self.values2[0], 0])
            elif temp > 1:
                self.set_values2([self.values2[0], 1])
        except:
            self.set_values2(self.values2)

    def max_update_entries2(self, event=None):
        min_ = float(self.min_entry2.get())
        max_ = self.max_entry2.get()

        try:
            max_ = min(max(0, float(max_)), 1)
        except:
            self.set_values2(self.values2)
            return

        if min_ > max_:
            self.set_values2((max_, max_))
        else:
            self.set_values2((min_, max_))

    def set_values2(self, v):
        min_, max_ = v[0], v[1]
        self.values2[0] = min_
        self.values2[1] = max_
        self.min_entry2.delete(0,tk.END)
        self.min_entry2.insert(0,round(min_,self.roundto))
        self.max_entry2.delete(0,tk.END)
        self.max_entry2.insert(0,round(max_,self.roundto))

    def last_update(self):
        self.min_update_entries1()
        self.max_update_entries1()
        self.min_update_entries2()
        self.max_update_entries2()

    def set(self, new_range):
        self.set_values1(new_range[:2])
        self.set_values2(new_range[2:])

    def get(self):
        self.last_update()
        return self.values1+self.values2

class RangeEditor(tk.Frame):
    def __init__(self, parent, name, info, narrow=False):
        tk.Frame.__init__(self, parent)
        self.name = name
        self.roundto = info["roundto"]
        self.values = info["range"]
        self.maxlen = [float('inf'), self.roundto]

        if "max" in info:
            self.upper_bound = info['max']
            self.maxlen[0] = len(str(int(info['max'])))
        else:
            self.upper_bound = float('inf')

        if "min" in info:
            self.lower_bound = info["min"]
        else:
            self.lower_bound = 0.0

        if name is not None:
            self.label = tk.Label(self,text=name, font=BODY_FONT, fg=BODY_COLOR)
            self.label.grid(row=0, column=0, padx=(BODY_LEFT_MARGIN, 0), sticky="w")
            self.columnconfigure(0, minsize=LABEL_WIDTH)
            starting_col = 1
        else:
            starting_col = 0

        vcmd = (self.register(self.is_okay),'%P')

        self.min_label = tk.Label(self, text="min:", font=BODY_FONT, fg=BODY_COLOR, width=10)
        self.min_entry = tk.Entry(self, width=6, validate="all", validatecommand=vcmd, font=BODY_FONT, fg=BODY_COLOR)
        self.max_label = tk.Label(self, text="max:", font=BODY_FONT, fg=BODY_COLOR, width=10)
        self.max_entry = tk.Entry(self, width=6, validate="all", validatecommand=vcmd, font=BODY_FONT, fg=BODY_COLOR)
        if narrow:
            for each in [self.min_label, self.min_entry, self.max_label, self.max_entry]:
                each.config(width=5)

        self.min_label.grid(row=0, column=starting_col)

        self.min_entry.grid(row=0, column=starting_col+1)
        self.min_entry.bind('<Return>',self.min_update_entries)
        self.min_entry.bind('<FocusOut>',self.min_if_editing)

        self.max_label.grid(row=0, column=starting_col+2)

        self.max_entry.grid(row=0, column=starting_col+3)
        self.max_entry.bind('<Return>',self.max_update_entries)
        self.max_entry.bind('<FocusOut>',self.max_if_editing)

        self.set_values(self.values)

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

    def min_if_editing(self, event):
        if self.focus_get() != self.max_entry:
            self.min_update_entries()
            return

        try:
            temp = float(self.min_entry.get())
            temp = min(max(self.lower_bound, temp), self.upper_bound)
            self.set_values([temp, self.values[1]])
        except:
            self.set_values(self.values)

    def min_update_entries(self, event=None):
        temp = self.min_entry.get()
        try:
            temp = float(temp)
        except:
            self.set_values(self.values)
            return

        max_ = float(self.max_entry.get())
        temp = min(max(self.lower_bound, temp), self.upper_bound)
        if max_ < temp:
            self.set_values((temp, temp))
        else:
            self.set_values((temp, max_))

    def max_if_editing(self, event):
        if self.focus_get() != self.min_entry:
            self.max_update_entries()
            return

        try:
            temp = float(self.max_entry.get())
            temp = min(max(self.lower_bound, temp), self.upper_bound)
            self.set_values([self.values[0], temp])
        except:
            self.set_values(self.values)

    def max_update_entries(self, event=None):
        temp = self.max_entry.get()
        try:
            temp = float(temp)
        except:
            self.set_values(self.values)
            return

        min_ = float(self.min_entry.get())
        temp = min(max(self.lower_bound, temp), self.upper_bound)
        if temp < min_:
            self.set_values((temp, temp))
        else:
            self.set_values((min_, temp))

    def set_values(self, v):
        self.values[0] = v[0]
        self.values[1] = v[1]
        self.min_entry.delete(0,tk.END)
        self.min_entry.insert(0,round(v[0],self.roundto))
        self.max_entry.delete(0,tk.END)
        self.max_entry.insert(0,round(v[1],self.roundto))

    def last_update(self):
        self.min_update_entries()
        self.max_update_entries()

    def set(self, new_range):
        self.set_values(new_range)

    def get(self):
        self.last_update()
        return self.values

class CellRangeEditor(tk.Frame):
    def __init__(self, parent, text, info):
        tk.Frame.__init__(self, parent)

        self.label = tk.Label(self, text=text, bg=parent.cget("bg"))
        self.label.grid(row=0, column=0, padx=(BODY_LEFT_MARGIN, 0), sticky="w")

        self.types = []
        temp_info = copy(info)
        for i in range(3):
            temp_info["range"] = info["range"][i]
            self.types.append(RangeEditor(self, None, temp_info, narrow=True))
            self.types[i].grid(row=0, column=i+1)
        self.columnconfigure(0, minsize=LABEL_WIDTH)
        self.columnconfigure(1, minsize=170)
        self.columnconfigure(2, minsize=170)
        self.columnconfigure(3, minsize=170)

        self.label.config(bg=parent.cget("bg"), fg=BODY_COLOR, font=BODY_FONT)

    def set(self, new_range):
        for value, widget in zip(new_range, self.types):
            widget.set(value)

    def get(self):
        new_range = []
        for each in self.types:
            new_range.append(each.get())
        return new_range

class InteractionRangeEditor(tk.Frame):
    def __init__(self, parent, text, info):
        tk.Frame.__init__(self, parent)
        #label
        self.label = tk.Label(self, text=text, fg=BODY_COLOR, font=BODY_FONT)
        self.label.grid(row=0, column=0, columnspan=4, padx=(BODY_LEFT_MARGIN, 0), sticky="w")

        #header
        self.header = [tk.Label(self, text=_) for _ in [""]+CELL_TYPE_LABELS]

        for i, each in enumerate(self.header):
            each.config(font=CELL_TYPE_HEADER_FONT, fg=CELL_TYPE_HEADER_COLOR)
            each.grid(row=1, column=i)

        #body
        self.row_headers = [tk.Label(self, text=_, font=CELL_TYPE_HEADER_FONT, fg=CELL_TYPE_HEADER_COLOR) for _ in CELL_TYPE_LABELS]
        temp_info = copy(info)
        self.entries = [[],[],[]]
        for i in range(3):
            for j in range(3-i):
                temp_info["range"] = info["range"][i][j]
                self.entries[i].append(RangeEditor(self, None, temp_info, narrow=True))


        for i in range(3):
            self.row_headers[i].grid(row=2+i, column=0, sticky="e", padx=(0,15))
            for j in range(3-i):
                self.entries[i][j].grid(row=2+i, column=1+i+j, sticky="w")

        self.columnconfigure(0, minsize=LABEL_WIDTH)
        self.columnconfigure(1, minsize=170)
        self.columnconfigure(2, minsize=170)
        self.columnconfigure(3, minsize=170)

        self.widgets = ([self.label]+self.header+self.row_headers)


    def set(self, new_range):
        for i in range(3):
            for j in range(3-i):
                self.entries[i][j].set(new_range[i][j])

    def get(self):
        new_range = [[],[],[]]
        for i in range(3):
            for j in range(3-i):
                new_range[i].append(self.entries[i][j].get())
        return new_range

class RangeSettingsWindow(tk.Frame):
    def __init__(self, master, session):
        tk.Frame.__init__(self, master)
        self.master = master
        master.wm_title("Parameter Range")
        master.protocol('WM_DELETE_WINDOW', self._close)

        self.session = session
        self.param_info = deepcopy(session.param_info)

        total_columns = 2
        header_space = 10
        left_space = 5

        #main params
        self.params = {}
        self.main_label = tk.Label(self, text="Main Parameters")
        self.main_label.grid(columnspan=total_columns, sticky="w", padx=left_space,
            pady=(header_space,0))

        for name in PARAM["main"]:
            self.params[name] = RangeEditor(self, name, self.param_info[name])
            self.params[name].grid(columnspan=total_columns, sticky="we")

        #cell params
        self.cell_label = tk.Label(self, text="Cell Parameters")
        self.cell_label.grid(columnspan=total_columns, sticky="w",
            pady=(header_space,0), padx=left_space)


        for name in PARAM["cell"]:
            info = self.param_info[name]
            if "type" not in info:
                self.params[name] = CellRangeEditor(self, name, info)
                self.params[name].grid(columnspan=total_columns, sticky="we")
            elif info["type"] == "qualitative":
                temp = tk.Frame(self)
                self.cell_types_headers = [tk.Label(temp, text=_, font=CELL_TYPE_HEADER_FONT, fg=CELL_TYPE_HEADER_COLOR) for _ in [""]+CELL_TYPE_LABELS]
                for i, each in enumerate(self.cell_types_headers):
                    each.grid(row=0, column=i)
                temp.grid(columnspan=total_columns,sticky="we", pady=(10,0))
                temp.columnconfigure(0, minsize=LABEL_WIDTH)
                temp.columnconfigure(1, minsize=170)
                temp.columnconfigure(2, minsize=170)
                temp.columnconfigure(3, minsize=170)
                self.params[name] = QualitativeRangeEditor(self, name, info)
                self.params[name].grid(columnspan=total_columns, sticky="we")
            elif info["type"] == "ratio":
                self.params[name] = RatioRangeEditor(self, info)
                self.params[name].grid(columnspan=total_columns, sticky="we")

        #interaction params
        self.interaction_label = tk.Label(self, text="Interaction Parameters")
        self.interaction_label.grid(columnspan=total_columns, sticky="w",
            pady=(header_space,0), padx=left_space)
        name = PARAM["interaction"][0]
        self.params[name] = InteractionRangeEditor(self, name, self.param_info[name])
        self.params[name].grid(columnspan=total_columns, sticky="we")

        self.headers = [self.main_label, self.cell_label, self.interaction_label]
        for each in self.headers:
            each.config(bg=self.cget("bg"),fg=HEADER_COLOR, font=HEADER_FONT)

        #buttons
        temp = tk.Frame(self)
        self.default_button = tk.Button(temp, text="Default", width=7, command=self.default)
        self.apply_button = tk.Button(temp, text="Apply", width=7, command=self.apply)
        temp.grid(columnspan=2, sticky="e", padx=10, pady=(10,0))
        self.default_button.grid(row=0, column=0, sticky="e", padx=3)
        self.apply_button.grid(row=0, column=1, sticky="w", padx=3)

    def _close(self):
        self.master.destroy()

    def set(self, new_settings):
        for name, w in self.params.items():
            w.set(new_settings[name]["range"])

    def get(self):
        for name, w in self.params.items():
            self.param_info[name]["range"] = w.get()
        return self.param_info

    def apply(self):
        param_info = self.get()
        self.session.set("param_info", param_info)

    def default(self):
        from common.parameters import PARAM_INFO
        param_info= deepcopy(PARAM_INFO)
        self.set(param_info)
        self.session.set("param_info", param_info)
