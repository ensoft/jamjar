#!/usr/bin/env python3

from distutils.core import setup

setup(
    name="jamjar",
    version="0.5",
    description="Jam target and dependency inspection tool",
    author="Phil Connell, Zoe Kelly, Jonathan Loh, Antony Wallace, Ensoft Ltd",
    author_email="philc@ensoft.co.uk",
    packages=["jamjar", "jamjar.parsers"],
)
