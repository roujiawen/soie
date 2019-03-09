import Tkinter as tk
from copy import deepcopy

from common.styles import BODY_COLOR
from common.tools import fit_into

GENERAL_SETTINGS_LG_FONT = ('Helvetica', '12')
GENERAL_SETTINGS_SM_FONT = ('Helvetica', '9')

class ShowTailEditor(tk.Frame):
    def __init__(self, parent, row=0, value1=5.0, value2=0.5, from1=0.1, to1=30.0, roundto1=1, from2=0.01, to2=1.0, roundto2=2):
        tk.Frame.__init__(self, parent)
        self.roundto1=roundto1
        self.lowerbound1 = from1
        self.upperbound1 = to1
        self.maxlen1 = [len(str(int(to1))), roundto1]
        self.roundto2=roundto2
        self.lowerbound2 = from2
        self.upperbound2 = to2
        self.maxlen2 = [len(str(int(to2))), roundto2]

        vcmd1 = (self.register(self.is_okay1),'%P')
        vcmd2 = (self.register(self.is_okay2),'%P')

        self.value1 = value1
        self.value2 = value2

        self.label1 = tk.Label(self, text="length:",font=GENERAL_SETTINGS_SM_FONT, fg=BODY_COLOR)
        self.label1.grid(row=0, column=0)

        self.entry1 = tk.Entry(self, width=3, validate="all", validatecommand=vcmd1, font=GENERAL_SETTINGS_SM_FONT, fg=BODY_COLOR)
        self.entry1.grid(row=0, column=1)

        self.entry1.bind('<Return>', self.update_value1)
        self.entry1.bind('<FocusOut>', self.update_value1)

        self.set_value1(value1)

        self.label2 = tk.Label(self, text="  alpha:", font=GENERAL_SETTINGS_SM_FONT, fg=BODY_COLOR)
        self.label2.grid(row=0, column=2)

        self.entry2 = tk.Entry(self, width=3, validate="all", validatecommand=vcmd2, font=GENERAL_SETTINGS_SM_FONT, fg=BODY_COLOR)
        self.entry2.grid(row=0, column=3)

        self.entry2.bind('<Return>', self.update_value2)
        self.entry2.bind('<FocusOut>', self.update_value2)

        self.set_value2(value2)

        self.grid(row=row, padx=30, sticky="w")

    def is_okay1(self, value):
        if value in ["", "."]: return True
        try:
            float(value)
            splitted = value.split(".")
            if any(len(splitted[i])>self.maxlen1[i] for i in range(len(splitted))):
                return False
            return True
        except:
            return False

    def is_okay2(self, value):
        if value in ["", "."]: return True
        try:
            float(value)
            splitted = value.split(".")
            if any(len(splitted[i])>self.maxlen2[i] for i in range(len(splitted))):
                return False
            return True
        except:
            return False

    def update_value1(self, event=None):
        temp = self.entry1.get()
        try:
            temp=float(temp)
        except:
            self.set_value1(self.value1)
            return

        self.set_value1(fit_into(temp, self.lowerbound1, self.upperbound1))

    def set_value1(self, v):
        self.value1 = v
        self.entry1.delete(0, tk.END)
        self.entry1.insert(0, round(v, self.roundto1))

    def update_value2(self, event=None):
        temp = self.entry2.get()
        try:
            temp=float(temp)
        except:
            self.set_value2(self.value2)
            return

        self.set_value2(fit_into(temp, self.lowerbound2, self.upperbound2))

    def set_value2(self, v):
        self.value2 = v
        self.entry2.delete(0, tk.END)
        self.entry2.insert(0, round(v, self.roundto2))

    def last_update(self):
        self.update_value1()
        self.update_value2()

    def disable(self):
        self.entry1["state"] = "disabled"
        self.label1["state"] = "disabled"
        self.entry2["state"] = "disabled"
        self.label2["state"] = "disabled"

    def activate(self):
        self.entry1["state"] = "normal"
        self.label1["state"] = "normal"
        self.entry2["state"] = "normal"
        self.label2["state"] = "normal"

    def set(self, l):
        self.set_value1(l[0])
        self.set_value2(l[1])
    def get(self):
        return [self.value1, self.value2]

class ZoomInEditor(tk.Frame):
    def __init__(self, parent, row=0, value=1.0, from_=0.1, to=10.0, roundto=2):
        tk.Frame.__init__(self, parent)
        self.roundto=roundto
        self.lowerbound = from_
        self.upperbound = to
        self.value = value
        self.maxlen = [len(str(int(to))), roundto]

        vcmd = (self.register(self.is_okay),'%P')

        self.entry = tk.Entry(self, width=3, validate="all", validatecommand=vcmd, font=GENERAL_SETTINGS_SM_FONT, fg=BODY_COLOR)
        self.entry.grid(row=0, column=0)

        self.label = tk.Label(self, text="x",font=GENERAL_SETTINGS_SM_FONT, fg=BODY_COLOR)
        self.label.grid(row=0, column=1)

        self.square_size_stringvar = tk.StringVar()
        self.square_size_stringvar.set("     (Resulting Square Size: 10x10)")
        self.square_size = tk.Label(self, textvariable=self.square_size_stringvar,font=GENERAL_SETTINGS_SM_FONT, fg=BODY_COLOR, width=30)
        self.square_size.grid(row=0, column=2)

        self.entry.bind('<Return>', self.update_value)
        self.entry.bind('<FocusOut>', self.update_value)

        self.set_value(value)
        self.grid(row=row, padx=30, sticky="w")

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

    def set(self, value):
        self.set_value(value)

    def get(self):
        return self.value
    def update_value(self, event=None):
        temp = self.entry.get()
        try:
            temp=float(temp)
        except:
            self.set_value(self.value)
            return
        self.set_value(fit_into(temp, self.lowerbound, self.upperbound))

    def set_value(self, v):
        self.value = v
        self.entry.delete(0, tk.END)
        self.entry.insert(0, round(v, self.roundto))
        self.square_size_stringvar.set("     (Resulting Square Size: {}x{})".format(round(10.0/v, 1), round(10.0/v, 1)))

    def last_update(self):
        self.update_value()

    def disable(self):
        self.entry["state"] = "disabled"
        self.label["state"] = "disabled"

    def activate(self):
        self.entry["state"] = "normal"
        self.label["state"] = "normal"

class ShowMovementEditor(tk.Frame):
    def __init__(self, parent, row=0, value=10, from_=1, to=500):
        tk.Frame.__init__(self, parent)
        self.lowerbound = from_
        self.upperbound = to
        self.value = value
        self.maxlen = len(str(int(to)))

        vcmd = (self.register(self.is_okay),'%P')

        self.label1 = tk.Label(self, text="for every", font=GENERAL_SETTINGS_SM_FONT, fg=BODY_COLOR)
        self.label1.grid(row=0, column=0)

        self.entry = tk.Entry(self, width=3, validate="all", validatecommand=vcmd, font=GENERAL_SETTINGS_SM_FONT, fg=BODY_COLOR)
        self.entry.grid(row=0, column=1)

        self.label2 = tk.Label(self, text="time step(s)", font=GENERAL_SETTINGS_SM_FONT, fg=BODY_COLOR)
        self.label2.grid(row=0, column=2)

        self.entry.bind('<Return>', self.update_value)
        self.entry.bind('<FocusOut>', self.update_value)

        self.set_value(value)
        self.grid(row=row, padx=30, sticky="w")

    def is_okay(self, value):
        if len(value) == 0: return True
        try:
            int(value)
            if len(value)>self.maxlen:
                return False
            return True
        except:
            return False

    def set(self, value):
        self.set_value(value)

    def get(self):
        return self.value

    def update_value(self, event=None):
        temp = self.entry.get()
        try:
            temp=float(temp)
        except:
            self.set_value(self.value)
            return
        self.set_value(fit_into(temp, self.lowerbound, self.upperbound))

    def set_value(self, v):
        self.value = int(v)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, int(v))

    def last_update(self):
        self.update_value()

    def disable(self):
        self.entry["state"] = "disabled"
        self.label1["state"] = "disabled"
        self.label2["state"] = "disabled"

    def activate(self):
        self.entry["state"] = "normal"
        self.label1["state"] = "normal"
        self.label2["state"] = "normal"

class GeneralSettingsWindow(tk.Frame):
    def __init__(self, master, general_settings, func):
        tk.Frame.__init__(self, master)
        self.master = master
        self.func = func
        master.wm_title("Advanced Control")
        master.protocol('WM_DELETE_WINDOW', self.close)

        subframe_spacing=5
        indent = 25

        # Show Trace
        temp=tk.Frame(self)
        self.show_tail_intvar = tk.IntVar()
        self.show_tail_check = tk.Checkbutton(
            temp,
            text = "Show Velocity Trace",
            variable=self.show_tail_intvar,
            command=self.show_tail_click,
            font=GENERAL_SETTINGS_LG_FONT, fg=BODY_COLOR
        )
        self.show_tail_editor = ShowTailEditor(
            temp,
            row=1
            )
        self.show_tail_check.grid(row=0, sticky="w")
        self.show_tail_editor.grid(row=1, padx=indent, sticky="w")
        temp.grid(sticky="w", pady=subframe_spacing)
        # Show Movement
        temp = tk.Frame(self)
        self.show_movement_intvar = tk.IntVar()
        self.show_movement_check = tk.Checkbutton(
            temp,
            text = "Show Movement",
            variable=self.show_movement_intvar,
            command=self.show_movement_click,
            font=GENERAL_SETTINGS_LG_FONT, fg=BODY_COLOR
        )
        self.show_movement_editor = ShowMovementEditor(
            temp,
            row=3)
        self.show_movement_check.grid(row=0, sticky="w")
        self.show_movement_editor.grid(row=1, padx=indent, sticky="w")
        temp.grid(sticky="w", pady=subframe_spacing)
        # Zoom In
        temp = tk.Frame(self)
        self.zoom_in_intvar = tk.IntVar()
        self.zoom_in_check = tk.Checkbutton(
            temp,
            text = "Zoom In",
            variable=self.zoom_in_intvar,
            command=self.zoom_in_click,
            font=GENERAL_SETTINGS_LG_FONT, fg=BODY_COLOR
        )
        self.zoom_in_editor = ZoomInEditor(
            temp,
            row=5
        )
        self.zoom_in_check.grid(row=0, sticky="w")
        self.zoom_in_editor.grid(row=1, padx=indent, sticky="w")
        temp.grid(sticky="w", pady=subframe_spacing)
        # Periodic Boundary
        self.periodic_boundary_intvar = tk.IntVar()
        self.periodic_boundary_intvar.set(general_settings["periodic_boundary"])
        self.periodic_boundary_check = tk.Checkbutton(
            self,
            text = "Periodic Boundary",
            variable=self.periodic_boundary_intvar,
            font=GENERAL_SETTINGS_LG_FONT, fg=BODY_COLOR
        )
        self.periodic_boundary_check.grid(sticky="w", pady=subframe_spacing)

        # Buttons
        temp = tk.Frame(self)
        self.default_button = tk.Button(temp, text="Default", width=7, command=self.default)
        self.apply_button = tk.Button(temp, text="Apply", width=7, command=self.apply)
        temp.grid(column=0, columnspan=2, sticky="e", padx=10, pady=(10,0))
        self.default_button.grid(row=0, column=0, sticky="e", padx=3)
        self.apply_button.grid(row=0, column=1, sticky="w", padx=3)

        self.set_values(general_settings)

    def show_tail_click(self, event=None):
        if self.show_tail_intvar.get() == 0:
            self.show_tail_editor.disable()
        else:
            self.show_tail_editor.activate()

    def show_movement_click(self, event=None):
        if self.show_movement_intvar.get() == 0:
            self.show_movement_editor.disable()
        else:
            self.show_movement_editor.activate()

    def zoom_in_click(self, event=None):
        if self.zoom_in_intvar.get() == 0:
            self.zoom_in_editor.disable()
        else:
            self.zoom_in_editor.activate()

    def close(self):
        self.master.destroy()

    def set_values(self, settings):
        self.show_tail_intvar.set(settings["show_tail"])
        self.show_tail_editor.set(settings["show_tail_value"])
        self.show_movement_intvar.set(settings["show_movement"])
        self.show_movement_editor.set(settings["show_movement_value"])
        self.zoom_in_intvar.set(settings["zoom_in"])
        self.zoom_in_editor.set(settings["zoom_in_value"])
        self.periodic_boundary_intvar.set(settings["periodic_boundary"])
        # Deactivate editor if checks are off
        self.show_tail_click()
        self.show_movement_click()
        self.zoom_in_click()

    def last_update(self):
        self.show_tail_editor.last_update()
        self.show_movement_editor.last_update()
        self.zoom_in_editor.last_update()

    def apply(self):
        """
        FORMATTING
        new_settings {
           "show_tail" : 0,
           "show_tail_value" : [5.0, 0.3],
           "show_movement" : 0,
           "show_movement_value" : 5,
           "zoom_in" : 0,
           "zoom_in_value" : 2.0,
           "periodic_boundary" : 0
        }
        """
        self.last_update()
        new_settings = {
            "show_tail" : self.show_tail_intvar.get(),
            "show_tail_value" : self.show_tail_editor.get(),
            "show_movement" : self.show_movement_intvar.get(),
            "show_movement_value" : self.show_movement_editor.get(),
            "zoom_in" : self.zoom_in_intvar.get(),
            "zoom_in_value" : self.zoom_in_editor.get(),
            "periodic_boundary" : self.periodic_boundary_intvar.get()
        }
        self.func(new_settings)

    def default(self):
        from common.parameters import GENERAL_SETTINGS
        new_settings= deepcopy(GENERAL_SETTINGS)
        self.set_values(new_settings)
        self.func(new_settings)
