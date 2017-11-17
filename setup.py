"""
This file installs the ltl package.
Note that it does not perform any installation of the documentation. For this, follow the specified procedure in the
 README
"""

from setuptools import setup, find_packages
from simmanager import __version__

setup(
    name="SimManager",
    version=__version__,
    packages=find_packages('/simmanager'),
    scripts=['scripts/subpatch.sh'],
    author="Anand Subramoney, Arjun Rao",
    author_email="anand@igi.tugraz.at, arjun@igi.tugraz.at",
    description="This module provides the interface for some quick code to record results and make"
                " code reproducible. It also contains some handy tools that are used often like"
                " timers and stdout redirection. It is dependent on the availability of the git"
                " executable on the system path",
    provides=['simmanager'],
)
