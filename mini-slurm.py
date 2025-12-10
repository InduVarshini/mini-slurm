#!/usr/bin/env python3
"""
Backward compatibility wrapper for mini-slurm CLI.

This file is kept for backward compatibility. New installations should use
the 'mini-slurm' command directly after installing the package.

To install: pip install -e .
To use: mini-slurm <command> [args...]
"""

import sys
import warnings

warnings.warn(
    "Using mini-slurm.py directly is deprecated. "
    "Please install the package and use 'mini-slurm' command instead: "
    "pip install -e . && mini-slurm <command>",
    DeprecationWarning,
    stacklevel=2
)

# Import and run the CLI from the package
from mini_slurm.cli import main

if __name__ == "__main__":
    main()
