from langgraph_agent_lab.metrics import ScenarioMetric, summarize_metrics
from langgraph_agent_lab.report import render_report


def test_render_report_contains_summary_and_scenario_table():
    report = summarize_metrics(
        [
            ScenarioMetric(
                scenario_id="S01",
                success=True,
                expected_route="simple",
                actual_route="simple",
            )
        ]
    )

    rendered = render_report(report)

    assert "## 4. Scenario results" in rendered
    assert "| Total scenarios | 1 |" in rendered
    assert "| S01 | simple | simple | PASS | 0 | 0 |" in rendered
