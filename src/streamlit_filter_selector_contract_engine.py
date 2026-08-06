"""Streamlit filter selector contract engine."""
from phase2d_closure_utils import load_csv
import pandas as pd
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

def build_filter_selector():
    return load_csv("streamlit_filter_selector_config.csv", CONFIG_DIR)

if __name__ == "__main__":
    print(build_filter_selector())
