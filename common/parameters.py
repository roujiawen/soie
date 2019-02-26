main_param = [
    "Cell Density",
    "Angular Inertia",
    "Interaction Force",
    "Interaction Range",
    "Alignment Force",
    "Alignment Range",
    "Noise Intensity"
]
cell_param = [
    "Cell Ratio",
    "Pinned Cells",
    "Velocity",
    "Gradient Intensity",
    "Gradient Direction"
]
interaction_param = ["Adhesion"]

PARAM= {
    "main":main_param,
    "cell":cell_param,
    "interaction":interaction_param
}

PARAM_INFO = {
    "Cell Density" :
    {
        "range" : [0.01,1.0],
        "min" : 0.01,
        "max" : 1.0,
        "resolution" : 0.01,
        "roundto" : 2
    },

    "Interaction Range" :
    {
        "range" : [2.01, 20.0],
        "min" : 2.0,
        "max" : 50.0,
        "resolution" : 0.01,
        "roundto" : 2
    },

    "Alignment Range" :
    {
        "range" : [2.01, 20.0],
        "min" : 2.0,
        "max" : 50.0,
        "resolution" : 0.01,
        "roundto" : 2
    },

    "Angular Inertia" :
    {
        "range" : [0.0, 5.0],
        "resolution" : 0.0001,
        "roundto" : 4
    },

    "Interaction Force" :
    {
        "range" : [0.0, 5.0],
        "resolution" : 0.0001,
        "roundto" : 4
    },

    "Alignment Force" :
    {
        "range" : [0.0, 5.0],
        "resolution" : 0.0001,
        "roundto" : 4
    },

    "Noise Intensity" :
    {
        "range" : [0.0, 0.5],
        "min" : 0.0,
        "max" : 1.0,
        "resolution" : 0.001,
        "roundto" : 3
    },

    "Cell Ratio" :
    {
        "type" : "ratio",
        "range" : [0.0, float('inf'), 0.0, 0.0],
        "roundto" : 2
    },

    "Velocity" :
    {
        "range" : [[0.005, 0.2],[0.005, 0.2],[0.005, 0.2]],
        "resolution" : 0.001,
        "roundto" : 3,
        "min" : 0.0
    },

    "Gradient Intensity" :
    {
        "range" : [[0.0, 2.0],[0.0, 2.0],[0.0, 2.0]],
        "min" : 0.0,
        "resolution" : 0.01,
        "roundto" : 2
    },

    "Gradient Direction" :
    {
        "range" : [[0.0, 2.0],[0.0, 2.0],[0.0, 2.0]],
        "min" : 0.0,
        "max" : 2.0,
        "resolution" : 0.01,
        "roundto" : 2
    },

    "Pinned Cells" :
    {
        "type" : "qualitative",
        "range" : [["none"],["none"],["none"]],
        "all_choices" : ["none", "random", "square", "circle", "ring"]
    },

    "Adhesion" :
    {
        "range" : [[[0.01, 5.],[0.01, 5.],[0.01, 5.]], [[0.01, 5.],[0.01, 5.]], [[0.01, 5.]]],
        "type" : "interaction",
        "min" : 0.0,
        "resolution" : 0.001,
        "roundto" : 3
    }
}

GENERAL_SETTINGS = {
    "show_tail" : 0,
    "show_tail_value" : [5.0, 0.5],
    "show_movement" : 0,
    "show_movement_value" : 5,
    "zoom_in" : 0,
    "zoom_in_value" : 2.0,
    "periodic_boundary" : 0,
}

GLOBAL_STATS_DISPLAY = {
    "show" : [1, 1, 1, 1, 1, 1]
}

GLOBAL_STATS_NAMES = ["Group Angular Momentum", "Alignment",
    "Segregation (Blue)", "Segregation (Red)", "Segregation (Green)",
    "Clustering"]

GLOBAL_STATS_NAMES_INV = {name:i for i, name in enumerate(GLOBAL_STATS_NAMES)}

EVOLVE_PROPERTY_SETTINGS = {
    "which_prop" : "Group Angular Momentum",
    "num_gen" : 10,
    "equi_range": (100, 200)
}

ADVANCED_MUTATE = {_:1 for _ in PARAM_INFO}
ADVANCED_MUTATE["rate"] = 0.2
