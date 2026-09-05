"""Thin wrapper: `python -m backend.scripts.train_model`."""
from __future__ import annotations

from backend.app.ml.train import main

if __name__ == "__main__":
    main()
