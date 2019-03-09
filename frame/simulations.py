import Tkinter as tk
import tkMessageBox

from common.io_utils import save_gene
from common.plotting import PlotWidget
from common.styles import (AXIS_LIMIT, EVOLVING_BORDER_COLOR, ON_CLICK_COLOR,
                           ON_HOVER_COLOR, ON_SELECT_COLOR, SIMS_FRAME_COLOR)
from frame.editwindow import EditWindow


class GraphFrame(tk.Frame):
    def __init__(self, parent, session, sim, info_frame, figsize=(2.15, 2.15), dpi=100):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.session = session
        sim.bind("state", self.update_graph)
        session.bind("vt", self.update_graph)
        self.sim = sim
        self.info_frame = info_frame
        self.selected = False
        self.state="NORMAL"
        self.double_clicked = False

        scale_factor = session.sf
        adjusted_limit = AXIS_LIMIT / scale_factor
        self.widget = PlotWidget(self, figsize=figsize, dpi=dpi, no_edge=True, axis="off",
            xlim=[0, adjusted_limit], ylim=[0, adjusted_limit])
        self.dots = (figsize[0]*dpi)**2

        highlight_thickness = 4
        self.widget.grid(pady=highlight_thickness, padx=highlight_thickness)
        self.widget.bind("<Enter>", self.on_hover)
        self.widget.bind("<Leave>", self.off_hover)
        self.widget.bind("<Button-2>", self.popup) #button-3 on windows
        self.widget.bind('<Double-Button-1>', self.edit)
        self.widget.bind("<ButtonRelease-1>", self.on_click)

        # Popup Menu
        self.popup_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_command(label="Edit", command=self.edit)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label="Restart", command=self.restart)
        self.popup_menu.add_command(label="Randomize", command=self.randomize)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label="Copy", command=self.copy, accelerator='Command-C')
        self.popup_menu.add_command(label="Paste", command=self.paste, accelerator='Command-V')
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label="Add to Library", command=self.click_and_save, accelerator='Command-S')

        self.bind("<Button-2>", self.popup)
        #self.freeze()

    def update_graph(self):
        self.widget.plot_sim(self.session, self.sim, self.dots)
        self.update()

    def bind_(self):
        self.widget.bind("<Button-2>", self.popup)
        self.widget.bind('<Double-Button-1>', self.edit)
    def unbind_(self):
        self.widget.unbind("<Button-2>")
        self.widget.unbind('<Double-Button-1>')
    def freeze(self):
        self.state = "DISABLED"
        for each in [0,2,3,6]:
            self.popup_menu.entryconfigure(each,state=tk.DISABLED)

    def unfreeze(self):
        self.state = "NORMAL"
        for each in [0,2,3,6]:
            self.popup_menu.entryconfigure(each,state=tk.NORMAL)

    def restart(self):
        self.on_click()
        self.sim.restart()

    def randomize(self):
        self.on_click()
        self.sim.randomize()

    def click_and_save(self):
        self.on_click()
        self.save()
        tkMessageBox.showinfo("", "Successfully saved!")

    def save(self):
        params = self.sim.genotype.parameters
        fig = self.widget.figure
        save_gene(params, fig)

    def popup(self, event):
        self.popup_menu.post(event.x_root, event.y_root)

    def edit(self, event=None):
        if self.state == "DISABLED": return
        self.freeze()
        t = tk.Toplevel(self)
        self.edit_window = EditWindow(self, t, self.session, self.sim)

    def copy(self):
        self.parent.copied = self.sim.genotype.copy_param()

    def paste(self):
        if self.state == "DISABLED": return
        if self.parent.copied is None: return
        self.sim.insert_new_param(self.parent.copied)

    def on_hover(self, event=None):
        if not self.selected: self.config(background=ON_HOVER_COLOR)

    def off_hover(self, event):
        if not self.selected: self.config(background=SIMS_FRAME_COLOR)

    def update_color(self):
        if self.selected:
            if self.parent.mode == "view":
                self.config(background=ON_CLICK_COLOR)
            elif (self.parent.mode == "choose_multiple") or (self.parent.mode == "choose_single"):
                self.config(background=ON_SELECT_COLOR)
            elif (self.parent.mode == "evolving"):
                self.config(background=EVOLVING_BORDER_COLOR)
        else:
            self.config(background=SIMS_FRAME_COLOR)

    def select(self):
        self.selected = True
        self.parent.selected = self
        self.update_color()

    def unselect(self):
        self.selected = False
        self.parent.selected = None
        self.update_color()

    def on_click(self, event=None):
        # This will result in not being able to deselect
        # e.g. click twice on the same item will still result in selected state
        if self.parent.mode == "evolving":
            return

        if self.parent.mode != "choose_multiple":
            self.parent.clear_all_selection()

        if self.selected:
            self.unselect()
            self.on_hover()
        else:
            self.select()

        if self.parent.mode == "view":
            self.info_frame.grid()
            self.parent.clear_info(new=self.info_frame)
            self.info_frame.update()
        else:
            self.parent.choose(self)

class SimsFrame(tk.Frame):
    """

    Attributes
    ----------
    mode : str
        Could be any of {"view", "choose_single", "choose_multiple"}
    """
    def __init__(self, parent, session, sims, info_frames, get_top_frame):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.get_top_frame = get_top_frame
        self.mode = "view"
        self.current_info = None
        self.copied = None
        self.selected = None
        self.graphs = [GraphFrame(self, session, _, __) for _,__ in zip(sims, info_frames)]
        for i, each in enumerate(self.graphs):
            each.grid(row=i/3, column=i%3, padx=5, pady=5)
        self.bind_all("<Command-c>", self.copy)
        self.bind_all("<Command-v>", self.paste)
        self.bind_all("<Command-s>", self.save)
        #self.info_frames = {_:__ for _,__ in zip(self.graphs, info_frames)}

    @property
    def top_frame(self):
        return self.get_top_frame()

    def save_all(self):
        for each in self.graphs:
            each.save()
        tkMessageBox.showinfo("", "Successfully saved!")

    def save(self, event):
        if (self.selected) and (self.mode=="view"):
            self.selected.save()
            tkMessageBox.showinfo("", "Successfully saved!")

    def copy(self, event):
        if (self.selected) and (self.mode=="view"):
            self.selected.copy()

    def paste(self, event):
        if (self.selected) and (self.mode=="view"):
            self.selected.paste()

    def choose(self, graph=None):
        if self.mode == "choose_single":
            self.top_frame.chosen(graph)
        elif self.mode == "choose_multiple":
            self.top_frame.chosen([_ for _ in self.graphs if _.selected])

    def clear_all_selection(self):
        for each in self.graphs:
            each.unselect()
    def clear_info(self, new=None):
        if self.current_info == new: return
        if self.current_info is not None:
            self.current_info.grid_remove()
        self.current_info = new

    def choose_all(self):
        self.clear_all_selection()
        for each in self.graphs:
            each.on_click()

    def to_view_mode(self):
        self.mode = "view"
        self.clear_all_selection()
        for each in self.graphs: each.bind_()

    def to_choose_mode(self, multiple=False):
        if multiple:
            self.mode = "choose_multiple"
        else:
            self.mode = "choose_single"
        self.clear_all_selection()
        self.clear_info()
        for each in self.graphs: each.unbind_()

    def highlight(self, which):
        # To highlight the parent chosen for next generation of evolution
        self.clear_all_selection()
        self.graphs[which].select()

    def to_evolving_mode(self):
        self.mode = "evolving"
        self.clear_all_selection()
        self.clear_info()
        for each in self.graphs: each.unbind_()
