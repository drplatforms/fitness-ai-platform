from __future__ import annotations

import inspect
import json
from pathlib import Path

import database
from services import daily_coach_human_voice_prompt_preview_service as preview_service
from services.daily_coach_human_voice_prompt_preview_service import (
    RAW_BACKEND_PAYLOAD_MARKER,
    build_daily_coach_human_voice_provider_input,
    load_human_voice_prompt_file,
    run_daily_coach_human_voice_prompt_preview,
)

CONTROLLED_PROMPT = "You are a health and fitness professional.\nWrite for the user.\n"

CONTROLLED_PAYLOAD = {
    "payload_version": "daily_coach_provider_preview_raw_data_payload_v1",
    "user_id": 102,
    "target_date": "2026-06-14",
    "generated_at": "2026-07-01T00:00:00+00:00",
    "developer_preview_only": True,
    "provider_call_allowed": False,
    "persistence_allowed": False,
    "product_surface_allowed": False,
    "source_snapshot_version": "daily_coach_intelligence_snapshot_v2",
    "source_services": ["daily_coach_intelligence_snapshot_service"],
    "source_data": {
        "recovery_intelligence": {"confidence": "Moderate"},
        "nutrition_trend_window": {"macro_gap": "protein_gap_known"},
    },
    "data_completeness": {"recovery_intelligence": "usable"},
    "source_data_gaps": [],
    "reason_codes": ["controlled_test_payload"],
    "limitations": [],
}

ANTI_CAGE_PHRASES = [
    "GOOD_STYLE_EXAMPLES",
    "BAD_STYLE_EXAMPLES",
    "EXAMPLE SHAPE ONLY",
    "FOCUS_TO_COPY_EXACTLY",
    "FACT_STRINGS_FOR_USED_FACTS",
    "DAILY_COACH_NARRATIVE_JSON_SCHEMA",
    "Sentence 1:",
    "Sentence 2:",
    "Final sentence:",
    "Return exactly these six keys",
]


def test_human_prompt_file_loads_without_rewrite(tmp_path: Path) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text(CONTROLLED_PROMPT, encoding="utf-8")

    assert load_human_voice_prompt_file(prompt_file) == CONTROLLED_PROMPT


def test_missing_prompt_file_raises_clear_error(tmp_path: Path) -> None:
    missing_prompt = tmp_path / "missing.md"

    try:
        load_human_voice_prompt_file(missing_prompt)
    except FileNotFoundError as exc:
        assert "Daily Coach human voice prompt file not found" in str(exc)
        assert str(missing_prompt) in str(exc)
    else:  # pragma: no cover - explicit failure path
        raise AssertionError("missing prompt file should raise FileNotFoundError")


def test_provider_input_passes_prompt_through_and_appends_raw_payload_json() -> None:
    provider_input = build_daily_coach_human_voice_provider_input(
        CONTROLLED_PROMPT,
        CONTROLLED_PAYLOAD,
    )

    assert provider_input.startswith(CONTROLLED_PROMPT)
    assert CONTROLLED_PROMPT in provider_input
    assert RAW_BACKEND_PAYLOAD_MARKER in provider_input
    assert (
        '"payload_version": "daily_coach_provider_preview_raw_data_payload_v1"'
        in provider_input
    )
    assert (
        '"source_snapshot_version": "daily_coach_intelligence_snapshot_v2"'
        in provider_input
    )
    assert provider_input.index(CONTROLLED_PROMPT) < provider_input.index(
        RAW_BACKEND_PAYLOAD_MARKER
    )


def test_provider_input_does_not_inject_old_caged_prompt_scaffolding() -> None:
    provider_input = build_daily_coach_human_voice_provider_input(
        CONTROLLED_PROMPT,
        CONTROLLED_PAYLOAD,
    )

    for phrase in ANTI_CAGE_PHRASES:
        assert phrase not in provider_input
    assert "Return JSON" not in provider_input
    assert "Return exactly" not in provider_input
    assert "exactly these" not in provider_input


def test_runtime_result_preserves_raw_model_output_without_parsing_or_scoring(
    tmp_path: Path,
) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text(CONTROLLED_PROMPT, encoding="utf-8")
    raw_output = "not-json and not scored: {coach-ish raw text}"

    result, provider_input = run_daily_coach_human_voice_prompt_preview(
        user_id=102,
        target_date="2026-06-14",
        model_name="fake-model",
        prompt_file=prompt_file,
        payload=CONTROLLED_PAYLOAD,
        provider_callable=lambda _: raw_output,
    )
    data = result.to_dict()

    assert data["raw_model_output"] == raw_output
    assert data["error_type"] is None
    assert data["error_message"] is None
    assert data["developer_preview_only"] is True
    assert data["provider_call_was_opt_in"] is True
    assert data["persistence_allowed"] is False
    assert data["product_surface_allowed"] is False
    assert data["normal_today_surface_allowed"] is False
    assert data["payload_version"] == CONTROLLED_PAYLOAD["payload_version"]
    assert (
        data["source_snapshot_version"] == CONTROLLED_PAYLOAD["source_snapshot_version"]
    )
    assert RAW_BACKEND_PAYLOAD_MARKER in provider_input


def test_runtime_service_can_use_injected_fake_provider_callable(
    tmp_path: Path,
) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text(CONTROLLED_PROMPT, encoding="utf-8")
    seen_inputs = []

    def fake_provider(provider_input: str) -> str:
        seen_inputs.append(provider_input)
        return "fake raw model output"

    result, _ = run_daily_coach_human_voice_prompt_preview(
        user_id=102,
        target_date="2026-06-14",
        model_name="fake-model",
        prompt_file=prompt_file,
        payload=CONTROLLED_PAYLOAD,
        provider_callable=fake_provider,
    )

    assert result.raw_model_output == "fake raw model output"
    assert len(seen_inputs) == 1
    assert CONTROLLED_PROMPT in seen_inputs[0]
    assert RAW_BACKEND_PAYLOAD_MARKER in seen_inputs[0]


def test_runtime_service_returns_error_metadata_on_provider_failure(
    tmp_path: Path,
) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text(CONTROLLED_PROMPT, encoding="utf-8")

    def failing_provider(_: str) -> str:
        raise RuntimeError("provider exploded")

    result, _ = run_daily_coach_human_voice_prompt_preview(
        user_id=102,
        target_date="2026-06-14",
        model_name="fake-model",
        prompt_file=prompt_file,
        payload=CONTROLLED_PAYLOAD,
        provider_callable=failing_provider,
    )

    assert result.raw_model_output == ""
    assert result.error_type == "RuntimeError"
    assert result.error_message == "provider exploded"
    assert result.developer_preview_only is True
    assert result.persistence_allowed is False
    assert result.product_surface_allowed is False


def test_runtime_service_does_not_mutate_database_when_given_built_payload(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    before = _database_table_counts()
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text(CONTROLLED_PROMPT, encoding="utf-8")

    run_daily_coach_human_voice_prompt_preview(
        user_id=102,
        target_date="2026-06-14",
        model_name="fake-model",
        prompt_file=prompt_file,
        payload=CONTROLLED_PAYLOAD,
        provider_callable=lambda _: "raw output",
    )

    assert _database_table_counts() == before


def test_runtime_service_does_not_import_old_caged_narrative_paths() -> None:
    source = inspect.getsource(preview_service).lower()

    assert "daily_coach_narrative_provider_service" not in source
    assert "daily_coach_narrative_validation_service" not in source
    assert "daily_coach_narrative_models" not in source
    assert "daily_coach_narrative_json_schema" not in source
    assert "good_style_examples" not in source
    assert "bad_style_examples" not in source
    assert "sentence 1:" not in source
    assert "sentence 2:" not in source
    assert "final sentence:" not in source
    assert "return exactly these six keys" not in source
    assert "crewai" not in source
    assert "openai" not in source


def test_call_ollama_uses_plain_generate_payload_without_json_schema(
    monkeypatch,
) -> None:
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return json.dumps({"response": "raw ollama text"}).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(preview_service.urllib.request, "urlopen", fake_urlopen)

    output = preview_service.call_ollama_human_voice_prompt_preview(
        provider_input="prompt plus payload",
        model_name="qwen2.5:3b",
        timeout_seconds=12,
        ollama_base_url="http://ollama.test:11434",
        temperature=0.8,
    )

    assert output == "raw ollama text"
    assert captured["url"] == "http://ollama.test:11434/api/generate"
    assert captured["timeout"] == 12
    assert captured["body"] == {
        "model": "qwen2.5:3b",
        "prompt": "prompt plus payload",
        "stream": False,
        "options": {"temperature": 0.8},
    }
    assert "format" not in captured["body"]


def _database_table_counts() -> dict[str, int]:
    conn = database.get_connection()
    cursor = conn.cursor()
    table_rows = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    counts = {}
    for row in table_rows:
        table_name = row[0]
        counts[table_name] = cursor.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()[0]
    conn.close()
    return counts
