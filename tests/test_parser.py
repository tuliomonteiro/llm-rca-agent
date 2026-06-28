"""Tests for Pydantic output schemas — no LLM calls needed."""
import pytest
from src.parser.output import RCAReport, FallbackReport


class TestRCAReport:
    def test_valid_construction(self):
        report = RCAReport(
            root_cause="Connection pool exhausted",
            contributing_factors=["Pool size too small", "Connection leak"],
            impact="All login endpoints returned 503 for 15 minutes",
            timeline="11:30 Deploy → 11:45 Error spike → 11:58 Rollback",
            immediate_actions=["Restart pod", "Kill idle connections"],
            prevention=["Add finally block", "Increase pool size"],
            confidence="HIGH",
        )
        assert report.root_cause == "Connection pool exhausted"
        assert len(report.contributing_factors) == 2
        assert len(report.immediate_actions) == 2

    def test_model_dump_has_all_keys(self):
        report = RCAReport(
            root_cause="OOM",
            contributing_factors=["Memory leak"],
            impact="Worker crashed",
            timeline="14:00 spike → 14:05 OOM",
            immediate_actions=["Restart"],
            prevention=["Fix leak"],
            confidence="MEDIUM",
        )
        d = report.model_dump()
        expected_keys = {
            "root_cause", "contributing_factors", "impact",
            "timeline", "immediate_actions", "prevention", "confidence",
        }
        assert expected_keys == set(d.keys())

    def test_contributing_factors_must_be_list(self):
        with pytest.raises(Exception):
            RCAReport(
                root_cause="X",
                contributing_factors="not a list",  # wrong type
                impact="Y",
                timeline="Z",
                immediate_actions=[],
                prevention=[],
                confidence="LOW",
            )

    def test_missing_required_field_raises(self):
        with pytest.raises(Exception):
            RCAReport(
                contributing_factors=["x"],
                impact="y",
                timeline="z",
                immediate_actions=[],
                prevention=[],
                confidence="LOW",
                # root_cause omitted
            )

    def test_empty_lists_are_valid(self):
        report = RCAReport(
            root_cause="Unknown",
            contributing_factors=[],
            impact="Minor",
            timeline="N/A",
            immediate_actions=[],
            prevention=[],
            confidence="LOW — insufficient data",
        )
        assert report.contributing_factors == []
        assert report.prevention == []


class TestFallbackReport:
    def test_default_message(self):
        report = FallbackReport(
            raw_analysis="Unable to identify root cause",
            recommendation="Add runbooks for this error type",
        )
        assert "No similar incidents" in report.message

    def test_custom_message_override(self):
        report = FallbackReport(
            message="Custom fallback message",
            raw_analysis="Something went wrong",
            recommendation="Check the logs",
        )
        assert report.message == "Custom fallback message"

    def test_model_dump_has_all_keys(self):
        report = FallbackReport(
            raw_analysis="Best effort analysis",
            recommendation="Add more runbooks",
        )
        d = report.model_dump()
        assert "message" in d
        assert "raw_analysis" in d
        assert "recommendation" in d
