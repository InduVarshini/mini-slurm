"""
Mini-SLURM: A Local HPC Scheduler for AI/ML Workloads

A lightweight, local job scheduler inspired by SLURM for managing
AI/ML workloads on a single-node local machine.
"""

__version__ = "0.1.2"

from .core import MiniSlurm, TopologyConfig
from .database import init_db, get_conn
from .utils import parse_mem, format_ts, current_user

__all__ = [
    "MiniSlurm",
    "TopologyConfig",
    "init_db",
    "get_conn",
    "parse_mem",
    "format_ts",
    "current_user",
]
