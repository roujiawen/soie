# Self-organization Interactive Evolution (SOIE)

SOIE is a GUI application written in Python and C++ for the interactive exploration of simulations of self-organizing active particles. The associated paper is [here](https://www.roujiawen.com/portfolio/pdfs/interactive_evolution.pdf).

<img src="https://github.com/roujiawen/soie_gifs/blob/master/cover.gif" width="600"/>

## Installation Guide

This software is written in [Python 2.7](https://www.python.org/downloads/release/python-2715/) and requires [pip](https://pip.pypa.io/en/stable/installing/) and [virtualenv](https://virtualenv.pypa.io/en/latest/installation/) to set up.


### Prerequisites
* **Check your Python version.** Type in command line:
```bash
python -V
```
* **Check that you have pip and virtualenv installed.** Type in command line:
```bash
pip --version
virtualenv --version
```

### Installing
* **Install SOIE dependencies in virtualenv.** In command line, go into the root folder of SOIE, set up a virtual environment, and install dependencies through pip:
```bash
cd [path to SOIE]
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```
where ```[path to SOIE]``` is the location of the downloaded SOIE code, for example, ```~/Downloads/soie-master```.

## Usage
If you have followed the installation guide, you are already inside a virtual environment. If that is the case,

* **Launch the application directly by typing in command line:**
```bash
python -m app
```
Otherwise, 

* **Activate the virtual environment first, and then launch the application:**
```bash
source venv/bin/activate
python -m app
```

## Tutorial

### Applying genetic operators
<img src="https://github.com/roujiawen/soie_gifs/blob/master/genetic_operators.gif" width="600"/>

### Manually adjusting parameters
<img src="https://github.com/roujiawen/soie_gifs/blob/master/edit_sim.gif" width="600"/>

### Importing from library and adjusting display settings
<img src="https://github.com/roujiawen/soie_gifs/blob/master/library_control.gif" width="600"/>

### Changing permissible parameter range
<img src="https://github.com/roujiawen/soie_gifs/blob/master/range.gif" width="600"/>

## Examples
### Replicating the Vicsek model
<img src="https://github.com/roujiawen/soie_gifs/blob/master/explore_vicsek.gif" width="600"/>

### Replicating the Social Differential Adhesion model
<img src="https://github.com/roujiawen/soie_gifs/blob/master/explore_social.gif" width="600"/>

## License
[MIT License](https://choosealicense.com/licenses/mit/)
