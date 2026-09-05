"""Thin wrapper for the dataset generator so users can run
`python -m backend.scripts.generate_data`.
"""
from __future__ import annotations

from backend.data.generate import main

if __name__ == "__main__":
    main()
