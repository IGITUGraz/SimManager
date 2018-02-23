"""
This file installs the SimManager package.
"""

from setuptools import setup, find_packages
from simmanager import __version__

setup(
    name="SimManager",
    version=__version__,
    packages=find_packages(),
    scripts=['scripts/subpatch.sh'],
    author="Arjun Rao, Anand Subramoney",
    author_email="arjun@igi.tugraz.at, anand@igi.tugraz.at",
    description="This module provides the interface for some quick code to record results and make"
                " code reproducible. It also contains some handy tools that are used often like"
                " timers and stdout redirection. It is dependent on the availability of the git"
                " executable on the system path",
    provides=['simmanager'],
)
