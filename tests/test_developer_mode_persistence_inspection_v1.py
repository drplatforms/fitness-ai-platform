from __future__ import annotations

import ast
import sqlite3
from pathlib import Path

import database
from services.daily_coach_async_persistence_service import (
    create_approved_narrative,
    create_async_job,
    get_latest_async_jobs,
    mark_async_job_displayable,
)


def _initialize_temp_database(tmp_path, monkeypatch):
    db_path = tmp_path / "fitness_ai_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    return db_path


def _create_job(job_id: str, *, target_date: str = "2026-06-22"):
    return create_async_job(
        job_id=job_id,
        user_id=1,
        target_date=target_date,
        workflow_target="today",
        next_action_id="review_daily_coach",
        context_hash=f"context-{job_id}",
        context_version="context-v1",
        prompt_contract_version="prompt-v1",
        validator_version="validator-v1",
    )


def _load_streamlit_inspection_helpers() -> dict:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    wanted_names = {
        "DAILY_COACH_ASYNC_PERSISTENCE_JOB_DISPLAY_FIELDS",
        "DAILY_COACH_ASYNC_PERSISTENCE_NARRATIVE_DISPLAY_FIELDS",
        "DAILY_COACH_ASYNC_PERSISTENCE_FORBIDDEN_UI_FIELDS",
        "daily_coach_async_persistence_forbidden_fields_present",
        "daily_coach_async_persistence_safe_job_payload",
        "daily_coach_async_persistence_safe_narrative_payload",
    }
    helper_nodes = []
    for node in module.body:
        if isinstance(node, ast.Assign):
            names = [
                target.id for target in node.targets if isinstance(target, ast.Name)
            ]
            if any(name in wanted_names for name in names):
                helper_nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in wanted_names:
            helper_nodes.append(node)

    namespace: dict = {}
    compiled = ast.Module(body=helper_nodes, type_ignores=[])
    ast.fix_missing_locations(compiled)
    exec(compile(compiled, "ui/streamlit_app.py", "exec"), namespace)
    return namespace


def test_latest_async_jobs_reads_recent_jobs_without_mutation(tmp_path, monkeypatch):
    db_path = _initialize_temp_database(tmp_path, monkeypatch)
    _create_job("job-1")
    _create_job("job-2")

    jobs = get_latest_async_jobs(user_id=1, target_date="2026-06-22", limit=10)

    assert [job.job_id for job in jobs] == ["job-2", "job-1"]

    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM daily_coach_async_jobs").fetchone()[0]
    conn.close()
    assert count == 2


def test_streamlit_inspection_helpers_exclude_forbidden_fields():
    helpers = _load_streamlit_inspection_helpers()

    job_payload = helpers["daily_coach_async_persistence_safe_job_payload"](
        {
            "job_id": "job-1",
            "status": "approved",
            "raw_provider_output": "forbidden",
            "rejected_provider_output": "forbidden",
            "full_prompt": "forbidden",
        }
    )

    assert job_payload["job_id"] == "job-1"
    assert "raw_provider_output" not in job_payload
    assert "rejected_provider_output" not in job_payload
    assert "full_prompt" not in job_payload
    assert helpers["daily_coach_async_persistence_forbidden_fields_present"](
        {"raw_provider_output": "forbidden"}
    ) == ["raw_provider_output"]


def test_streamlit_inspection_narrative_requires_displayable_public_safe_gate():
    helpers = _load_streamlit_inspection_helpers()
    safe_narrative_payload = helpers[
        "daily_coach_async_persistence_safe_narrative_payload"
    ]

    assert (
        safe_narrative_payload(
            {
                "narrative_id": "narrative-1",
                "approved_text": "Approved.",
                "displayable": False,
                "public_safe": True,
            }
        )
        is None
    )
    assert (
        safe_narrative_payload(
            {
                "narrative_id": "narrative-1",
                "approved_text": "Approved.",
                "displayable": True,
                "public_safe": False,
            }
        )
        is None
    )

    safe = safe_narrative_payload(
        {
            "narrative_id": "narrative-1",
            "approved_text": "Approved.",
            "displayable": True,
            "public_safe": True,
            "raw_model_output": "forbidden",
        }
    )
    assert safe is not None
    assert safe["approved_text"] == "Approved."
    assert "raw_model_output" not in safe


def test_developer_mode_persistence_panel_is_developer_guarded():
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")

    assert "Developer Persistence Inspection: Daily Coach Async" in source
    assert "def render_daily_coach_async_persistence_inspection_panel" in source
    assert 'if not st.session_state.get("developer_mode", False):' in source
    assert "No provider is called" in source
    assert "normal Today behavior is unchanged" in source


def test_approved_narrative_can_be_seeded_for_inspection(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job("job-1")
    mark_async_job_displayable("job-1")

    narrative = create_approved_narrative(
        narrative_id="narrative-1",
        job_id="job-1",
        user_id=1,
        target_date="2026-06-22",
        context_hash="context-job-1",
        context_version="context-v1",
        approved_narrative_json={"narrative": "Approved."},
        approved_text="Approved.",
        reason_codes_json=["safe"],
        action_refs_json=["review_daily_coach"],
        validator_version="validator-v1",
        prompt_contract_version="prompt-v1",
        final_narrative_source="deterministic",
        displayable=True,
        public_safe=True,
    )

    assert narrative.displayable is True
    assert narrative.public_safe is True
    assert narrative.approved_text == "Approved."
