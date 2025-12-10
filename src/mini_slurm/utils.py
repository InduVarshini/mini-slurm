"""Utility functions for mini-slurm."""

import os
from datetime import datetime
from typing import Optional


def parse_mem(mem_str: str) -> int:
    """
    Convert memory strings like '8GB', '1024MB', '2g', '512m' into MB.
    """
    s = mem_str.strip().upper()
    if s.endswith("GB") or s.endswith("G"):
        value = float(s.rstrip("GB").rstrip("G"))
        return int(value * 1024)
    if s.endswith("MB") or s.endswith("M"):
        value = float(s.rstrip("MB").rstrip("M"))
        return int(value)
    # bare number => MB
    return int(float(s))


def format_ts(ts: Optional[float]) -> str:
    """Format timestamp to readable string."""
    if ts is None:
        return "-"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def current_user() -> str:
    """Get current username."""
    return os.getenv("USER") or os.getenv("USERNAME") or "unknown"
