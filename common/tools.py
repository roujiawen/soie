from Tkinter import *
from common.styles import *

def is_within(value, min_, max_):
    """ Inclusive.
    """
    if value > max_:
        return False
    if value < min_:
        return False
    return True

def fit_into(value, min_, max_):
    return max(min_,min(max_, value))

def create_buttons(parent, button_dict):
    """Create a group of buttons at once.

    Parameters
    ----------
    parent : Frame object
    button_dict : dictionary
        Following the format {name:[text, row, column], ...}. Command function
        name is the same as button name.
    """
    buttons = {}
    for name, attributes in button_dict.items():
        b = Button(parent, text=attributes[0], command=getattr(parent,name), padx=BUTTON_X_MARGIN)
        b.grid(row=attributes[1], column=attributes[2])
        buttons[name] = b
    return buttons
