"""Browser acceptance for management and financial context alignment."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8502"
OUTPUT_DIR = "outputs/streamlit"
os.makedirs(OUTPUT_DIR, exist_ok=True)

CASES = [
    ("Emergency Department", 1, "ed_jan"),
    ("Emergency Department", 3, "ed_mar"),
    ("Emergency Department", 7, "ed_jul"),
    ("Intensive Care Unit", 1, "icu_jan"),
    ("Intensive Care Unit", 3, "icu_mar"),
    ("Intensive Care Unit", 7, "icu_jul"),
    ("Medical Ward", 1, "med_jan"),
    ("Medical Ward", 3, "med_mar"),
    ("Medical Ward", 7, "med_jul"),
    ("Admissions", 1, "adm_jan"),
    ("Admissions", 3, "adm_mar"),
    ("Admissions", 7, "adm_jul"),
    ("All Departments", 1, "all_jan"),
    ("All Departments", 3, "all_mar"),
    ("All Departments", 7, "all_jul"),
]


def select_option(page, label_text, option_text):
    """Robust Streamlit selectbox interaction via keyboard."""
    # Find the selectbox by its visible label
    selects = page.query_selector_all("[data-testid='stSelectbox']")
    target = None
    for sel in selects:
        label = sel.query_selector("label")
        if label and label_text.lower() in label.inner_text().lower():
            target = sel
            break
    if not target:
        print(f"WARNING: Could not find selectbox for {label_text}")
        return False

    # Click to focus
    target.click()
    time.sleep(0.5)

    # Type the option text to filter
    page.keyboard.press("Control+a")
    page.keyboard.press("Delete")
    page.keyboard.type(option_text)
    time.sleep(0.8)

    # Press Enter to select
    page.keyboard.press("Enter")
    time.sleep(2)
    return True


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 1200})

        print(f"Opening {BASE_URL}")
        page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        time.sleep(3)

        # Click Executive Overview in sidebar
        sidebar_links = page.query_selector_all("[data-testid='stSidebarNav'] a")
        for link in sidebar_links:
            if "Executive Overview" in link.inner_text():
                link.click()
                time.sleep(4)
                break

        for dept_label, month, case_name in CASES:
            try:
                print(f"Testing {case_name}: {dept_label} month={month}")
                # Select department
                select_option(page, "Department", dept_label)
                # Select month
                month_name = {
                    1: "January", 2: "February", 3: "March", 4: "April",
                    5: "May", 6: "June", 7: "July", 8: "August",
                    9: "September", 10: "October", 11: "November", 12: "December",
                }.get(month, str(month))
                select_option(page, "Month", month_name)
                time.sleep(4)
                screenshot_path = os.path.join(OUTPUT_DIR, f"browser_acceptance_mgmt_fin_{case_name}.png")
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"Saved {screenshot_path}")
            except Exception as e:
                print(f"ERROR for {case_name}: {e}")

        browser.close()


if __name__ == "__main__":
    run()
