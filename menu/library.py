import json
import os
import Tkinter as tk

from PIL import Image, ImageTk

from common.io_utils import delete_gene, load_params
from common.styles import ON_HOVER_COLOR, ON_SELECT_COLOR

NCOL = 5
IMAGE_WIDTH = 108
HALF_WIDTH = IMAGE_WIDTH/2
SPACE = 10

class SavedGene(object):
    def __init__(self, parent, gene_id, data, image, x, y):

        self.parent = parent
        self.data = data
        self.gene_id = gene_id
        self.canvas = parent.canvas
        coords = self.get_border_coords(x,y)

        self.clicked = False

        self.hover_border = self.canvas.create_rectangle(
            *coords,
            width=0, outline=ON_HOVER_COLOR)

        self.click_border = self.canvas.create_rectangle(
            *coords,
            width=0, outline=ON_SELECT_COLOR)
        self.image = self.canvas.create_image(x, y, image=image)
        self.img = image

        self.canvas.tag_bind(self.image, "<Enter>", self.on_hover)
        self.canvas.tag_bind(self.image, "<Leave>", self.off_hover)
        self.canvas.tag_bind(self.image, "<ButtonRelease - 1>", self.on_click)

    def get_border_coords(self, x, y):
        return [x-HALF_WIDTH+0.5,y-HALF_WIDTH+0.5,x+HALF_WIDTH,y+HALF_WIDTH]

    def show_border(self, border):
        self.canvas.itemconfigure(border, width=4)

    def hide_border(self, border):
        self.canvas.itemconfigure(border, width=0)

    def on_hover(self, event):
        self.show_border(self.hover_border)

    def off_hover(self, event):
        #if not self.clicked:
        self.hide_border(self.hover_border)

    def on_click(self, event):
        if self.parent.selected == self:
            return
        else:
            self.show_border(self.click_border)
            #self.clicked = True
            self.parent.select_new(self)

    def unclick(self):
        self.hide_border(self.click_border)

    def delete(self):
        for each in [self.image, self.click_border, self.hover_border]:
            self.canvas.delete(each)

    def move(self, new_x, new_y):
        self.canvas.coords(self.image, new_x, new_y)
        coords = self.get_border_coords(new_x, new_y)
        self.canvas.coords(self.hover_border, *coords)
        self.canvas.coords(self.click_border, *coords)

class CanvasGrid(object):
    def __init__(self, parent, images):
        self.parent = parent
        self.coords = []
        self.saved_genes = []
        self.height = 0
        for each in images: self.add(each)

    def move_up(self, gene):
        starting = self.saved_genes.index(gene)
        self.saved_genes.remove(gene)
        for i, each in enumerate(self.saved_genes[starting:]):
            each.move(*self.coords[starting+i])

        if len(self.saved_genes) <= len(self.coords) - NCOL:
            self.coords = self.coords[:-NCOL]
            self.height -= SPACE+IMAGE_WIDTH
            self.parent.set_scroll_length(self.height)

    def add(self, id_image):
        gene_id, data, image = id_image
        i = len(self.saved_genes)
        if i >= len(self.coords):
            self.expand()
        coords = self.coords[i]
        self.saved_genes.append(SavedGene(self.parent, gene_id, data, image, *coords))

    def expand(self):
        new_row = []
        new_y = self.height + (SPACE+IMAGE_WIDTH)/2.
        self.height += SPACE+IMAGE_WIDTH
        new_row = [[(c+0.5)*(SPACE+IMAGE_WIDTH),new_y] for c in range(NCOL)]
        self.coords += new_row
        self.parent.set_scroll_length(self.height)

CANVAS_WIDTH = NCOL*(IMAGE_WIDTH+SPACE)
CANVAS_HEIGHT = 3 * (IMAGE_WIDTH+SPACE)
class LibraryWindow(tk.Frame):
    def __init__(self, parent, master, func):
        tk.Frame.__init__(self, master)
        self.master = master
        self.parent = parent
        self.func = func
        master.wm_title("Gene Library")
        master.protocol('WM_DELETE_WINDOW', self._close)

        self.selected = None
        total_columns = 2

        # Top Row Buttons
        trash_icon =ImageTk.PhotoImage(Image.open("menu/trash.png"))
        self.image = trash_icon
        self.delete_button = tk.Button(self, image=trash_icon, bd=0, padx=0, pady=0, width=22, command=self.delete, state=tk.DISABLED)
        self.delete_button.grid(row=0, columnspan=total_columns, sticky="e", padx=15,pady=(5,5))

        self.canvas=tk.Canvas(self,bg='#FFFFFF',width=CANVAS_WIDTH,height=CANVAS_HEIGHT,
            scrollregion=(0,0,CANVAS_WIDTH,CANVAS_HEIGHT))
        self.canvas.grid(row=1, column=0)

        self.scroll = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scroll.grid(row=1, column=1, sticky="ns")

        self.canvas.config(yscrollcommand=self.scroll.set)

        def on_vertical(event):
            self.canvas.yview_scroll(-1 * event.delta, 'units')
        self.canvas.bind('<MouseWheel>', on_vertical)

        # Bottom Row Buttons
        self.open_button = tk.Button(self, text="Open", width=7, command=self.open, state=tk.DISABLED)
        self.open_button.grid(columnspan=total_columns, sticky="e", padx=15, pady=(10,0))

        self.load()

    def set_scroll_length(self, value):
        value = max(CANVAS_HEIGHT, value)
        self.canvas.config(scrollregion=(0, 0, CANVAS_WIDTH, value))

    def activate_options(self):
        self.delete_button.config(state=tk.NORMAL)
        self.open_button.config(state=tk.NORMAL)

    def disable_options(self):
        self.delete_button.config(state=tk.DISABLED)
        self.open_button.config(state=tk.DISABLED)

    def select_new(self, new):
        if self.selected is not None:
            self.selected.unclick()
        self.selected = new
        self.activate_options()


    def load(self):
        curr_dir = os.path.dirname(os.path.dirname(__file__))
        folder_name = "libdata"
        target_dir = os.path.join(curr_dir, "{}/params.json".format(folder_name))

        data = load_params(target_dir)
        images = []
        for i in range(len(data["items"])):#data
            gene_id = data["loc"][str(i)]
            images.append((gene_id, data["items"][gene_id], ImageTk.PhotoImage(Image.open("{}/{}.png".format(folder_name,gene_id)))))

        self.canvas_grid = CanvasGrid(self, images)

    def _close(self):
        self.master.destroy()

    def open(self):
        self.func(self.selected.data)
        self.master.destroy()

    def delete(self):
        if self.selected is not None:
            self.selected.delete()
            self.canvas_grid.move_up(self.selected)
            delete_gene(self.selected.gene_id)
            self.selected = None
            self.disable_options()




if __name__ == "__main__":
    root = Tk()

    app = LibraryWindow(None, root)
    app.pack()
    root.mainloop()
