"""Sentinel360 — Step 3A: Data Upload and Validation Page."""

import os
import sys
import uuid
import datetime
import pandas as pd
import streamlit as st
from io import BytesIO

# Ensure src is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.streamlit_upload_page_controller import process_uploaded_file
from src.streamlit_upload_session_manager import UploadSessionManager
from src.streamlit_validation_issue_engine import ValidationIssueEngine
from src.streamlit_upload_manifest_engine import UploadManifestEngine
from src.streamlit_upload_report_engine import UploadReportEngine
from src.streamlit_upload_logging import log_event, log_exception
from src.streamlit_schema_registry import load_required_file_config
from src.streamlit_validation_scorecard_engine import compute_overall_status
from src.streamlit_file_reader import read_uploaded_file
from src.s360_sidebar_chrome import render_sidebar_chrome

# --- SIDEBAR CHROME (brand + footer + native nav styling) ---
render_sidebar_chrome()

DEMO_DIR = os.path.join(PROJECT_ROOT, "data", "demo")

# --------------------------------------------------
# SESSION STATE INITIALISATION
# --------------------------------------------------
def init_state():
    if "upload_session_id" not in st.session_state:
        st.session_state.upload_session_id = f"S3A-{uuid.uuid4().hex[:12].upper()}"
    if "upload_timestamp" not in st.session_state:
        st.session_state.upload_timestamp = datetime.datetime.now().isoformat()
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = {}
    if "file_metadata" not in st.session_state:
        st.session_state.file_metadata = {}
    if "validation_issues" not in st.session_state:
        st.session_state.validation_issues = {}
    if "validation_scorecards" not in st.session_state:
        st.session_state.validation_scorecards = {}
    if "confirmed_dataset_types" not in st.session_state:
        st.session_state.confirmed_dataset_types = {}
    if "validation_completed" not in st.session_state:
        st.session_state.validation_completed = False
    if "processing_status" not in st.session_state:
        st.session_state.processing_status = "New Data Uploaded"
    if "validation_status" not in st.session_state:
        st.session_state.validation_status = "Not Yet Validated"
    if "selected_preview_file" not in st.session_state:
        st.session_state.selected_preview_file = None
    if "preview_row_count" not in st.session_state:
        st.session_state.preview_row_count = 20

init_state()

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.title("DATA UPLOAD AND VALIDATION")
st.caption("Upload hospital operational data, verify quality, and confirm readiness for Sentinel360 processing.")

st.info("Sentinel360 validates uploaded data before analytical processing. Files that do not meet required schema, quality, or integrity rules are flagged for correction.")

# Page-level styles for the ETL flow diagram and Processing Status card.
st.markdown(
    """<style>
.s360-etl-flow {
    display: flex;
    align-items: stretch;
    background: #F4F7FB;
    border: 1px solid #DDE3EC;
    border-radius: 10px;
    padding: 14px;
    margin: 6px 0 10px 0;
    flex-wrap: wrap;
}
.s360-etl-node {
    flex: 1 1 180px;
    background: #FFFFFF;
    border: 1px solid #DDE3EC;
    border-left: 4px solid #2F6FB3;
    border-radius: 8px;
    padding: 12px 14px;
    text-align: left;
    min-width: 160px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.s360-etl-step {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: #2F6FB3;
    color: #FFFFFF;
    font-size: 0.85rem;
    font-weight: 800;
    margin-bottom: 6px;
    line-height: 1;
}
.s360-etl-label {
    font-size: 0.78rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    color: #1A365D;
    margin: 0 0 3px 0;
    line-height: 1.2;
}
.s360-etl-desc {
    font-size: 0.78rem;
    font-weight: 500;
    color: #4A5568;
    line-height: 1.4;
}
.s360-etl-arrow {
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    color: #2F6FB3;
    font-weight: 800;
    padding: 0 12px;
    min-width: 28px;
}
@media (max-width: 1100px) {
    .s360-etl-flow { flex-direction: column; }
    .s360-etl-arrow { transform: rotate(90deg); padding: 6px 0; }
}

/* Processing Status card */
.s360-ps-card {
    background: #FFFFFF;
    border: 1px solid #DDE3EC;
    border-left: 5px solid #2F6FB3;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 8px 0 12px 0;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.s360-ps-card .s360-ps-title {
    font-size: 0.68rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.85px;
    color: #1A365D;
    margin: 0 0 10px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #DDE3EC;
    line-height: 1.2;
}
.s360-ps-card .s360-ps-row { margin: 8px 0 10px 0; }
.s360-ps-card .s360-ps-row:last-child { margin-bottom: 0; }
.s360-ps-card .s360-ps-label {
    display: block;
    font-size: 0.66rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    color: #1A365D;
    margin-bottom: 3px;
    line-height: 1.2;
}
.s360-ps-card .s360-ps-label.ok   { color: #2F7D32; }
.s360-ps-card .s360-ps-label.warn { color: #C53030; }
.s360-ps-card .s360-ps-body {
    font-size: 0.95rem;
    font-weight: 500;
    color: #1A2B47;
    line-height: 1.55;
}
</style>""",
    unsafe_allow_html=True,
)

# --------------------------------------------------
# ETL PROCESS — horizontal process diagram
# --------------------------------------------------
st.markdown("##### ETL Process")
_etl_html = (
    '<div class="s360-etl-flow">'
    '<div class="s360-etl-node">'
    '<div class="s360-etl-step">1</div>'
    '<div class="s360-etl-label">Extract</div>'
    '<div class="s360-etl-desc">Upload operational data</div>'
    '</div>'
    '<div class="s360-etl-arrow">&rarr;</div>'
    '<div class="s360-etl-node">'
    '<div class="s360-etl-step">2</div>'
    '<div class="s360-etl-label">Validate</div>'
    '<div class="s360-etl-desc">Check schema, completeness and quality</div>'
    '</div>'
    '<div class="s360-etl-arrow">&rarr;</div>'
    '<div class="s360-etl-node">'
    '<div class="s360-etl-step">3</div>'
    '<div class="s360-etl-label">Transform</div>'
    '<div class="s360-etl-desc">Standardize and map accepted data</div>'
    '</div>'
    '<div class="s360-etl-arrow">&rarr;</div>'
    '<div class="s360-etl-node">'
    '<div class="s360-etl-step">4</div>'
    '<div class="s360-etl-label">Load</div>'
    '<div class="s360-etl-desc">Prepare governed data for Sentinel360 analytics</div>'
    '</div>'
    '</div>'
)
st.markdown(_etl_html, unsafe_allow_html=True)
st.divider()

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def get_status_color(status: str) -> str:
    mapping = {
        "Accepted": "green",
        "Accepted with Warnings": "orange",
        "Rejected": "red",
        "Not Yet Validated": "grey",
        "Ready for Processing": "green",
        "Ready with Warnings": "orange",
        "Correction Required": "red",
        "Not Assessable": "grey",
        "New Data Uploaded": "blue",
        "Validation Pending": "blue",
        "Processing Required": "orange",
        "Processing Complete": "green",
    }
    return mapping.get(status, "grey")


def count_by_status(files: dict, status: str) -> int:
    return sum(1 for f in files.values() if f.get("validation_status") == status)


# --------------------------------------------------
# SECTION A — UPLOAD SESSION SUMMARY
# --------------------------------------------------
with st.container():
    st.subheader("Upload Session Summary")
    cols = st.columns(4)
    total = len(st.session_state.file_metadata)
    accepted = count_by_status(st.session_state.file_metadata, "Accepted")
    warnings = count_by_status(st.session_state.file_metadata, "Accepted with Warnings")
    rejected = count_by_status(st.session_state.file_metadata, "Rejected")
    cols[0].metric("Files Uploaded", total)
    cols[1].metric("Files Accepted", accepted)
    cols[2].metric("Files with Warnings", warnings)
    cols[3].metric("Files Rejected", rejected)

    c1, c2, c3, c4 = st.columns(4)
    c1.text_input("Upload Session ID", value=st.session_state.upload_session_id, disabled=True, key="session_id_display")
    c2.text_input("Upload Timestamp", value=st.session_state.upload_timestamp, disabled=True, key="timestamp_display")
    c3.text_input("Validation Status", value=st.session_state.validation_status, disabled=True, key="validation_status_display")
    c4.text_input("Data Refresh Status", value=st.session_state.processing_status, disabled=True, key="processing_status_display")

    # --- Lightweight row-level summary cards (ETL demo) ---
    # Derive counts only from values already present in session state.
    _rows_received = sum(
        int(meta.get("row_count", 0) or 0)
        for meta in st.session_state.file_metadata.values()
    )
    _preview_rows_with_issues: set = set()
    for _fname, _iss in st.session_state.validation_issues.items():
        for _i in _iss:
            _rn = _i.get("row_number", "")
            if _rn not in (None, "", "0"):
                try:
                    _preview_rows_with_issues.add(int(_rn))
                except (TypeError, ValueError):
                    continue
    _rows_review = min(len(_preview_rows_with_issues), _rows_received)
    _rows_accepted = max(_rows_received - _rows_review, 0)

    st.markdown("##### Validation Summary (Preview Sample)")
    _rcol1, _rcol2, _rcol3 = st.columns(3, gap="small")
    _rcol1.metric("Rows Received", _rows_received)
    _rcol2.metric("Rows Accepted", _rows_accepted)
    _rcol3.metric("Rows Requiring Review", _rows_review)
    st.caption("Counts reflect the validated preview sample processed by the current ETL pipeline.")

st.markdown("---")

# --------------------------------------------------
# SECTION B — DATASET UPLOAD
# --------------------------------------------------
with st.container():
    st.subheader("Dataset Upload")
    use_demo = st.radio("Data source", options=["Upload My Own Files", "Use Existing Synthetic Demo Files"], key="data_source")

    st.session_state.demo_mode = (use_demo == "Use Existing Synthetic Demo Files")
    if use_demo == "Use Existing Synthetic Demo Files":
        demo_files = {
            "Staff Roster": "staff_roster.csv",
            "Staff Attendance": "staff_attendance.csv",
            "Patient Encounters": "patient_encounters.csv",
            "Bed Occupancy": "bed_capacity_records.csv",
            "Patient Queue": "patient_queue_records.csv",
            "Patient Complaints": "patient_complaints.csv",
            "Patient Survey": "patient_surveys.csv",
        }
        st.markdown("Select demo files to load:")
        selected_demo = []
        for label, fname in demo_files.items():
            if st.checkbox(label, key=f"demo_{label}"):
                selected_demo.append((label, fname))
        if st.button("Load Selected Demo Files", key="load_demo"):
            for label, fname in selected_demo:
                fpath = os.path.join(DEMO_DIR, fname)
                if os.path.exists(fpath):
                    with open(fpath, "rb") as f:
                        content = f.read()
                    st.session_state.uploaded_files[fname] = {"content": content, "demo": True}
            st.rerun()
    else:
        uploaded = st.file_uploader(
            "Drag and drop files here (CSV, XLSX, XLS)",
            type=["csv", "xlsx", "xls"],
            accept_multiple_files=True,
            key="file_uploader",
        )
        if uploaded:
            for up in uploaded:
                st.session_state.uploaded_files[up.name] = {"content": up.getvalue(), "demo": False}

    with st.expander("Supported formats and guidance"):
        st.markdown("""
- **Supported formats:** CSV, XLSX, XLS
- **Expected categories:** Staff Roster, Staff Attendance, Patient Encounters, Bed Occupancy, Patient Queue, Patient Complaints, Patient Survey, Scenario Baseline, KPI Configuration, Other Supporting Data
- **Required datasets:** Staff Attendance, Bed Occupancy, Patient Queue, Patient Complaints, Patient Survey
- **Conditionally required:** Staff Roster (when staff-level attendance validation is performed)
- **Optional:** Patient Encounters, Other Supporting Data
- **Governed supporting:** Scenario Baseline, KPI Configuration (not permitted to overwrite frozen configuration automatically)
""")

st.markdown("---")

# --------------------------------------------------
# SECTION C — DATASET-TYPE CONFIRMATION
# --------------------------------------------------
with st.container():
    st.subheader("Dataset-Type Confirmation")
    if not st.session_state.uploaded_files:
        st.info("No files uploaded yet.")
    else:
        for fname, fdata in st.session_state.uploaded_files.items():
            with st.container():
                c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 1, 1, 1, 2])
                c1.markdown(f"**{fname}**")
                detected = "Unknown"
                confidence = "Not Detected"
                rows = 0
                cols = 0
                if fname in st.session_state.file_metadata:
                    detected = st.session_state.file_metadata[fname].get("detected_dataset_type", "Unknown")
                    confidence = "High"
                    rows = st.session_state.file_metadata[fname].get("row_count", 0)
                    cols = st.session_state.file_metadata[fname].get("column_count", 0)
                c2.markdown(f"Detected: `{detected}` ({confidence})")
                c3.markdown(f"Rows: {rows}")
                c4.markdown(f"Cols: {cols}")
                c5.markdown(f"Size: {len(fdata['content'])} bytes")
                all_types = [
                    "Staff Roster", "Staff Attendance", "Patient Encounters", "Bed Occupancy",
                    "Patient Queue", "Patient Complaints", "Patient Survey",
                    "Scenario Baseline", "KPI Configuration", "Other Supporting Data"
                ]
                current = st.session_state.confirmed_dataset_types.get(fname, detected)
                selected = c6.selectbox("Confirm type", options=all_types, index=all_types.index(current) if current in all_types else 0, key=f"confirm_{fname}")
                if selected != current:
                    st.session_state.confirmed_dataset_types[fname] = selected

st.markdown("---")

# --------------------------------------------------
# VALIDATION TRIGGER
# --------------------------------------------------
with st.container():
    c1, c2 = st.columns([1, 1])
    validate_clicked = c1.button("Validate Uploaded Files", type="primary", key="validate_btn")
    reset_clicked = c2.button("Reset Upload Session", key="reset_btn")

    if reset_clicked:
        st.warning("Are you sure? This will clear all uploaded files, previews, and validation results.")
        confirm_reset = st.button("Confirm Reset", key="confirm_reset")
        if confirm_reset:
            st.session_state.upload_session_id = f"S3A-{uuid.uuid4().hex[:12].upper()}"
            st.session_state.upload_timestamp = datetime.datetime.now().isoformat()
            st.session_state.uploaded_files = {}
            st.session_state.file_metadata = {}
            st.session_state.validation_issues = {}
            st.session_state.validation_scorecards = {}
            st.session_state.confirmed_dataset_types = {}
            st.session_state.validation_completed = False
            st.session_state.processing_status = "New Data Uploaded"
            st.session_state.validation_status = "Not Yet Validated"
            st.session_state.selected_preview_file = None
            st.rerun()

    if validate_clicked and st.session_state.uploaded_files:
        st.session_state.validation_completed = False
        st.session_state.processing_status = "Validation Pending"
        log_event(f"Validation started for session {st.session_state.upload_session_id}")
        for fname, fdata in st.session_state.uploaded_files.items():
            confirmed = st.session_state.confirmed_dataset_types.get(fname, None)
            schema_profile = (
                "SENTINEL360_SYNTHETIC_DEMO"
                if st.session_state.get("demo_mode")
                else "GENERIC_UPLOAD"
            )
            try:
                result = process_uploaded_file(
                    fdata["content"], fname, st.session_state.upload_session_id,
                    dataset_type=confirmed, schema_profile=schema_profile,
                )
                st.session_state.file_metadata[fname] = {
                    "original_filename": fname,
                    "detected_dataset_type": result.get("detected_type", "Unknown"),
                    "confirmed_dataset_type": result.get("dataset_type", confirmed or "Unknown"),
                    "file_extension": fname.split(".")[-1],
                    "file_size_bytes": len(fdata["content"]),
                    "row_count": len(result.get("df_preview", pd.DataFrame())),
                    "column_count": len(result.get("df_preview", pd.DataFrame()).columns),
                    "validation_status": compute_overall_status(result.get("scorecard", [])) if result.get("scorecard") else "Not Yet Validated",
                    "authoritative_status": "Uploaded — Not Authoritative",
                    "schema_profile": schema_profile,
                    "schema_version": result.get("schema_version", ""),
                }
                st.session_state.validation_issues[fname] = result.get("issues", [])
                st.session_state.validation_scorecards[fname] = result.get("scorecard", [])
            except Exception as e:
                log_exception(f"Validation failed for {fname}: {e}")
                # Preserve known metadata; do not overwrite with Unknown/0
                try:
                    df_preview, _ = read_uploaded_file(fdata["content"], fname)
                    row_count = len(df_preview)
                    column_count = len(df_preview.columns)
                except Exception:
                    row_count = 0
                    column_count = 0
                st.session_state.file_metadata[fname] = {
                    "original_filename": fname,
                    "detected_dataset_type": confirmed or "Unknown",
                    "confirmed_dataset_type": confirmed or "Unknown",
                    "file_extension": fname.split(".")[-1],
                    "file_size_bytes": len(fdata["content"]),
                    "row_count": row_count,
                    "column_count": column_count,
                    "validation_status": "Rejected",
                    "authoritative_status": "Uploaded — Not Authoritative",
                    "schema_profile": schema_profile,
                }
                st.session_state.validation_issues[fname] = [{
                    "validation_issue_id": f"ISS-{st.session_state.upload_session_id}-ERR",
                    "upload_session_id": st.session_state.upload_session_id,
                    "filename": fname,
                    "dataset_type": confirmed or "Unknown",
                    "row_number": "",
                    "column_name": "",
                    "issue_category": "Validation Engine",
                    "issue_severity": "Critical",
                    "issue_description": f"Internal validation engine error: {str(e)}",
                    "observed_value": "",
                    "expected_rule": "",
                    "suggested_correction": "",
                    "blocking_flag": "Blocking",
                    "validation_status": "Rejected",
                    "timestamp": datetime.datetime.now().isoformat(),
                }]
                st.session_state.validation_scorecards[fname] = []
        st.session_state.validation_completed = True
        st.session_state.validation_status = "Validation Complete"
        st.session_state.processing_status = "Processing Required"
        st.rerun()

st.markdown("---")

# --------------------------------------------------
# SECTION D — FILE PREVIEW
# --------------------------------------------------
with st.container():
    st.subheader("File Preview")
    if not st.session_state.uploaded_files:
        st.info("No files to preview.")
    else:
        preview_options = list(st.session_state.uploaded_files.keys())
        selected = st.selectbox("Select file to preview", options=preview_options, key="preview_select")
        st.session_state.selected_preview_file = selected
        preview_rows = st.selectbox("Preview rows", options=[5, 10, 20, 50, 100], index=2, key="preview_rows")
        st.session_state.preview_row_count = preview_rows

        if selected and selected in st.session_state.uploaded_files:
            fdata = st.session_state.uploaded_files[selected]
            try:
                from src.streamlit_file_reader import read_uploaded_file
                df, _ = read_uploaded_file(fdata["content"], selected)
                preview_df = df.head(preview_rows)
                tabs = st.tabs(["Data Preview", "Column Profile", "Validation Results", "Issues", "Metadata"])
                with tabs[0]:
                    st.dataframe(preview_df, use_container_width=True)
                with tabs[1]:
                    profile = []
                    for col in df.columns:
                        profile.append({
                            "Column": col,
                            "Inferred Type": str(df[col].dtype),
                            "Null Count": int(df[col].isna().sum()),
                            "Unique Count": int(df[col].nunique()),
                            "Sample": str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else "",
                        })
                    st.dataframe(pd.DataFrame(profile), use_container_width=True)
                with tabs[2]:
                    if selected in st.session_state.validation_scorecards:
                        sc = st.session_state.validation_scorecards[selected]
                        if sc:
                            st.dataframe(pd.DataFrame(sc), use_container_width=True)
                        else:
                            st.info("No validation scorecard available.")
                    else:
                        st.info("Validation not yet run.")
                with tabs[3]:
                    if selected in st.session_state.validation_issues:
                        iss = st.session_state.validation_issues[selected]
                        if iss:
                            st.dataframe(pd.DataFrame(iss), use_container_width=True)
                        else:
                            st.info("No issues found.")
                    else:
                        st.info("Validation not yet run.")
                with tabs[4]:
                    if selected in st.session_state.file_metadata:
                        meta = st.session_state.file_metadata[selected]
                        st.json(meta)
                    else:
                        st.info("Metadata not yet generated.")
            except Exception as e:
                st.error(f"Could not preview file: {e}")
                log_exception(f"Preview failed for {selected}")

st.markdown("---")

# --------------------------------------------------
# SECTION E — VALIDATION SUMMARY
# --------------------------------------------------
with st.container():
    st.subheader("Validation Summary")
    if not st.session_state.file_metadata:
        st.info("No files validated yet.")
    else:
        summary_rows = []
        for fname, meta in st.session_state.file_metadata.items():
            issues = st.session_state.validation_issues.get(fname, [])
            blocking = sum(1 for i in issues if i.get("blocking_flag") == "Blocking")
            warnings = sum(1 for i in issues if i.get("issue_severity") == "Warning" and i.get("blocking_flag") != "Blocking")
            errors = sum(1 for i in issues if i.get("issue_severity") == "Error")
            summary_rows.append({
                "Filename": fname,
                "Dataset Type": meta.get("confirmed_dataset_type", ""),
                "Row Count": meta.get("row_count", 0),
                "Column Count": meta.get("column_count", 0),
                "Schema": "Pass" if not any(i["issue_category"] in ("Missing Column", "Schema") and i.get("blocking_flag") == "Blocking" for i in issues) else "Fail",
                "Data Type": "Pass" if not any(i["issue_category"] == "Data Type" and i.get("blocking_flag") == "Blocking" for i in issues) else "Fail",
                "Missing Values": "Pass" if not any(i["issue_category"] == "Missing Value" for i in issues) else "Warning",
                "Duplicates": "Pass" if not any(i["issue_category"] == "Duplicate Record" for i in issues) else "Warning",
                "Date Validity": "Pass" if not any(i["issue_category"] in ("Invalid Date", "Date Range") and i.get("blocking_flag") == "Blocking" for i in issues) else "Fail",
                "Identifiers": "Pass" if not any(i["issue_category"] == "Invalid Identifier" and i.get("blocking_flag") == "Blocking" for i in issues) else "Fail",
                "Value Range": "Pass" if not any(i["issue_category"] == "Value Range" and i.get("blocking_flag") == "Blocking" for i in issues) else "Fail",
                "Referential": "Not Assessable" if any(i["issue_category"] == "Referential Integrity" and i.get("issue_severity") == "Informational" for i in issues) else ("Pass" if not any(i["issue_category"] == "Referential Integrity" and i.get("blocking_flag") == "Blocking" for i in issues) else "Fail"),
                "Overall": meta.get("validation_status", "Not Yet Validated"),
                "Issues": len(issues),
                "Warnings": warnings,
                "Errors": errors,
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

st.markdown("---")

# --------------------------------------------------
# TRANSFORMATIONS APPLIED (lightweight, honest)
# --------------------------------------------------
with st.container():
    st.subheader("Transformations Applied")
    st.caption(
        "The items below reflect transformations and checks actually executed by the "
        "Sentinel360 ETL validation layer."
    )
    st.markdown(
        """
- **Column names normalized** to the canonical schema via alias mapping
- **Required fields validated** for presence in every uploaded record
- **Data types checked** against the expected schema (numeric, text, identifier)
- **Date formats parsed and verified** for parseability and ordering
- **Identifiers and value ranges checked** for uniqueness and allowed bounds
"""
    )

st.markdown("---")

# --------------------------------------------------
# SECTION F — VALIDATION ISSUES
# --------------------------------------------------
with st.container():
    st.subheader("Validation Issues")
    all_issues = []
    for fname, issues in st.session_state.validation_issues.items():
        all_issues.extend(issues)
    if not all_issues:
        st.info("No issues recorded.")
    else:
        issue_df = pd.DataFrame(all_issues)
        if not issue_df.empty:
            severity_filter = st.multiselect("Filter by severity", options=issue_df["issue_severity"].unique().tolist(), default=issue_df["issue_severity"].unique().tolist(), key="issue_severity_filter")
            category_filter = st.multiselect("Filter by category", options=issue_df["issue_category"].unique().tolist(), default=issue_df["issue_category"].unique().tolist(), key="issue_category_filter")
            filtered = issue_df[
                (issue_df["issue_severity"].isin(severity_filter)) &
                (issue_df["issue_category"].isin(category_filter))
            ]
            st.dataframe(filtered, use_container_width=True)
        else:
            st.info("Issue DataFrame is empty.")

st.markdown("---")

# --------------------------------------------------
# SECTION G — DATA READINESS DECISION
# --------------------------------------------------
with st.container():
    st.subheader("Data Readiness Decision")
    file_readiness = []
    for fname, meta in st.session_state.file_metadata.items():
        status = meta.get("validation_status", "Not Yet Validated")
        if status == "Accepted":
            readiness = "Ready for Processing"
        elif status == "Accepted with Warnings":
            readiness = "Ready with Warnings"
        elif status == "Rejected":
            readiness = "Correction Required"
        else:
            readiness = "Not Assessable"
        file_readiness.append({"Filename": fname, "Readiness": readiness, "Status": status})

    if file_readiness:
        st.dataframe(pd.DataFrame(file_readiness), use_container_width=True)

    overall = "Not Assessable"
    if st.session_state.file_metadata:
        statuses = [f.get("validation_status", "") for f in st.session_state.file_metadata.values()]
        if any(s == "Rejected" for s in statuses):
            overall = "Correction Required"
        elif all(s == "Accepted" for s in statuses):
            overall = "All Required Files Ready"
        elif any(s == "Accepted with Warnings" for s in statuses) and all(s in ("Accepted", "Accepted with Warnings") for s in statuses):
            overall = "Ready with Warnings"
        elif any(s in ("Accepted", "Accepted with Warnings", "Rejected") for s in statuses):
            overall = "Incomplete Required Dataset Set"

    st.metric("Upload-Session Readiness", overall)

    # Check required files presence
    schema_profile = (
        "SENTINEL360_SYNTHETIC_DEMO"
        if st.session_state.get("demo_mode")
        else "GENERIC_UPLOAD"
    )
    req_config = load_required_file_config(schema_profile)
    if not req_config.empty:
        required_types = req_config[req_config["required"].str.lower() == "required"]["dataset_type"].tolist()
        uploaded_types = [f.get("confirmed_dataset_type", "") for f in st.session_state.file_metadata.values()]
        missing = [r for r in required_types if r not in uploaded_types]
        if missing:
            st.warning(f"Missing required datasets: {', '.join(missing)}")
        else:
            if required_types:
                st.success("All required dataset categories are present.")

st.markdown("---")

# --------------------------------------------------
# SECTION H — DOWNLOAD VALIDATION REPORT
# --------------------------------------------------
with st.container():
    st.subheader("Download Validation Report")
    if st.session_state.file_metadata and st.session_state.validation_completed:
        report_engine = UploadReportEngine()
        files_list = list(st.session_state.file_metadata.values())
        all_issues_list = []
        for issues in st.session_state.validation_issues.values():
            all_issues_list.extend(issues)
        summary_df = report_engine.build_validation_summary(files_list, all_issues_list)
        manifest = report_engine.build_manifest_json(
            {
                "upload_session_id": st.session_state.upload_session_id,
                "session_start_timestamp": st.session_state.upload_timestamp,
                "user_display_name": "Demo User",
                "validation_status": st.session_state.validation_status,
                "processing_status": st.session_state.processing_status,
                "session_manifest_version": "1.0",
                "source_type": "Web Upload",
                "governance_note": "Uploaded data is not authoritative until governed processing is completed.",
            },
            files_list,
            all_issues_list,
        )
        c1, c2, c3 = st.columns(3)
        c1.download_button("Download Validation Summary (CSV)", data=summary_df.to_csv(index=False), file_name="validation_summary.csv", mime="text/csv", key="dl_summary")
        c2.download_button("Download Issue Register (CSV)", data=pd.DataFrame(all_issues_list).to_csv(index=False), file_name="issue_register.csv", mime="text/csv", key="dl_issues")
        c3.download_button("Download Upload Manifest (JSON)", data=report_engine.to_json(manifest), file_name="upload_manifest.json", mime="application/json", key="dl_manifest")
    else:
        st.info("Validate files to enable downloads.")

st.markdown("---")

# --------------------------------------------------
# PROCESSING STATUS (compact; replaces former Processing Boundary +
# Readiness Banner sections)
#
# Reuses the same session_state validation_status values already produced
# by the upload/validation controllers. UI only — no validation rules,
# processing pipeline or frozen-snapshot behaviour are touched.
# --------------------------------------------------
_session_statuses = [
    f.get("validation_status", "") for f in st.session_state.file_metadata.values()
]
_has_files = bool(st.session_state.file_metadata)
_has_blocking = any(s == "Rejected" for s in _session_statuses)
_has_warnings = any(s == "Accepted with Warnings" for s in _session_statuses)
_all_clean = _has_files and all(s == "Accepted" for s in _session_statuses)

_not_authoritative_html = (
    '<div class="s360-ps-row">'
    '<span class="s360-ps-label">Not Yet Authoritative</span>'
    '<div class="s360-ps-body">'
    'The uploaded data has not replaced the frozen analytical snapshot '
    'currently used by Sentinel360.'
    '</div>'
    '</div>'
)

_next_step_html = (
    '<div class="s360-ps-row">'
    '<span class="s360-ps-label">Next Step</span>'
    '<div class="s360-ps-body">'
    'Governed processing and approval would be required before KPI, risk, '
    'forecast, scenario and financial outputs are recalculated.'
    '</div>'
    '</div>'
)

_ps_head = '<div class="s360-ps-card"><div class="s360-ps-title">Processing Status</div>'
_ps_tail = '</div>'

if _all_clean:
    _ps_html = (
        _ps_head
        + '<div class="s360-ps-row">'
        + '<span class="s360-ps-label ok">Upload Validated</span>'
        + '<div class="s360-ps-body">The uploaded file has passed the current validation checks.</div>'
        + '</div>'
        + _not_authoritative_html
        + _next_step_html
        + _ps_tail
    )
elif _has_files and (_has_blocking or _has_warnings):
    _ps_html = (
        _ps_head
        + '<div class="s360-ps-row">'
        + '<span class="s360-ps-label warn">Data Requires Review</span>'
        + '<div class="s360-ps-body">'
        + 'The uploaded file contains validation issues that must be resolved before governed processing.'
        + '</div></div>'
        + _not_authoritative_html
        + _ps_tail
    )
else:
    _ps_html = (
        _ps_head
        + '<div class="s360-ps-body">'
        + 'Upload and validate data to determine readiness for the Sentinel360 analytical layer.'
        + '</div>'
        + _ps_tail
    )

st.markdown(_ps_html, unsafe_allow_html=True)

# One prototype note + one footer line.
st.caption(
    "Prototype note: Manual file upload is used only to demonstrate the "
    "ingestion and validation process. In production, Sentinel360 is "
    "designed to receive operational data through automated hospital data "
    "pipelines and connected source systems."
)

st.caption(
    "Sentinel360 Data Upload & Validation — analytical snapshot remains frozen "
    "until governed processing."
)
