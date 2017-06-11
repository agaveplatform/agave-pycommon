# agave_common #

## Overview ##

Python package for building legacy django python web services for the Agave platform.

## Installation ##
Most likely you will want to add this package as a requirement in your requirements file. Add:

```
-e git+https://bitbucket.org/deardooley/agave_pycommon.git#egg=agave_pycommon
```

to a requirements.txt file to be able to import from the package "common".

Install from source: Clone the repository, change into the project directory, activate a
virtualenv if appropriate and run:

```
#!bash

$ python setup.py install
```

All dependencies will be automatically installed along with the package.
