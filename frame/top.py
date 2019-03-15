import Tkinter as tk

from common.styles import BUTTON_X_MARGIN, LG_BODY_COLOR, LG_BODY_FONT
from common.tools import create_buttons, is_within


class ReversedCheckbutton(tk.Frame):
    def __init__(self, parent, text, variable, command):
        tk.Frame.__init__(self, parent)
        self.checkbutton = tk.Checkbutton(self, variable=variable, command=command)

        self.label = tk.Label(self, text=text)
        self.label.grid(row=0, column=0)
        self.checkbutton.grid(row=0, column=1)

        self.widgets = [self.checkbutton, self.label]

class AddStepsWidget(tk.Frame):
    def __init__(self, parent, func, text="Add Steps:"):
        tk.Frame.__init__(self, parent, bg=parent.cget("bg"))
        if func is None:
            def do_nothing(*args, **kwargs):
                pass
            func = do_nothing
        self.func=func

        self.l = tk.Label(self, text=text, bg=self.cget("bg"))

        vcmd = (self.register(self.is_okay),'%P')
        self.v = tk.StringVar()
        self.v.set('20')
        self.s = tk.Spinbox(self, width=5, from_=20, to=9980, increment=20,
            textvariable=self.v, validate="all",
            validatecommand=vcmd)

        self.s.bind("<Command-a>", self.spinbox_select_all)

        self.b = tk.Button(self, text="Go!", command=self.go, bg=self.cget("bg"), padx=BUTTON_X_MARGIN)

        self.widgets = [self.l, self.s, self.b]

        for i, each in enumerate(self.widgets):
            each.grid(row=0, column=i)

    def is_okay(self, value):
        if value == "": return True
        if (len(value) > 4): return False
        try:
            if is_within(int(value), 0, 9999): return True
        except:
            pass
        return False

    def spinbox_select_all(self, event):
        self.s.selection("range", 0, tk.END)

    def go(self):
        v = self.v.get()
        if v == "":
            return
        v = int(v)
        self.func(v)

class ButtonsFrame(tk.Frame):
    def __init__(self, parent, session, new_pop_command, mutate_command, cross_command, add_command):
        tk.Frame.__init__(self, parent)
        self.new_pop = new_pop_command
        self.mutate = mutate_command
        self.cross = cross_command
        self.session = session
        session.bind("general_settings", self.update_checkbutton)

        buttons_row = 0
        buttons = create_buttons(self,
            {"new_pop":["New Population", buttons_row, 0],
             "mutate":["Mutate", buttons_row, 1],
             "cross":["Crossover", buttons_row, 2]
        })
        self.new_pop_button, self.mutate_button, self.cross_button = buttons

        self.add_steps_widget = AddStepsWidget(self, add_command)
        self.add_steps_widget.grid(row=buttons_row, column=3, padx=30)

        self.show_movement_intvar = tk.IntVar()
        self.show_movement_checkbutton = ReversedCheckbutton(self,
            text = "Show Movement", variable=self.show_movement_intvar,
            command=self.show_movement
        )
        self.show_movement_checkbutton.grid(row=buttons_row, column=4)

        self.widgets = buttons.values() + [
            self.add_steps_widget,
            self.show_movement_checkbutton
        ]

    def grid_(self):
        self.grid()

    def update_checkbutton(self):
        movement = self.session.general_settings["show_movement"]
        if movement != self.show_movement_intvar.get():
            self.show_movement_intvar.set(movement)

    def show_movement(self):
        new_settings = self.session.general_settings
        new_settings["show_movement"] = self.show_movement_intvar.get()
        self.session.set("general_settings", new_settings)

class MutateFrame(tk.Frame):
    def __init__(self, parent, session, mutate_func, advanced_frame):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.session = session
        self.mutate_func = mutate_func
        self.advanced_frame = advanced_frame
        self.label = tk.Label(self, text="Choose a parent", fg=LG_BODY_COLOR, font=LG_BODY_FONT)
        self.label.grid(row=0, column=1)

        self.buttons = create_buttons(self, {
            "ok":["Mutate!", 0, 1], #u"\u2713"
            "cancel": ["<Back", 0, 0], # \u21a9
            "advanced": ["Advanced", 0, 2]
        })

        #self.buttons["ok"].config(state=tk.DISABLED)
        #self.buttons["ok"].grid(sticky="w")
        self.buttons["ok"].grid_remove()
        self.buttons["cancel"].grid(sticky="w")
        self.buttons["advanced"].grid(sticky="e")

        for i, weight in enumerate([1,1,1]):
            self.columnconfigure(i, weight=weight, minsize=50)
    def grid_(self):
        self.buttons["ok"].grid_remove()
        self.label.grid()
        self.grid()

    def chosen(self, graph):
        self.reveal_button()
        self.current_chosen = graph

    def reveal_button(self):
        self.label.grid_remove()
        self.buttons["ok"].grid()
        #self.buttons["ok"].config(state=tk.NORMAL)
        self.update()

    def ok(self):
        self.session.set("advanced_mutate", self.advanced_frame.get())
        self.mutate_func(self.current_chosen.sim)
        self.cancel()

    def cancel(self):
        self.advanced_frame.grid_remove()
        self.parent.back_to_home_topframe()

    def advanced(self):
        self.advanced_frame.grid()

class CrossFrame(tk.Frame):
    def __init__(self, parent, cross_func):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.cross_func = cross_func

        self.label = tk.Label(self, text="Choose parents", fg=LG_BODY_COLOR, font=LG_BODY_FONT)
        self.label.grid(row=0, column=1)

        self.buttons = create_buttons(self, {
            "ok":["Crossover!", 0, 1], #u"\u2713"
            "cancel": ["<Back", 0, 0], # \u21a9
        })

        #self.buttons["ok"].config(state=tk.DISABLED)
        #self.buttons["ok"].grid(sticky="w")
        self.buttons["ok"].grid_remove()
        self.buttons["cancel"].grid(sticky="w")

        for i, weight in enumerate([1,1,1]):
            self.columnconfigure(i, weight=weight, minsize=50)

    def grid_(self):
        self.unreveal_button()
        self.grid()

    def chosen(self, graphs):
        if len(graphs)>=2:
            self.reveal_button()
        else:
            self.unreveal_button()

        self.current_chosen = graphs

    def reveal_button(self):
        self.label.grid_remove()
        self.buttons["ok"].grid()
        #self.buttons["ok"].config(state=tk.NORMAL)
        self.update()

    def unreveal_button(self):
        self.buttons["ok"].grid_remove()
        self.label.grid()
        self.update()

    def ok(self):
        self.cross_func([_.sim for _ in self.current_chosen])
        self.cancel()

    def cancel(self):
        self.parent.back_to_home_topframe()

class InsertLibFrame(tk.Frame):
    def __init__(self, parent, insert_func):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.insert_func = insert_func

        self.label = tk.Label(self, text="Choose locations to replace", fg=LG_BODY_COLOR, font=LG_BODY_FONT)
        self.label.grid(row=0, column=1)

        self.buttons = create_buttons(self, {
            "ok":["Insert!", 0, 1], #u"\u2713"
            "cancel": ["<Back", 0, 0], # \u21a9
        })

        self.all_intvar = tk.IntVar()
        self.all_checkbutton = ReversedCheckbutton(self, "All", self.all_intvar, self.check_all)
        #self.buttons["ok"].config(state=tk.DISABLED)
        #self.buttons["ok"].grid(sticky="w")
        self.all_checkbutton.grid(row=0, column=2, sticky="e")
        self.buttons["ok"].grid_remove()
        self.buttons["cancel"].grid(sticky="w")

        for i, weight in enumerate([1,1,1]):
            self.columnconfigure(i, weight=weight)

    def grid_(self):
        self.unreveal_button()
        self.grid()

    def chosen(self, graphs):
        if len(graphs) >= 1:
            self.reveal_button()
        else:
            self.unreveal_button()
        self.current_chosen = graphs

    def reveal_button(self):
        self.label.grid_remove()
        self.buttons["ok"].grid()
        #self.buttons["ok"].config(state=tk.NORMAL)
        self.update()

    def unreveal_button(self):
        self.buttons["ok"].grid_remove()
        self.label.grid()
        self.update()

    def ok(self):
        self.insert_func(self.chosen_gene, [_.sim for _ in self.current_chosen])
        self.parent.expand_range_settings(self.chosen_gene)
        self.chosen_gene = None
        self.cancel()

    def cancel(self):
        self.all_intvar.set(0)
        self.parent.back_to_home_topframe()

    def check_all(self):
        if self.all_intvar.get() == 1:
            self.parent.frames["sims"].choose_all()
            self.reveal_button()
        else:
            self.parent.frames["sims"].clear_all_selection()
            self.unreveal_button()


class EvolvingFrame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent

        self.display_text = tk.StringVar()
        self.label = tk.Label(self, textvariable=self.display_text, fg=LG_BODY_COLOR, font=LG_BODY_FONT)
        self.label.grid(row=0, column=1)

        self.buttons = create_buttons(self, {
            "cancel": ["<Back", 0, 0], # \u21a9
        })

        #self.buttons["ok"].grid_remove()
        self.buttons["cancel"].grid(sticky="w")
        self.buttons["cancel"].grid_remove()

        for i, weight in enumerate([1,1,1]):
            self.columnconfigure(i, weight=weight, minsize=50)

    def grid_(self):
        self.buttons["cancel"].grid_remove()
        self.display_text.set("")
        self.grid()

    def done(self):
        self.buttons["cancel"].grid()

    def cancel(self):
        self.parent.back_to_home_topframe()
