"""Validation issue tracker with deduplication support."""

from typing import List, Dict, Optional


class ValidationIssueEngine:
    """Collect, deduplicate, and manage validation issues."""

    def __init__(self):
        self._issues: List[Dict] = []

    def add_issue(
        self,
        filename: str,
        dataset_type: str,
        issue_category: str,
        issue_severity: str,
        issue_description: str,
        column_name: str = "",
        row_number: str = "",
        observed_value: str = "",
        expected_rule: str = "",
        suggested_correction: str = "",
        blocking_flag: str = "Non-blocking",
        validation_issue_id: str = "",
        upload_session_id: str = "",
    ) -> Dict:
        issue = {
            "validation_issue_id": validation_issue_id,
            "upload_session_id": upload_session_id,
            "filename": filename,
            "dataset_type": dataset_type,
            "row_number": str(row_number),
            "column_name": column_name,
            "issue_category": issue_category,
            "issue_severity": issue_severity,
            "issue_description": issue_description,
            "observed_value": observed_value,
            "expected_rule": expected_rule,
            "suggested_correction": suggested_correction,
            "blocking_flag": blocking_flag,
            "timestamp": "",
        }
        self._issues.append(issue)
        return issue

    def get_issues(self) -> List[Dict]:
        return self._issues.copy()

    def clear(self):
        self._issues.clear()

    def deduplicate(self) -> List[Dict]:
        """Remove duplicate issues based on filename, dataset_type, issue_category, column_name, issue_description."""
        seen = set()
        unique = []
        for issue in self._issues:
            key = (
                issue.get("filename", ""),
                issue.get("dataset_type", ""),
                issue.get("issue_category", ""),
                issue.get("column_name", ""),
                issue.get("issue_description", ""),
            )
            if key not in seen:
                seen.add(key)
                unique.append(issue)
        self._issues = unique
        return self._issues.copy()

    def count_by_severity(self, severity: str) -> int:
        return sum(1 for i in self._issues if i.get("issue_severity") == severity)

    def has_blocking_issues(self) -> bool:
        return any(i.get("blocking_flag") == "Blocking" for i in self._issues)
