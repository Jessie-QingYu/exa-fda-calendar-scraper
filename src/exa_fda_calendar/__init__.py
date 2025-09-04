"""
exa_fda_calendar package

Provides:
- run_pipeline: main function to run the scraping + fallback pipeline
- main: CLI entrypoint (argument parser)
"""

from .pipeline import run_pipeline
from .cli import main

__all__ = ["run_pipeline", "main"]
