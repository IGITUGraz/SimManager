"""
This file installs the ltl package.
Note that it does not perform any installation of the documentation. For this, follow the specified procedure in the
 README
"""

from setuptools import setup
from simplesimman import __version__

setup(
    name="SimpleSimManager",
    version=__version__,
    packages=['simplesimman'],
    author="Anand Subramoney, Arjun Rao",
    author_email="anand@igi.tugraz.at, arjun@igi.tugraz.at",
    description="This module provides the interface for some quick code to record results "
                "and make code reproducible. It is dependent on the availability of the "
                "git executable on the system.",
    provides=['simplesimman'],
)
