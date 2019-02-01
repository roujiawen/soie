from Tkinter import *
import ttk
import os
import json
from random import choice
from common.parameters import PARAM



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
        b = Button(parent, text=attributes[0], command=getattr(parent,name))
        b.grid(row=attributes[1], column=attributes[2])
        buttons[name] = b
    return buttons

def recursive_freeze(frame):
    for each in frame.widgets:
        if isinstance(each, Frame):
            recursive_freeze(each)
        else:
            each.config(state=DISABLED)

def recursive_unfreeze(frame):
    for each in frame.widgets:
        if isinstance(each, Frame):
            recursive_unfreeze(each)
        else:
            each.config(state=NORMAL)

def read_json(filename):
    import json
    with open(filename) as f:
        json_data = f.readlines()
        d = json.loads(json_data)
    return d

def flatten(params):
    pinned_code = {"none":0, "random":1, "square":2, "circle":3, "ring":4}
    flattened = [params[name] for name in PARAM["main"]]
    for name in PARAM["cell"]:
        if name == "Pinned Cells":
            flattened += [pinned_code[_] for _ in params[name]]
        else:
            flattened += params[name]
    adh = PARAM["Adhesion"]
    flattened += [adh[i][j] for i in range(3) for j in range(3)]
    return flattened

def hash_list(l):
    """ Given a list of floats, return a 8-digit base-36 string hash.
    """
    def tobaseN(n,N,D="0123456789abcdefghijklmnopqrstuvwxyz"):
        return (tobaseN(n//N,N)+D[n%N]).lstrip("0") if n>0 else "0"
    x = 0
    a1, b1, p1 = 102345, 567, 104729
    a, b = 7654321, 1234567
    p = 29996224275833
    m = 2821109907456
    for each in l:
        x *=1000
        x += (int(each*a1+b1) % p1) % 1000
    x = ((x*a+b) % p) % m
    return tobaseN(x, 36).zfill(8)

def random_string(n, allchar="0123456789abcdefghijklmnopqrstuvwxyz"):
    return "".join(choice(allchar) for _ in xrange(n))

def load_params(path):
    # Load params.json file
    try:
        with open(path,"r") as f:
            data = json.load(f)
    except:
        data = {"items":{}, "loc":{}}
    return data

LIB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),'libdata')
JSON_PATH = os.path.join(LIB_PATH, "params.json")

def delete_all_genes():
    data = load_params(JSON_PATH)
    for gene_id in data["items"]:
        FIG_PATH = os.path.join(LIB_PATH, "{}.png".format(gene_id))
        os.remove(FIG_PATH)
    os.remove(JSON_PATH)


def delete_gene(gene_id):
    data = load_params(JSON_PATH)

    # Move up locations
    flag = False
    for i in xrange(len(data["items"])):
        if flag:
            data["loc"][str(i-1)] = data["loc"][str(i)]
        else:
            if data["loc"][str(i)] == gene_id:
                flag = True
    data["loc"].pop(str(i))

    # Delete from items
    data["items"].pop(gene_id)

    # Save json file
    with open(JSON_PATH, 'w') as f:
         json.dump(data, f, indent=4, separators=(',', ': '))

    # Delete figure
    FIG_PATH = os.path.join(LIB_PATH, "{}.png".format(gene_id))
    os.remove(FIG_PATH)


def save_gene(params, fig):
    data = load_params(JSON_PATH)

    # Add and save json file
    gene_id = random_string(8)
    while gene_id in data["items"]:
        gene_id = random_string(8)

    data["loc"][str(len(data["items"]))] = gene_id
    data["items"][gene_id] = params
    with open(JSON_PATH, 'w') as f:
         json.dump(data, f, indent=4, separators=(',', ': '))

    # Save figure
    FIG_PATH = os.path.join(LIB_PATH, "{}.png".format(gene_id))
    fig.savefig(FIG_PATH,
        edgecolor='w',facecolor='w', dpi=48)
