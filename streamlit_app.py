"""Streamlit approval UI for the LangGraph workflow."""

from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

import streamlit as st
from langgraph.types import Command

from langgraph_agent_lab.graph import build_graph
from langgraph_agent_lab.persistence import build_checkpointer
from langgraph_agent_lab.state import Route, Scenario, initial_state


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _interrupt_payload(snapshot: Any) -> dict | None:
    """Return the first pending interrupt payload, if this run is paused."""
    for task in getattr(snapshot, "tasks", ()):
        for interrupt in getattr(task, "interrupts", ()):
            value = getattr(interrupt, "value", interrupt)
            return value if isinstance(value, dict) else {"proposed_action": str(value)}
    return None


st.set_page_config(page_title="Approval workflow", page_icon="✅")
st.title("Human approval workflow")
st.caption("Yêu cầu có tác động sẽ tạm dừng để người có thẩm quyền phê duyệt.")

# The UI is the explicit real-HITL entrypoint; library and batch CLI remain offline-safe.
os.environ["LANGGRAPH_INTERRUPT"] = "true"

if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"streamlit-{uuid4()}"
if "graph" not in st.session_state:
    st.session_state.graph = build_graph(checkpointer=build_checkpointer("memory"))

graph = st.session_state.graph
thread_id = st.session_state.thread_id
config = _config(thread_id)
snapshot = graph.get_state(config)
pending = _interrupt_payload(snapshot)

if pending:
    st.warning("Workflow đang chờ quyết định.")
    st.subheader("Hành động đề xuất")
    st.write(pending.get("proposed_action", "Không có mô tả hành động."))
    comment = st.text_area("Ghi chú (không bắt buộc)", key="approval_comment")
    approve, reject = st.columns(2)
    with approve:
        if st.button("Phê duyệt", type="primary", use_container_width=True):
            graph.invoke(Command(resume={"approved": True, "comment": comment}), config=config)
            st.rerun()
    with reject:
        if st.button("Từ chối", use_container_width=True):
            graph.invoke(Command(resume={"approved": False, "comment": comment}), config=config)
            st.rerun()
else:
    query = st.text_area("Yêu cầu hỗ trợ", placeholder="Ví dụ: Refund this customer")
    if st.button("Chạy workflow", type="primary", disabled=not query.strip()):
        scenario = Scenario(id=thread_id, query=query.strip(), expected_route=Route.SIMPLE)
        with st.spinner("Đang xử lý yêu cầu..."):
            graph.invoke(initial_state(scenario), config=config)
        st.rerun()

snapshot = graph.get_state(config)
values = snapshot.values or {}
if values.get("final_answer"):
    st.subheader("Kết quả")
    st.success(values["final_answer"])
if values.get("events"):
    with st.expander("Audit events"):
        st.json(values["events"])
