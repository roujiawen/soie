"""This modeule contains useful functions that are shared across different
UI components.
"""

import Tkinter as tk

from common.styles import BUTTON_X_MARGIN


def is_within(value, min_, max_):
    """ Return True if value is within [min_, max_], inclusive.
    """
    if value > max_:
        return False
    if value < min_:
        return False
    return True


def fit_into(value, min_, max_):
    """ Return value bounded by min_ and max_.
    """
    return max(min_, min(max_, value))


def create_buttons(parent, button_dict):
    """Create a group of buttons at once.

    Parameters:
        parent (tk.Frame): The parent on which the button widget is anchored.
        button_dict (dict): Specifies button display name and position. Given
            in the format {name:[text, row, column], ...}. Command function
            name should be the same as button name.

    Returns:
        buttons (dict): A group of button widgets created. Format is
            {name: button_widget, ...}
    """
    buttons = {}
    for name, attributes in button_dict.items():
        # Associate the button with a command function
        button = tk.Button(parent, text=attributes[0],
                           command=getattr(parent, name), padx=BUTTON_X_MARGIN)
        button.grid(row=attributes[1], column=attributes[2])
        buttons[name] = button
    return buttons


def counts2slices(counts):
    """Convert a list of counts to cummulative slices.
    Example: [5, 1, 3] ==> [slice(0, 5), slice(5, 6), slice(6, 9)]
    """
    cumu = [sum(counts[:i]) for i in range(len(counts)+1)]
    slices = [slice(cumu[i-1], cumu[i]) for i in range(1, len(cumu))]
    return slices
