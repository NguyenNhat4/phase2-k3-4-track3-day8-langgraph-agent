# Day 08 Lab Report

## 1. Team / student

- Name: Nguyen Minh Nhat
- Repo/commit: local working tree
- Date: 2026-08-25

## 2. Architecture

The workflow is a LangGraph `StateGraph` with a single entry path:
`START -> intake -> classify`. Classification then branches to a simple answer,
tool lookup, clarification, or risky-action approval. Tool results pass through
`evaluate`; transient failures go through bounded `retry` back to `tool`, while
exhausted retries go to `dead_letter`. Every branch ends at `finalize -> END`.

## 3. State schema

| Field | Reducer | Why |
|---|---|---|
| `messages` | append | Keep conversational trace entries. |
| `tool_results` | append | Preserve every tool attempt for evaluation and audit. |
| `errors` | append | Preserve retry and failure history. |
| `events` | append | Record every visited node and outcome. |
| `route`, `attempt`, `evaluation_result` | overwrite | Store the current routing state. |
| `approval`, `final_answer`, `pending_question` | overwrite | Store the current decision or user-facing result. |

## 4. Scenario results

| Scenario | Expected route | Actual route | Success | Retries | Interrupts |
|---|---|---|---:|---:|---:|
| S01_simple | simple | simple | PASS | 0 | 0 |
| S02_tool | tool | tool | PASS | 0 | 0 |
| S03_missing | missing_info | missing_info | PASS | 0 | 0 |
| S04_risky | risky | risky | PASS | 0 | 1 |
| S05_error | error | error | PASS | 2 | 0 |
| S06_delete | risky | risky | PASS | 0 | 1 |
| S07_dead_letter | error | error | PASS | 1 | 0 |

### Summary

| Metric | Value |
|---|---:|
| Total scenarios | 7 |
| Success rate | 100.0% |
| Average nodes visited | 6.43 |
| Total retries | 3 |
| Total interrupts | 2 |
| Resume success | Not demonstrated |

## 5. Failure analysis

1. Retry or tool failure: a tool result containing `ERROR` becomes
   `needs_retry`. The retry node increments `attempt`; once `attempt >=
   max_attempts`, the graph routes to `dead_letter`, preventing an infinite loop.
2. Risky action without approval: risky requests are prepared first and then
   pass through approval. Rejection routes to clarification and never executes
   the tool branch.
3. Missing information: vague requests do not receive an invented answer;
   `clarify` creates a pending question and then finalizes the audit trail.

All recorded scenarios passed.

## 6. Persistence / recovery evidence

The scenario run uses a per-scenario `thread_id` in the LangGraph config. The
default lab configuration uses the in-memory checkpointer, which supports
thread-scoped state during one process. Crash-resume and durable SQLite
evidence were not part of this Phase 4 run.

## 7. Extension work

The graph includes the approval/HITL node and bounded retry/dead-letter path.
The classifier keeps the required LLM call for ambiguous requests and adds a
high-confidence safety guard for explicit side effects such as `refund`,
`delete`, `cancel`, and `send email`, ensuring those requests cannot bypass
approval because of classifier variance.

`streamlit_app.py` provides the interactive approval UI. It starts a workflow
with a stable session `thread_id`, displays the proposed action at an
interrupt, and resumes the same checkpoint with `Command(resume=...)` after
Approve or Reject. The batch CLI deliberately forces deterministic mock
approval so `make run-scenarios` can complete all scenarios; Streamlit is the
real interrupt/resume entrypoint.

## 8. Improvement plan

First, add a SQLite checkpointer run with state-history output and a regression
test for restart recovery. Next, replace the mock tool with authenticated,
observable integrations and add latency/error metrics per node. Finally,
demonstrate a full Streamlit reject/resume run and record its checkpoint
evidence alongside this batch report.
