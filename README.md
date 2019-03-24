# Self-organization Interactive Evolution (SOIE)

SOIE is a GUI application written in Python and C++ for the interactive exploration of simulations of self-organizing active particles.

![Cover GIF](https://github.com/roujiawen/soie/blob/master/img/cover.gif)

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
* **Install SOIE dependencies in virtualenv.** Go into the root folder of SOIE, set up a virtual environment, and install dependencies through pip:
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
![Applying genetic operators GIF](https://github.com/roujiawen/soie/blob/master/img/genetic_operators.gif)

### Manually adjusting parameters
![Manually adjusting parameters GIF](https://github.com/roujiawen/soie/blob/master/img/edit_sim.gif)

### Importing from library and adjusting display settings
![Importing from library and adjusting display settings GIF](https://github.com/roujiawen/soie/blob/master/img/library_control.gif)

### Changing permissible parameter range
![Changing permissible parameter range GIF](https://github.com/roujiawen/soie/blob/master/img/range.gif)


## Examples
### Replicating the Vicsek model
![Vicsek GIF](https://github.com/roujiawen/soie/blob/master/img/explore_vicsek.gif)

### Replicating the Social Differential Adhesion model
![Social Differential Adhesion GIF](https://github.com/roujiawen/soie/blob/master/img/explore_social.gif)

## License
[MIT License](https://choosealicense.com/licenses/mit/)
