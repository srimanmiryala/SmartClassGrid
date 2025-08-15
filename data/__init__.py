
# data/__init__.py

"""
Data Directory

Contains JSON data files for courses, rooms, and faculty.
This file makes the data directory a Python package for easier imports.
"""

import os
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent

def load_json_file(filename):
    """Load JSON file from data directory."""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def get_data_files():
    """Get list of available data files."""
    return [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]

__all__ = ['load_json_file', 'get_data_files', 'DATA_DIR']

