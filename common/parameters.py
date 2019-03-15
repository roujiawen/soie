""" Default parameters, settings and other constants shared among different
components of the software.

PARAM: the names of parameters sorted in categories.

PARAM_INFO: specifying properties of different types of parameters.

    * max, min: the absolute theoretical limit of the parameter.
    * range: the default range of the parameter.
    * roundto: how many digits to keep in parameter viewers/editors.
    * resolution: the resolution in parameter sliders.

    Note that the difference between ``max``/``min`` and ``range`` is that
    ``max``/``min`` is the limit exceeding which the model no longer makes
    sense physically, whereas ``range`` specifies the practically useful range
    to evolve parameters within. ``range`` can be modified in the GUI whereas
    ``max``/``min`` cannot.

GENERAL_SETTINGS: the default values for general settings.

GLOBAL_STATS_DISPLAY: the default values for global_stats_display, specifying
which global properties to display in the plots.

GLOBAL_STATS_NAMES: a list of the names of the global properties.

GLOBAL_STATS_NAMES_INV: the dictionary inverse to GLOBAL_STATS_NAMES, that is,
mapping names to indices.

EVOLVE_PROPERTY_SETTINGS: the default values for evolve_property_settings.

ADVANCED_MUTATE: the default values for the settings of advanced_mutate.

"""

# TODO: add comments
CORE_RADIUS = 0.1
FIELD_SIZE = 10.0
N_GLOBAL_STATS = 6

PARAM = {
    "main": [
        "Cell Density",
        "Angular Inertia",
        "Interaction Force",
        "Interaction Range",
        "Alignment Force",
        "Alignment Range",
        "Noise Intensity"
        ],
    "cell": [
        "Cell Ratio",
        "Pinned Cells",
        "Velocity",
        "Gradient Intensity",
        "Gradient Direction"
        ],
    "interaction": ["Adhesion"]
}

PARAM_INFO = {
    "Cell Density":
    {
        "range": [0.01, 1.00],
        "min": 0.01,
        "max": 1.0,
        "resolution": 0.01,
        "roundto": 2
    },

    "Interaction Range":
    {
        "range": [2.01, 20.0],
        "min": 2.0,
        "max": 50.0,
        "resolution": 0.01,
        "roundto": 2
    },

    "Alignment Range":
    {
        "range": [2.01, 20.0],
        "min": 2.0,
        "max": 50.0,
        "resolution": 0.01,
        "roundto": 2
    },

    "Angular Inertia":
    {
        "range": [0.0, 5.0],
        "resolution": 0.0001,
        "roundto": 4
    },

    "Interaction Force":
    {
        "range": [0.0, 5.0],
        "resolution": 0.0001,
        "roundto": 4
    },

    "Alignment Force":
    {
        "range": [0.0, 5.0],
        "resolution": 0.0001,
        "roundto": 4
    },

    "Noise Intensity":
    {
        "range": [0.0, 0.5],
        "min": 0.0,
        "max": 1.0,
        "resolution": 0.001,
        "roundto": 3
    },

    "Cell Ratio":
    {
        "type": "ratio",
        "range": [0.0, float('inf'), 0.0, 0.0],
        "roundto": 2
    },

    "Velocity":
    {
        "range": [[0.005, 0.2], [0.005, 0.2], [0.005, 0.2]],
        "resolution": 0.001,
        "roundto": 3,
        "min": 0.0
    },

    "Gradient Intensity":
    {
        "range": [[0.0, 2.0], [0.0, 2.0], [0.0, 2.0]],
        "min": 0.0,
        "resolution": 0.01,
        "roundto": 2
    },

    "Gradient Direction":
    {
        "range": [[0.0, 2.0], [0.0, 2.0], [0.0, 2.0]],
        "min": 0.0,
        "max": 2.0,
        "resolution": 0.01,
        "roundto": 2
    },

    "Pinned Cells":
    {
        "type": "qualitative",
        "range": [["none"], ["none"], ["none"]],
        "all_choices": ["none", "random", "square", "circle", "ring"]
    },

    "Adhesion":
    {
        "range": [[[0.01, 5.], [0.01, 5.], [0.01, 5.]],
                  [[0.01, 5.], [0.01, 5.]], [[0.01, 5.]]],
        "type": "interaction",
        "min": 0.0,
        "resolution": 0.001,
        "roundto": 3
    }
}

GENERAL_SETTINGS = {
    "show_tail": 0,
    "show_tail_value": [5.0, 0.5],
    "show_movement": 0,
    "show_movement_value": 5,
    "zoom_in": 0,
    "zoom_in_value": 2.0,
    "periodic_boundary": 0,
}

GLOBAL_STATS_DISPLAY = {
    "show": [1, 1, 1, 1, 1, 1]
}

GLOBAL_STATS_NAMES = [
    "Group Angular Momentum", "Alignment",
    "Segregation (Blue)", "Segregation (Red)", "Segregation (Green)",
    "Clustering"]

GLOBAL_STATS_NAMES_INV = {name: i for i, name in enumerate(GLOBAL_STATS_NAMES)}

EVOLVE_PROPERTY_SETTINGS = {
    "which_prop": "Group Angular Momentum",
    "num_gen": 10,
    "equi_range": (100, 200)
}

ADVANCED_MUTATE = {_: 1 for _ in PARAM_INFO}
ADVANCED_MUTATE["rate"] = 0.2
