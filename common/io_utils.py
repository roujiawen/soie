"""This module contains input/output functions.

There are two types of data being handled: session data and gene library data.

Session data:
    A dict containing the following attributes from the SessionData object:
        * general_settings
        * param_info
        * advanced_mutate
        * global_stats_display
        * evolve_property_settings
    and
        * model_data: a list of dictionaries each describing the current state
            of one of the nine Simulation objects, with the following format
                {"params": sim.params,
                 "state": sim.state,
                 "global_stats": sim.global_stats,
                 "step": sim.step}

    The functions ``save_session_data`` and ``load_session_data`` save and load
    session data respectively for a given file path.


Gene library data:
    Under LIB_PATH, there is a json file storing the parameters of all saved
    simulations (called genes), their identifier string, and display locations
    in the library window. In addition, thumbnail images for each simulation
    are stored in separate png files under the same directory.

    The json file has format:
    {
        "items": {
            "hn90y8ws": some params...,
            "h0suw44x": some params...
            ...
        },
        "loc": {
            "0": "h0suw44x",
            "3": "hn90y8ws",
            ...
        }
    }

    The function ``random_string`` generates identifiers for genes to be
    stored. ``load_params`` loads the json file from LIB_PARAMS_JSON_PATH.
    ``delete_gene`` removes the information associated with a given gene (its
    png file and related entries in the json file). ``delete_all_genes``
    deletes everything. ``save_gene`` saves a gene to files given its
    parameters and figure.

"""
import json
import os
from random import choice

import numpy as np

from parameters import PARAM_INFO

LIB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'libdata')
LIB_PARAMS_JSON_PATH = os.path.join(LIB_PATH, "params.json")

def fit_into(x, a, b):
    return max(min(x, b), a)

def gene2params(gene):
    """Convert from gene format (for one cell type) to params format (for
    three cell types)."""
    adh = np.exp(np.tan(fit_into(gene["Adhesion"], -0.99, 0.99)*np.pi/2))
    params = {
        "Alignment Range": gene["Alignment Range"],
        "Pinned Cells": ["none"] * 3,
        "Interaction Force": gene["Interaction Force"],
        "Gradient Intensity": [gene["Gradient Intensity"],
            0.0,
            0.0
        ],
        "Cell Ratio": [1.0, 0.0, 0.0],
        "Alignment Force": gene["Alignment Force"],
        "Noise Intensity": gene["Noise Intensity"],
        "Angular Inertia": gene["Angular Inertia"],
        "Adhesion": [
            [round(adh, PARAM_INFO["Adhesion"]["roundto"]), 0., 0.],
            [0., 0., 0.],
            [0., 0., 0.]
        ],
        "Gradient Direction": [gene["Gradient Direction"], 0.0, 0.0],
        "Cell Density": gene["Cell Density"],
        "Velocity": [gene["Velocity"], 0., 0.],
        "Interaction Range": gene["Interaction Range"]
    }
    # Rounding
    for each in params:
        if isinstance(params[each], list):
            if isinstance(params[each][0], int) or isinstance(params[each][0], float):
                params[each][0] = round(params[each][0], PARAM_INFO[each]["roundto"])
        elif isinstance(params[each], int) or isinstance(params[each], float):
            params[each] = round(params[each], PARAM_INFO[each]["roundto"])

    return params

def load_from_files(input_file_name):
    """ Load JSON and return params dictoinary."""
    with open(input_file_name, "r") as infile:
        temp = json.load(infile)
        if "gene" in temp:
            gene = temp["gene"]
        elif "Gradient Intensity" in temp:
            gene = temp
        else:
            raise IOError("Failed to open gene. This file does not have the correct format.")
    return gene2params(gene)


def save_session_data(output_file_name, session_data):
    """Save session data to a json file."""
    with open(output_file_name, 'w') as outfile:
        json.dump(session_data, outfile)


def load_session_data(input_file_name):
    """Load and return session data from a json file."""
    with open(input_file_name, "r") as infile:
        session_data = json.load(infile)
    return session_data


def random_string(length, allchar="0123456789abcdefghijklmnopqrstuvwxyz"):
    """Generate a random string to be used as identifier for saved genes."""
    return "".join(choice(allchar) for _ in range(length))


def load_params(path):
    """Load and return gene library data from a json file. If the path does not
    exist (library being empty), create a new empty dictionary."""
    try:
        with open(path, "r") as infile:
            data = json.load(infile)
    except (IOError, ValueError):
        # If file fails to load, create new dictionary
        data = {"items": {}, "loc": {}}
    return data


def delete_all_genes():
    """Remove all library data by deleting all png files and the json file."""
    try:
        with open(LIB_PARAMS_JSON_PATH, "r") as infile:
            data = json.load(infile)
    except (IOError, ValueError):
        return
    for gene_id in data["items"]:
        figure_path = os.path.join(LIB_PATH, "{}.png".format(gene_id))
        os.remove(figure_path)
    os.remove(LIB_PARAMS_JSON_PATH)


def delete_gene(gene_id):
    """Delete the png file associated a specific gene, and remove its entry
    from the json file."""
    try:
        with open(LIB_PARAMS_JSON_PATH, "r") as infile:
            data = json.load(infile)
    except (IOError, ValueError):
        return
    # Move up locations following the deleted spot
    flag = False
    for i in range(len(data["items"])):
        if flag:
            data["loc"][str(i-1)] = data["loc"][str(i)]
        else:
            if data["loc"][str(i)] == gene_id:
                flag = True
    # Delete the last spot
    data["loc"].pop(str(len(data["items"])-1))

    # Delete from items
    data["items"].pop(gene_id)

    # Save json file
    with open(LIB_PARAMS_JSON_PATH, 'w') as outfile:
        json.dump(data, outfile, indent=4, separators=(',', ': '))

    # Delete figure
    figure_path = os.path.join(LIB_PATH, "{}.png".format(gene_id))
    os.remove(figure_path)


def save_gene(params, fig):
    """Write a gene's information to files: save a thumbnail figure to png and
    add an entry to the json parameters file."""
    data = load_params(LIB_PARAMS_JSON_PATH)

    # Generate new identifier, make sure it doesn't clash with ones that exist
    gene_id = random_string(8)
    while gene_id in data["items"]:
        gene_id = random_string(8)

    # Add entry and save json file
    data["loc"][str(len(data["items"]))] = gene_id
    data["items"][gene_id] = params
    with open(LIB_PARAMS_JSON_PATH, 'w') as outfile:
        json.dump(data, outfile, indent=4, separators=(',', ': '))

    # Save figure
    figure_path = os.path.join(LIB_PATH, "{}.png".format(gene_id))
    fig.savefig(figure_path, edgecolor='w', facecolor='w', dpi=48)
