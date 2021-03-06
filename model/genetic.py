"""This module contains the logic of the genetic algorithm.
"""

import concurrent.futures
import copy_reg
import types
from copy import deepcopy

import numpy as np

from common.parameters import GLOBAL_STATS_NAMES_INV, DEFAULT_STEPS
from model.DA import Model


def _pickle_method(method):
    """Pickle methods of classes for multi-processing.
    """
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    return _unpickle_method, (func_name, obj, cls)


def _unpickle_method(func_name, obj, cls):
    """Unpickle methods of classes for multi-processing.
    """
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    return func.__get__(obj, cls)


copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)


def ticks(group):
    """Wrapper function for .add_steps method.
    """
    pheno, steps, sim_id = group
    pheno.add_steps(steps)
    return pheno, sim_id


class Genotype(object):
    """A class that represents a genotype of a model in a population.
    """
    def __init__(self, parameters):
        self.parameters = parameters

    def copy_param(self):
        return deepcopy(self.parameters)

class Phenotype(object):
    """A class that represents a phenotype of a model in a population.

    Methods:
        add_steps: Evolve the phenotype for a given number of steps.

    Attributes:
        genotype (Genotype): The genotype associated with this phenotype.
        step (int): The number of steps that this phenotype has evolved.
        periodic_boundary (bool): Whether the phenotype is under periodic
            boundary conditions.
        model (Model): The DA.Model object associated with this phenotype.
    """
    def __init__(self, genotype, scale_factor, periodic_boundary, prev=False):
        """
        Parameters:
            scale_factor (float): The scale factor for the simulation
                associated with this phenotype.
            prev (bool): Whether this phenotype is restored from some
                previously saved state.
            genotype, periodic_boundary: See ``Attributes``.
        """
        self.genotype = genotype
        self.step = 0
        self.periodic_boundary = periodic_boundary
        self.scale_factor = scale_factor
        self.model = Model(
            genotype.copy_param(), scale_factor, periodic_boundary)
        if not prev:
            self.model.init_particles_state()

    def add_steps(self, n_steps):
        self.step += n_steps
        self.model.tick(n_steps)


class GenoGenerator(object):
    """Generator of genotypes. It specifies the randomization algorithm for
    different types of parameters.

    Methods:
        update_ranges: Update the permissible range for parameters, used when
            the user changes corresponding settings.
        randomize: Generate a completely random genotype.
        new_population: Generate a population of completely random genotypes.
        crossover: Generate a population using crossover on chosen parents.
        mutate: Generate a population through mutating a chosen parent.
    """
    @staticmethod
    def randomize_d0(limits, res=2):
        return limits[0]+round(np.random.random()*(limits[1]-limits[0]), res)

    @staticmethod
    def randomize_d1_discrete(list_of_choices):
        def randomize_d0_discrete(choices):
            if "none" in choices:
                if len(choices) == 1:
                    return "none"
                temp = [_ for _ in choices if _ != "none"]
                return np.random.choice(["none", np.random.choice(temp)],
                                        p=[0.8, 0.2])
            else:
                return np.random.choice(choices)
        return [randomize_d0_discrete(_) for _ in list_of_choices]

    @staticmethod
    def randomize_d1_ratio(limits, res=2):
        r1r2_min, r1r2_max, r3_min, r3_max = limits
        # If no restrictions, return
        if ((r1r2_min == 0.0) and (r1r2_max == float("inf")) and
                (r3_min == 0.0) and (r3_max == 1.0)):
            return np.random.dirichlet((1, 1, 1)).tolist()
        ratio3 = round(r3_min + np.random.random()*(r3_max-r3_min), res)
        rest = 1 - ratio3

        if (r1r2_min == 0.0) and (r1r2_max == float("inf")):
            ratio1 = round(np.random.random()*rest, res)
            ratio2 = round(rest - ratio1, res)
        elif r1r2_max == float("inf"):
            inv = 1/r1r2_min
            ratio2 = round(np.random.random()*(inv/(inv+1.0)) * rest, res)
            ratio1 = round(rest - ratio2, res)
        else:
            r1_max = r1r2_max/(r1r2_max+1.0)
            r1_min = r1r2_min/(r1r2_min+1.0)
            ratio1 = round(
                (r1_min + np.random.random() * (r1_max - r1_min)) * rest, res)
            ratio2 = round(rest - ratio1, res)

        return [ratio1, ratio2, ratio3]

    def randomize_d1(self, limits, res=3):
        return [self.randomize_d0(_, res) for _ in limits]

    @staticmethod
    def randomize_d1_biased(limits, res=2):
        def randomize_d0_biased(limits, res):
            return limits[0] + max(
                0, round(np.random.random() * 3. * (limits[1] - limits[0])
                         - 2.0 * (limits[1] - limits[0]), res))
        return [randomize_d0_biased(_, res) for _ in limits]

    def randomize_d2(self, limits, res=2):
        temp = [[self.randomize_d0(limits[i][j-i], res) if i <= j else -1
                 for j in xrange(3)] for i in xrange(3)]
        return [[temp[i][j] if i <= j else temp[j][i]
                 for j in xrange(3)] for i in xrange(3)]

    def __init__(self, session):
        self.session = session
        session.bind("param_info", self.update_ranges)
        self.update_ranges()

        self.param_gen = {
            "Cell Density": self.randomize_d0,
            "Noise Intensity": self.randomize_d0,
            "Angular Inertia": lambda limits: self.randomize_d0(limits, 4),
            "Interaction Force": lambda limits: self.randomize_d0(limits, 4),
            "Interaction Range": self.randomize_d0,
            "Alignment Force": lambda limits: self.randomize_d0(limits, 4),
            "Alignment Range": self.randomize_d0,

            "Pinned Cells": self.randomize_d1_discrete,
            "Cell Ratio": self.randomize_d1_ratio,
            "Velocity": self.randomize_d1,
            "Gradient Intensity": self.randomize_d1_biased,
            "Gradient Direction": lambda limits: self.randomize_d1(limits, 2),

            "Adhesion": self.randomize_d2
        }

    def update_ranges(self):
        param_info = self.session.param_info
        new_ranges = {name: info["range"] for name, info in param_info.items()}
        self.ranges = new_ranges

    def randomize(self):
        parameters = {
            name: generator(self.ranges[name])
            for name, generator in self.param_gen.items()
        }

        return Genotype(parameters)

    def new_population(self, num=9):
        children = []
        for _ in range(num):
            children.append(self.randomize())
        return children

    @staticmethod
    def choose(parents, name):
        if isinstance(parents, list):
            temp = np.random.choice(parents).parameters[name]
        else:
            temp = parents.parameters[name]
        if isinstance(temp, list):
            temp = deepcopy(temp)
        return temp

    def crossover(self, parents):
        num = 9 - len(parents)
        children = []
        for _ in range(num):
            parameters = {
                name: self.choose(parents, name)
                for name in self.param_gen
            }

            children.append(Genotype(parameters))
        return children

    def mutate(self, parent, num=8):
        not_locked = mutate_info = self.session.advanced_mutate
        rate = mutate_info["rate"]
        children = []
        for _ in range(num):
            parameters = {
                name:
                (generator(self.ranges[name])
                 if (np.random.random() < rate) and (not_locked[name])
                 else self.choose(parent, name))
                for name, generator in self.param_gen.items()
            }

            children.append(Genotype(parameters))
        return children


class Simulation(object):
    """A class that represents an agent-based simulation of self-propelled
    particles. It links the genetic algorithm, the core simulation, and the
    user interface.

    Methods:
        load_prev_session: Restore a simulation from saved session data.
        update_phenotype: Update the phenotype basing on the genotype of this
            simulation.
        insert_new_genotype: Insert a new genotype to this simulation.
        insert_new_param: Insert a new parameter-set for this simulation.
        randomize: Randomly generate a new genotype and run the simulation.
        restart: Restart this simulation using the same genotype.
        add_steps: Run this simulation for a given number of steps.

    Attributes:
        id (str): {0,1,2,..8}. Identifies this simulation on the GUI.
        genotype (Genotype): The genotype associated with this simulation.
        phenotype (Phenotype): The phenotype associated with this simulation.
    """
    def __init__(self, geno_generator, session, sim_id):
        self.id = sim_id
        self.genotype = None
        self.phenotype = None
        self.geno_generator = geno_generator
        self.session = session
        self.bindings = {"params": [], "state": [],
                         "global_stats": [], "step": []}

    def __repr__(self):
        return self.id

    @property
    def params(self):
        return self.genotype.parameters

    @property
    def state(self):
        return self.phenotype.model.state

    @property
    def step(self):
        return self.phenotype.step

    @property
    def global_stats(self):
        return self.phenotype.model.global_stats

    @property
    def n_per_species(self):
        return self.phenotype.model.internal_params["n_per_species"]

    def bind(self, data_name, func, first=False):
        """Bind functions to data; if data changes, the binded functions are
        called. the `first` flag specifies whether to prioritize the given
        function when calling a sequence of functions.

        Parameters:
            data_name (str): {"params", "state", "global_stats", "step"}
            func (function): Function to be binded to given data name
        """
        if first:
            self.bindings[data_name].insert(0, func)
        else:
            self.bindings[data_name].append(func)

    def unbind(self, data_name, func):
        """Remove a function from the list of binded functions."""
        self.bindings[data_name].remove(func)

    def call_bindings(self, data_name):
        """Call binded functions."""
        for each_func in self.bindings[data_name]:
            each_func()

    def load_prev_session(self, data):
        """Restore a simulation from previously saved session data."""
        session = self.session
        sf, pb, _ = session.pheno_settings
        self.genotype = Genotype(data["params"])
        self.phenotype = Phenotype(self.genotype, sf, pb, prev=True)
        self.phenotype.model.set(data["state"], data["global_stats"])
        self.phenotype.step = data["step"]
        # Update
        for each_data_name in data.keys():
            self.call_bindings(each_data_name)

    def update_phenotype(self):
        """Update phenotype with the new genotype and phenotype settings."""
        sf, pb, _ = self.session.pheno_settings
        self.phenotype = Phenotype(self.genotype, sf, pb)
        self.call_bindings("state")
        self.call_bindings("step")
        self.call_bindings("global_stats")

    def insert_new_genotype(self, new_genotype):
        """Insert a new genotype and update phenotype."""
        self.genotype = new_genotype
        self.call_bindings("params")
        self.update_phenotype()

    def insert_new_param(self, parameters):
        """"Insert a new set of parameters that the user provided, assuming
        the parameters fit into the range already."""
        new_genotype = Genotype(parameters)
        self.insert_new_genotype(new_genotype)
        self.add_steps(DEFAULT_STEPS)

    def randomize(self):
        """Generate a new genotype and run simulation."""
        new_genotype = self.geno_generator.randomize()
        self.insert_new_genotype(new_genotype)
        self.add_steps(DEFAULT_STEPS)

    def restart(self):
        """Restart the simulation."""
        self.update_phenotype()

    def add_steps(self, n_steps):
        """Run the simulation for a given number of steps."""
        movement = self.session.movement
        if movement is False:
            intervals = [n_steps]
        else:
            intervals = [movement] * (n_steps/movement)
            if n_steps % movement > 0:
                intervals.append(n_steps % movement)

        for step in intervals:
            self.phenotype.add_steps(step)
            self.call_bindings("state")
            self.call_bindings("step")
        self.call_bindings("global_stats")


class Population(object):
    """A class that represents a population of simulationsself.

    Methods:
        load_prev_session: Restore all simulations of this population from
            saved session data.
        update_phenotype: Update phenotypes of this population when phenotype
            settings (e.g. scale factor, boundary condition) change.
        new_population: Generate a new random population.
        mutate: Apply the mutation operator on a chosen parent.
        crossover: Apply the crossover operator on some chosen parents.
        mutate2: Apply mutation operator, but for the evolve_by_property
            function.
        evolve_by_property: Apply a genetic algorithm which uses a global
            property (as opposed to human judgement) as the fitness function.
        insert_from_lib: Insert genes to the simulation frame from the library.
        add_steps_all: Add a given number of steps to all simulations.
        add_steps_all_till: Add a number of steps to all simulations until
            they reach certain target number of steps.

    Attributes:
    """
    def __init__(self, session):
        self.geno_generator = GenoGenerator(session)
        self.session = session
        session.bind("general_settings", self.update_phenotype)
        self.sf, self.pb, self.vt = session.pheno_settings
        self.simulations = [Simulation(self.geno_generator, session, str(_))
                            for _ in range(9)]

    def load_prev_session(self, model_data):
        self.sf, self.pb, self.vt = self.session.pheno_settings
        for data, sim in zip(model_data, self.simulations):
            sim.load_prev_session(data)

    def update_phenotype(self):
        """
        {"periodic_boundary": bool,
        "scale_factor": float,
        "velocity_trace": list of float}
        """
        pb_changed = self.pb != self.session.pb
        sf_changed = self.sf != self.session.sf
        new_trace, old_trace = self.session.vt, self.vt
        trace_changed = (not (new_trace[0] == 0 and old_trace[0] == 0)) and (
            (new_trace[0] != old_trace[0]) or (new_trace[1] != old_trace[1]))
        self.sf, self.pb, self.vt = self.session.pheno_settings

        rerun_model = pb_changed or sf_changed
        if rerun_model:
            for each in self.simulations:
                each.update_phenotype()
            self.add_steps_all(DEFAULT_STEPS)
        else:
            if trace_changed:
                self.session.update("vt")

    def new_population(self):
        new_pop = self.geno_generator.new_population()

        # Put them into simulations
        for each in self.simulations:
            each.insert_new_genotype(new_pop.pop())

        self.add_steps_all(DEFAULT_STEPS)

    def mutate(self, chosen_sim):
        """Change eight simulations into the children of one chosen simulation
        through parameter mutation.
        """
        # Take one simulation; generate eight new instances of genotypes
        children = self.geno_generator.mutate(chosen_sim.genotype)
        # Put them into simulations
        for each in self.simulations:
            if each != chosen_sim:
                each.insert_new_genotype(children.pop())

        self.add_steps_all(
            DEFAULT_STEPS, sims=[each for each in self.simulations
                                 if each != chosen_sim])

    def crossover(self, chosen_sims):
        parents = [_.genotype for _ in chosen_sims]
        children = self.geno_generator.crossover(parents)

        for each in self.simulations:
            if each not in chosen_sims:
                each.insert_new_genotype(children.pop())

        self.add_steps_all(
            DEFAULT_STEPS, sims=[each for each in self.simulations
                                 if each not in chosen_sims])

    def mutate2(self, chosen_sim, target_steps):
        """Mutate function customized for evolve_by_property
        """
        sf, pb, _ = self.session.pheno_settings

        # Take one simulation; generate eight new instances of genotypes
        children = self.geno_generator.mutate(chosen_sim.genotype)

        # Put them into simulations
        for each in self.simulations:
            if each != chosen_sim:
                each.genotype = children.pop()
                each.call_bindings("params")
            # Start new Phenotype but not updating display
            each.phenotype = Phenotype(each.genotype, sf, pb)
        self.add_steps_all(target_steps)

    def evolve_by_property(self, which_prop, num_gen, equi_range,
                           display_text, highlight_func):
        start_step, end_step = equi_range
        prop_index = GLOBAL_STATS_NAMES_INV[which_prop]

        # Prepare for initial step
        self.add_steps_all_till(end_step)

        # For each generation
        for each_gen in range(num_gen):
            fitnesses = [np.abs(
                each_sim.global_stats[prop_index, start_step:end_step]).mean()
                         for each_sim in self.simulations]
            parent = self.simulations[np.argmax(fitnesses)]

            # Update display text and highlight parent
            display_text.set("Generation:{}/{}\tMax Fitness:{}".format(
                each_gen, num_gen, round(np.max(fitnesses), 4)))
            highlight_func(int(parent.id))
            self.mutate2(parent, end_step)

        # Final fitness
        fitnesses = [np.abs(
            each_sim.global_stats[prop_index, start_step:end_step]).mean()
                     for each_sim in self.simulations]
        parent = self.simulations[np.argmax(fitnesses)]

        # Update display text and highlight parent
        display_text.set("Generation:{}/{}\tMax Fitness:{}".format(
            num_gen, num_gen, round(np.max(fitnesses), 4)))
        highlight_func(int(parent.id))

    def insert_from_lib(self, param, chosen_sims):
        for each in chosen_sims:
            each.insert_new_param(param)

    def add_steps_all(self, n_steps, sims=None):
        if sims is None:
            sims = self.simulations

        movement = self.session.movement
        if movement is False:
            intervals = [n_steps]
        else:
            intervals = [movement] * (n_steps/movement)
            if n_steps % movement > 0:
                intervals.append(n_steps % movement)

        for step in intervals:
            args = [[sim.phenotype, step, i] for i, sim in enumerate(sims)]
            with concurrent.futures.ProcessPoolExecutor() as executor:
                for pheno, i in executor.map(ticks, args):
                    sims[i].phenotype = pheno
                    sims[i].call_bindings("state")
                    sims[i].call_bindings("step")

        for each in sims:
            each.call_bindings("global_stats")

    def add_steps_all_till(self, target_step):
        sims = self.simulations
        args = [[sim.phenotype, max(0, target_step - sim.step), i]
                for i, sim in enumerate(sims)]
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for pheno, i in executor.map(ticks, args):
                sims[i].phenotype = pheno
                sims[i].call_bindings("state")
                sims[i].call_bindings("step")
        for each in sims:
            each.call_bindings("global_stats")
