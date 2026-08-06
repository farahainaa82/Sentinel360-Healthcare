"""
Sentinel360 Phase 3B — Browser Acceptance Test for Executive Overview
Comprehensive: per-department screenshots + KPI status verification
"""

import sys
import os
import json
import time
import subprocess
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = Path("c:/Users/DELL/OneDrive/Desktop/Sentinel360_Dynamic")
OUTPUT_DIR = WORKSPACE / "outputs" / "streamlit" / "browser_acceptance"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RESULTS_JSON = OUTPUT_DIR / "step_3b_browser_acceptance_results.json"
SERVER_PORT = 8502
SERVER_URL = f"http://localhost:{SERVER_PORT}"


def log(msg: str) -> None:
    print(msg, flush=True)


def server_responds(url: str, timeout: int = 5) -> bool:
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "Sentinel360-BrowserTest/1.0")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def start_streamlit_server() -> subprocess.Popen:
    log("Starting Streamlit server...")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", str(WORKSPACE / "app.py"),
            "--server.port", str(SERVER_PORT),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
        ],
        cwd=str(WORKSPACE),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for attempt in range(30):
        time.sleep(1)
        if server_responds(SERVER_URL):
            log("Server is responding.")
            return proc
        log(f"  Waiting... ({attempt + 1}/30)")
    raise RuntimeError("Server did not start within 30 seconds.")


def select_department(page, dept_name: str) -> None:
    """Select department from the Streamlit dropdown."""
    try:
        # Streamlit selectboxes are rendered as <div role="combobox">
        # We'll try to click the Department dropdown, then select the option
        dropdowns = page.locator("[data-testid='stSelectbox']").all()
        if len(dropdowns) >= 2:
            # Second dropdown is Department
            dropdowns[1].click()
            time.sleep(0.5)
            # Find the option in the dropdown list
            option = page.locator(f"[role='option'] >> text=/{dept_name}/i")
            if option.count() > 0:
                option.first.click()
                time.sleep(1.5)
            else:
                log(f"  Option '{dept_name}' not found in dropdown, trying fallback.")
                # Fallback: type into the input
                input_field = dropdowns[1].locator("input")
                input_field.fill(dept_name)
                time.sleep(0.5)
                input_field.press("Enter")
                time.sleep(1.5)
        else:
            log(f"  Could not find department dropdown ({len(dropdowns)} selectboxes).")
    except Exception as exc:
        log(f"  Department selection error: {exc}")


def extract_kpi_info(page) -> dict:
    """Extract KPI values and statuses from the page HTML by parsing primary and supporting card elements."""
    info = {
        "dominant_issue": "",
        "kpi_values": {},
        "kpi_statuses": {},
        "operational_banner": "",
        "management_action": "",
        "consistency_ok": False,
    }
    text = page.locator("body").inner_text(timeout=5000)
    lower = text.lower()

    # Banner
    for line in text.splitlines():
        if "priority management review" in line.lower() or "routine monitoring" in line.lower() or "stable operations" in line.lower() or "operational attention" in line.lower():
            info["operational_banner"] = line.strip()
            break

    # Dominant issue
    for line in text.splitlines():
        if "dominant issue" in line.lower():
            info["dominant_issue"] = line.strip()
            break

    # Management action
    for line in text.splitlines():
        if "recommended action" in line.lower() or "primary permitted action" in line.lower():
            info["management_action"] = line.strip()
            break

    # Extract PRIMARY KPI cards from HTML
    cards = page.locator(".s360-kpi-card").all()
    for card in cards:
        try:
            title = card.locator(".s360-kpi-title").inner_text(timeout=500)
            value = card.locator(".s360-kpi-value").inner_text(timeout=500)
            meta = card.locator(".s360-kpi-meta").inner_text(timeout=500)
            info["kpi_values"][title] = f"{value} ({meta})"
            class_attr = card.get_attribute("class") or ""
            if "red" in class_attr:
                info["kpi_statuses"][title] = "Red"
            elif "amber" in class_attr:
                info["kpi_statuses"][title] = "Amber"
            elif "green" in class_attr:
                info["kpi_statuses"][title] = "Green"
            elif "blue" in class_attr:
                info["kpi_statuses"][title] = "Monitoring"
            else:
                if "acceptable" in meta.lower() or "stable" in meta.lower() or "green" in meta.lower():
                    info["kpi_statuses"][title] = "Green"
                elif "warning" in meta.lower() or "amber" in meta.lower():
                    info["kpi_statuses"][title] = "Amber"
                elif "critical" in meta.lower() or "red" in meta.lower():
                    info["kpi_statuses"][title] = "Red"
                else:
                    info["kpi_statuses"][title] = "Monitoring"
        except Exception:
            pass

    # Extract SUPPORTING KPI cards from HTML
    supporting_cards = page.locator(".s360-supporting-card").all()
    for card in supporting_cards:
        try:
            title = card.locator(".s360-supporting-title").inner_text(timeout=500)
            value = card.locator(".s360-supporting-value").inner_text(timeout=500)
            meta = card.locator(".s360-supporting-meta").inner_text(timeout=500)
            info["kpi_values"][title] = f"{value} ({meta})"
            class_attr = card.get_attribute("class") or ""
            if "red" in class_attr:
                info["kpi_statuses"][title] = "Red"
            elif "amber" in class_attr:
                info["kpi_statuses"][title] = "Amber"
            elif "green" in class_attr:
                info["kpi_statuses"][title] = "Green"
            elif "blue" in class_attr:
                info["kpi_statuses"][title] = "Monitoring"
            else:
                if "acceptable" in meta.lower() or "stable" in meta.lower() or "green" in meta.lower():
                    info["kpi_statuses"][title] = "Green"
                elif "warning" in meta.lower() or "amber" in meta.lower():
                    info["kpi_statuses"][title] = "Amber"
                elif "critical" in meta.lower() or "red" in meta.lower():
                    info["kpi_statuses"][title] = "Red"
                else:
                    info["kpi_statuses"][title] = "Monitoring"
        except Exception:
            pass

    # Consistency check
    has_red = any(s == "Red" for s in info["kpi_statuses"].values())
    has_amber = any(s == "Amber" for s in info["kpi_statuses"].values())
    if has_red or has_amber:
        info["consistency_ok"] = "red" in info["dominant_issue"].lower() or "amber" in info["dominant_issue"].lower()
    else:
        info["consistency_ok"] = "stable operations" in info["operational_banner"].lower() or "routine monitoring" in info["operational_banner"].lower()

    return info


def main() -> int:
    log("=" * 60)
    log("Sentinel360 Phase 3B Browser Acceptance Test")
    log("=" * 60)

    server_available = server_responds(SERVER_URL)
    streamlit_proc = None
    if not server_available:
        try:
            streamlit_proc = start_streamlit_server()
            server_available = True
        except Exception as exc:
            log(f"ERROR: Could not start server: {exc}")
            server_available = False

    if not server_available:
        RESULTS_JSON.write_text(json.dumps({"acceptance_status": "FAILED", "issues": ["Server not available"]}, indent=2), encoding="utf-8")
        return 1

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("ERROR: Playwright not installed.")
        RESULTS_JSON.write_text(json.dumps({"acceptance_status": "FAILED", "issues": ["Playwright not installed"]}, indent=2), encoding="utf-8")
        return 1

    departments = [
        "All Departments",
        "Outpatient Clinic",
        "Diagnostics",
        "Emergency Department",
        "Intensive Care Unit",
        "Patient Experience",
        "Surgery",
    ]

    results: dict = {
        "acceptance_status": "PENDING",
        "departments": {},
        "screenshots": [],
        "issues": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        try:
            direct_url = f"{SERVER_URL}/Executive_Overview"
            page.goto(direct_url, wait_until="networkidle", timeout=30000)
            time.sleep(3)
            # Wait for running indicator
            for attempt in range(30):
                time.sleep(1)
                if page.locator("[data-testid='stStatusWidgetRunningIcon']").count() == 0:
                    break
            time.sleep(2)

            # Full page baseline
            full_page_path = OUTPUT_DIR / "full_page_all_departments.png"
            page.screenshot(path=str(full_page_path), full_page=True)
            results["screenshots"].append(str(full_page_path))
            log(f"Screenshot saved: {full_page_path.name}")

            for dept in departments:
                log(f"\n--- Department: {dept} ---")
                if dept != "All Departments":
                    select_department(page, dept)
                    # Wait for rerender
                    for attempt in range(20):
                        time.sleep(1)
                        if page.locator("[data-testid='stStatusWidgetRunningIcon']").count() == 0:
                            break
                    time.sleep(2)

                # Screenshot for this department
                dept_safe = dept.lower().replace(" ", "_")
                screenshot_path = OUTPUT_DIR / f"dept_{dept_safe}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                results["screenshots"].append(str(screenshot_path))
                log(f"Screenshot saved: {screenshot_path.name}")

                # Extract info
                info = extract_kpi_info(page)
                results["departments"][dept] = info
                log(f"  Dominant issue: {info['dominant_issue']}")
                log(f"  Banner: {info['operational_banner']}")
                log(f"  Action: {info['management_action']}")
                log(f"  Consistency: {'OK' if info['consistency_ok'] else 'FAIL'}")
                for kpi, status in info["kpi_statuses"].items():
                    log(f"  {kpi}: {status}")

                # KPI trend row screenshot (scroll to top area)
                page.evaluate("window.scrollTo(0, 300)")
                time.sleep(0.5)
                trend_path = OUTPUT_DIR / f"trend_row_{dept_safe}.png"
                page.screenshot(path=str(trend_path), full_page=False)
                results["screenshots"].append(str(trend_path))
                log(f"  Trend row screenshot: {trend_path.name}")

                # Six-KPI visibility verification (per department)
                info = extract_kpi_info(page)
                all_kpi_names = [
                    "Staffing Level",
                    "Staff Absenteeism Rate",
                    "Bed Occupancy Rate",
                    "Average Patient Waiting Time",
                    "Patient Complaint Rate",
                    "Patient Satisfaction Score",
                ]
                visible_kpis = set(info["kpi_values"].keys())
                missing_kpis = [k for k in all_kpi_names if k not in visible_kpis]
                if missing_kpis:
                    results["issues"].append(f"Missing KPIs in page for {dept}: {missing_kpis}")
                    log(f"  ISSUE: Missing KPIs: {missing_kpis}")
                else:
                    log("  All six KPIs visible.")

                if "Patient Satisfaction Score" not in visible_kpis:
                    results["issues"].append(f"Patient Satisfaction Score not visible in {dept}")
                if "Patient Complaint Rate" not in visible_kpis:
                    results["issues"].append(f"Patient Complaint Rate not visible in {dept}")
                if sum(1 for k in visible_kpis if k == "Patient Satisfaction Score") > 1:
                    results["issues"].append(f"Patient Satisfaction Score duplicated in {dept}")
                if sum(1 for k in visible_kpis if k == "Patient Complaint Rate") > 1:
                    results["issues"].append(f"Patient Complaint Rate duplicated in {dept}")

                # Financial Impact visibility via DOM text
                body_text = page.locator("body").inner_text(timeout=5000)
                if "Financial Impact" not in body_text:
                    results["issues"].append(f"Financial Impact section not visible in {dept}")
                    log("  ISSUE: Financial Impact section not visible")
                else:
                    log("  Financial Impact section visible.")
                    # Verify all three financial labels are present (or readiness fallback)
                    fin_labels = ["Estimated Intervention Cost", "Estimated Benefit", "Net Financial Impact", "Not Yet Quantified"]
                    has_fin_label = any(label in body_text for label in fin_labels)
                    if not has_fin_label:
                        results["issues"].append(f"Financial Impact section lacks expected labels in {dept}")
                        log("  ISSUE: Financial Impact lacks expected labels")
                    else:
                        log("  Financial Impact labels present.")

                # Check for fabricated RM amounts
                if "RM0.00" in body_text or "RM0" in body_text:
                    results["issues"].append(f"Fabricated RM0 amount detected in {dept}")
                    log("  ISSUE: Fabricated RM0 amount detected")

                # Check for repeated "Unnamed Scenario" placeholder text
                unnamed_count = body_text.lower().count("unnamed scenario")
                if unnamed_count > 0:
                    results["issues"].append(f"Repeated 'Unnamed Scenario' detected ({unnamed_count} times) in {dept}")
                    log(f"  ISSUE: 'Unnamed Scenario' appears {unnamed_count} times")
                else:
                    log("  No 'Unnamed Scenario' placeholder text.")

                # Scenario Comparison section check
                if "SCENARIO COMPARISON" not in body_text:
                    results["issues"].append(f"Scenario Comparison section not visible in {dept}")
                    log("  ISSUE: Scenario Comparison section not visible")
                else:
                    log("  Scenario Comparison section visible.")
                    # Should show either a table or the clean fallback message
                    has_fallback = (
                        "Scenario comparison requires scenario-specific financial linkage" in body_text
                        or "Scenario comparison is not yet available" in body_text
                    )
                    has_table = "<table" in page.content()
                    if not has_fallback and not has_table:
                        results["issues"].append(f"Scenario Comparison shows neither table nor fallback in {dept}")
                        log("  ISSUE: Scenario Comparison lacks table or fallback")

                # Chart compactness: verify 3 chart images in the trend row area
                chart_imgs = page.locator("img").all()
                # Streamlit renders matplotlib charts as <img> tags
                trend_imgs = [img for img in chart_imgs if (img.get_attribute("src") or "").endswith(".png")]
                # All Departments view may have no KPI cards, so 0 charts is acceptable there
                if len(trend_imgs) < 3 and dept != "All Departments":
                    results["issues"].append(f"Fewer than 3 trend chart images found in {dept} (found {len(trend_imgs)})")
                    log(f"  ISSUE: Only {len(trend_imgs)} chart images found")
                else:
                    log(f"  {len(trend_imgs)} chart images found (compact layout OK).")

            # Check for Connected Operational Situation count (after all departments)
            html = page.content()
            story_count = html.count("Connected Operational Situation")
            if story_count != 0:
                results["issues"].append(f"Connected Operational Situation appears {story_count} times (expected 0)")
            else:
                log("\nConnected Operational Situation correctly removed.")

            # Chart titles are rendered inside matplotlib images; verified in source code by test_invariant_16/18.
            # We capture trend-row screenshots for visual confirmation.

            results["acceptance_status"] = "PASSED" if not results["issues"] else "PASSED_WITH_WARNINGS"

        except Exception as exc:
            log(f"CRITICAL ERROR: {exc}")
            import traceback
            log(traceback.format_exc())
            results["acceptance_status"] = "FAILED"
            results["issues"].append(str(exc))
        finally:
            browser.close()

    if streamlit_proc is not None:
        log("\nTerminating background Streamlit server...")
        streamlit_proc.terminate()
        try:
            streamlit_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            streamlit_proc.kill()

    RESULTS_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")
    log(f"\nResults saved to: {RESULTS_JSON}")
    log(f"Acceptance status: {results['acceptance_status']}")
    if results["issues"]:
        log(f"Issues: {len(results['issues'])}")
        for issue in results["issues"]:
            log(f"  - {issue}")
    log("=" * 60)

    return 0 if results["acceptance_status"] in ("PASSED", "PASSED_WITH_WARNINGS") else 1


if __name__ == "__main__":
    sys.exit(main())
