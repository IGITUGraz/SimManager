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
    description="The Simulation Manager is a library for enabling reproducible scientific simulations.",
    provides=['simmanager'],
)
