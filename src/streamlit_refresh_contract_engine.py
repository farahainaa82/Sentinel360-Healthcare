"""Streamlit refresh contract engine."""
from phase2d_closure_utils import load_csv
import pandas as pd
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

def build_refresh_contract():
    return load_csv("streamlit_refresh_contract_config.csv", CONFIG_DIR)

if __name__ == "__main__":
    print(build_refresh_contract())
