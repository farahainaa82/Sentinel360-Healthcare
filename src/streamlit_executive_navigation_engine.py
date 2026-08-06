"""
streamlit_executive_navigation_engine.py
Navigation and actions engine.
"""

from typing import Dict, List

NAV_PAGES = [
    {"label": "Data Upload and Validation", "page": "01_Data_Upload_and_Validation", "exists": True},
    {"label": "Executive Overview", "page": "02_Executive_Overview", "exists": True},
    {"label": "KPI Dashboard", "page": "03_KPI_Dashboard", "exists": False},
    {"label": "Risk and Alerts", "page": "04_Risk_and_Alerts", "exists": False},
    {"label": "Recommendation Summary", "page": "05_Recommendation_Summary", "exists": False},
    {"label": "Scenario Lab", "page": "06_Scenario_Lab", "exists": False},
    {"label": "Financial Impact", "page": "07_Financial_Impact", "exists": False},
    {"label": "Integrated Decision", "page": "08_Integrated_Decision", "exists": False},
    {"label": "Management Review and Actions", "page": "09_Management_Review", "exists": False},
    {"label": "Reports and Export", "page": "10_Reports_and_Export", "exists": False},
    {"label": "Audit and Traceability", "page": "11_Audit_and_Traceability", "exists": False},
]


def get_navigation_pages() -> List[Dict]:
    return NAV_PAGES
