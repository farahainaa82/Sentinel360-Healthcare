"""Streamlit page architecture engine."""
from phase2d_closure_utils import load_csv
import pandas as pd
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

def build_page_architecture():
    return load_csv("streamlit_page_architecture_config.csv", CONFIG_DIR)

if __name__ == "__main__":
    print(build_page_architecture())
