import Tkinter as tk
import tkMessageBox
from copy import deepcopy

from common.parameters import GLOBAL_STATS_NAMES
from common.styles import BODY_COLOR, BODY_FONT
from common.tools import is_within


class EvolvePropertyWindow(tk.Frame):
    def __init__(self, master, evolve_property_settings, func):
        tk.Frame.__init__(self, master)
        self.master = master
        self.func = func
        master.wm_title("Evolve by Property")
        master.protocol('WM_DELETE_WINDOW', self.close)

        spacing=5

        # Which global property to be the fitness function
        self.which_prop_label = tk.Label(self, text="Fitness function:", font=BODY_FONT, fg=BODY_COLOR)
        self.which_prop_label.grid(row=0, column=0, pady=spacing)

        self.which_prop = tk.StringVar()
        self.which_prop_menu = tk.OptionMenu(self, self.which_prop, *GLOBAL_STATS_NAMES)
        self.which_prop_menu.config(width=20, font=BODY_FONT)
        self.which_prop_menu.grid(row=0, column=1, columnspan=3, pady=spacing)

        # Number of generations to be evolved
        self.num_gen_label = tk.Label(self, text="Number of generations:", font=BODY_FONT, fg=BODY_COLOR)
        self.num_gen_label.grid(row=1, column=0, pady=spacing)

        def is_int(value):
            if value == "": return True
            if (len(value) > 3): return False
            try:
                if is_within(int(value), 0, 999): return True
            except:
                pass
            return False

        is_int_vcmd = (self.register(is_int),'%P')

        self.num_gen_entry = tk.Entry(self, width=3, validate="all", validatecommand=is_int_vcmd, font=BODY_FONT, fg=BODY_COLOR)
        self.num_gen_entry.grid(row=1, column=1, columnspan=3, pady=spacing)

        # Range of steps to calculate fitness from
        self.equi_range_label = tk.Label(self, text="Significant step range:", font=BODY_FONT, fg=BODY_COLOR)
        self.equi_range_label.grid(row=2, column=0, pady=spacing)

        self.equi_range_entry0 = tk.Entry(self, width=3, validate="all", validatecommand=is_int_vcmd, font=BODY_FONT, fg=BODY_COLOR)
        self.equi_range_entry0.grid(row=2, column=1, sticky="e", pady=spacing)

        self.equi_range_labelsub = tk.Label(self, text="-", font=BODY_FONT, fg=BODY_COLOR)
        self.equi_range_labelsub.grid(row=2, column=2, sticky="we", pady=spacing)

        self.equi_range_entry1 = tk.Entry(self, width=3, validate="all", validatecommand=is_int_vcmd, font=BODY_FONT, fg=BODY_COLOR)
        self.equi_range_entry1.grid(row=2, column=3, sticky="w", pady=spacing)


        # Buttons
        self.default_button = tk.Button(self, text="Default", width=7, command=self.default)
        self.evolve_button = tk.Button(self, text="Evolve!", width=7, command=self.evolve)
        self.default_button.grid(row=3, column=1, sticky="e", padx=3, pady=(10,0))
        self.evolve_button.grid(row=3, column=3, sticky="w", padx=3, pady=(10,0))

        self.columnconfigure(0, weight=5)
        self.columnconfigure(1, weight=2)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=2)

        self.set_values(evolve_property_settings)


    def close(self):
        self.master.destroy()

    def set_values(self, settings):
        self.which_prop.set(settings["which_prop"])
        self.num_gen_entry.delete(0,tk.END)
        self.num_gen_entry.insert(0,settings["num_gen"])
        self.equi_range_entry0.delete(0,tk.END)
        self.equi_range_entry0.insert(0,settings["equi_range"][0])
        self.equi_range_entry1.delete(0,tk.END)
        self.equi_range_entry1.insert(0,settings["equi_range"][1])

    def evolve(self):
        num_gen = self.num_gen_entry.get()
        equi_range0 = self.equi_range_entry0.get()
        equi_range1 = self.equi_range_entry1.get()
        if (num_gen=="") or (equi_range0=="") or (equi_range1==""):
            return

        num_gen = int(num_gen)
        equi_range0 = int(equi_range0)
        equi_range1 = int(equi_range1)

        if (equi_range0 >= equi_range1):
            tkMessageBox.showerror("Invalid Input", "Please enter a valid step range!")
            return

        new_settings = {
            "which_prop" : self.which_prop.get(),
            "num_gen" : num_gen,
            "equi_range": (equi_range0, equi_range1)
        }
        self.func(new_settings)

    def default(self):
        from common.parameters import EVOLVE_PROPERTY_SETTINGS
        new_settings= deepcopy(EVOLVE_PROPERTY_SETTINGS)
        self.set_values(new_settings)
