import os
import json
from random import choice
import numpy as np

LIB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),'libdata')
LIB_PARAMS_JSON_PATH = os.path.join(LIB_PATH, "params.json")
RECORD_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),'sessions')

def save_session_data(output_file_name, session_data):
    with open(output_file_name, 'w') as f:
        json.dump(session_data, f)

def load_session_data(input_file_name):
    with open(input_file_name, "r") as f:
        session_data = json.load(f)
    return session_data

def random_string(n, allchar="0123456789abcdefghijklmnopqrstuvwxyz"):
    return "".join(choice(allchar) for _ in range(n))

def load_params(path):
    # Load params.json file
    try:
        with open(path,"r") as f:
            data = json.load(f)
    except:
        data = {"items":{}, "loc":{}}
    return data

def delete_all_genes():
    data = load_params(LIB_PARAMS_JSON_PATH)
    for gene_id in data["items"]:
        FIG_PATH = os.path.join(LIB_PATH, "{}.png".format(gene_id))
        os.remove(FIG_PATH)
    os.remove(LIB_PARAMS_JSON_PATH)

def delete_gene(gene_id):
    data = load_params(LIB_PARAMS_JSON_PATH)

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
    with open(LIB_PARAMS_JSON_PATH, 'w') as f:
         json.dump(data, f, indent=4, separators=(',', ': '))

    # Delete figure
    FIG_PATH = os.path.join(LIB_PATH, "{}.png".format(gene_id))
    os.remove(FIG_PATH)

def save_gene(params, fig):
    data = load_params(LIB_PARAMS_JSON_PATH)

    # Add and save json file
    gene_id = random_string(8)
    while gene_id in data["items"]:
        gene_id = random_string(8)

    data["loc"][str(len(data["items"]))] = gene_id
    data["items"][gene_id] = params
    with open(LIB_PARAMS_JSON_PATH, 'w') as f:
         json.dump(data, f, indent=4, separators=(',', ': '))

    # Save figure
    FIG_PATH = os.path.join(LIB_PATH, "{}.png".format(gene_id))
    fig.savefig(FIG_PATH,
        edgecolor='w',facecolor='w', dpi=48)
