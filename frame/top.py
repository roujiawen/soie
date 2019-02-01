from common.styles import *
from common.tools import *

class ReversedCheckbutton(Frame):
    def __init__(self, parent, text, variable, command):
        Frame.__init__(self, parent)
        self.checkbutton = Checkbutton(self, variable=variable, command=command)

        self.label = Label(self, text=text)
        self.label.grid(row=0, column=0)
        self.checkbutton.grid(row=0, column=1)

        self.widgets = [self.checkbutton, self.label]

class AddStepsWidget(Frame):
    def __init__(self, parent, func, text="Add Steps:"):
        Frame.__init__(self, parent, bg=parent.cget("bg"))
        if func is None:
            def do_nothing(*args, **kwargs):
                pass
            func = do_nothing
        self.func=func

        self.l = Label(self, text=text, bg=self.cget("bg"))

        vcmd = (self.register(self.is_okay),'%P')
        self.v = StringVar()
        self.v.set('20')
        self.s = Spinbox(self, width=3, from_=20, to=980, increment=20,
            textvariable=self.v, validate="all",
            validatecommand=vcmd)

        self.s.bind("<Command-a>", self.spinbox_select_all)

        self.b = Button(self, text="Go!", command=self.go, bg=self.cget("bg"))

        self.widgets = [self.l, self.s, self.b]

        for i, each in enumerate(self.widgets):
            each.grid(row=0, column=i)

    def is_okay(self, value):
        if value == "": return True
        if (len(value) > 3): return False
        try:
            if is_within(int(value), 0, 999): return True
        except:
            pass
        return False

    def spinbox_select_all(self, event):
        self.s.selection("range", 0, END)

    def go(self):
        v = self.v.get()
        if v == "":
            return
        v = int(v)
        self.func(v)

class ButtonsFrame(Frame):
    def __init__(self, parent, session, new_pop_command, mutate_command, cross_command, add_command):
        Frame.__init__(self, parent)
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

        self.show_movement_intvar = IntVar()
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

    def freeze(self):
        recursive_freeze(self)

class MutateFrame(Frame):
    def __init__(self, parent, session, mutate_func, advanced_frame):
        Frame.__init__(self, parent)
        self.parent = parent
        self.session = session
        self.mutate_func = mutate_func
        self.advanced_frame = advanced_frame
        self.label = Label(self, text="Choose a parent", fg=LG_BODY_COLOR, font=LG_BODY_FONT)
        self.label.grid(row=0, column=1)

        self.buttons = create_buttons(self, {
            "ok":["Mutate!", 0, 1], #u"\u2713"
            "cancel": ["<Back", 0, 0], # \u21a9
            "advanced": ["Advanced", 0, 2]
        })

        #self.buttons["ok"].config(state=DISABLED)
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
        #self.buttons["ok"].config(state=NORMAL)
        self.update()

    def ok(self):
        self.session.set("advanced_mutate", self.advanced_frame.get())
        self.mutate_func(self.current_chosen.sim)
        self.cancel()

    def cancel(self):
        self.advanced_frame.grid_remove()
        self.parent.cancel_choose_mode()

    def advanced(self):
        self.advanced_frame.grid()

class CrossFrame(Frame):
    def __init__(self, parent, cross_func):
        Frame.__init__(self, parent)
        self.parent = parent
        self.cross_func = cross_func

        self.label = Label(self, text="Choose parents", fg=LG_BODY_COLOR, font=LG_BODY_FONT)
        self.label.grid(row=0, column=1)

        self.buttons = create_buttons(self, {
            "ok":["Crossover!", 0, 1], #u"\u2713"
            "cancel": ["<Back", 0, 0], # \u21a9
        })

        #self.buttons["ok"].config(state=DISABLED)
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
        #self.buttons["ok"].config(state=NORMAL)
        self.update()

    def unreveal_button(self):
        self.buttons["ok"].grid_remove()
        self.label.grid()
        self.update()

    def ok(self):
        self.cross_func([_.sim for _ in self.current_chosen])
        self.cancel()

    def cancel(self):
        self.parent.cancel_choose_mode()


class InsertLibFrame(Frame):
    def __init__(self, parent, insert_func):
        Frame.__init__(self, parent)
        self.parent = parent
        self.insert_func = insert_func

        self.label = Label(self, text="Choose locations to replace", fg=LG_BODY_COLOR, font=LG_BODY_FONT)
        self.label.grid(row=0, column=1)

        self.buttons = create_buttons(self, {
            "ok":["Insert!", 0, 1], #u"\u2713"
            "cancel": ["<Back", 0, 0], # \u21a9
        })

        self.all_intvar = IntVar()
        self.all_checkbutton = ReversedCheckbutton(self, "All", self.all_intvar, self.check_all)
        #self.buttons["ok"].config(state=DISABLED)
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
        #self.buttons["ok"].config(state=NORMAL)
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
        self.parent.cancel_choose_mode()

    def check_all(self):
        if self.all_intvar.get() == 1:
            self.parent.sims_frame.choose_all()
            self.reveal_button()
        else:
            self.parent.sims_frame.clear_all_selection()
            self.unreveal_button()
