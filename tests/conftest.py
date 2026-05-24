import pytest


@pytest.fixture(autouse=True)
def fake_crewai_recommendation_provider(monkeypatch):
    """Prevent tests from calling the live CrewAI/Ollama recommendation path."""

    import services.recommendation_engine_service as recommendation_engine_service

    def fake_generate_crewai_candidate_action_plan_json(context):
        return recommendation_engine_service.generate_candidate_action_plan_json(
            context
        )

    def fake_build_crewai_approved_action_plan(health_state):
        return recommendation_engine_service.build_approved_action_plan(
            health_state,
            candidate_provider=(
                recommendation_engine_service.generate_crewai_candidate_action_plan_json
            ),
        )

    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        fake_generate_crewai_candidate_action_plan_json,
    )

    monkeypatch.setattr(
        recommendation_engine_service,
        "build_crewai_approved_action_plan",
        fake_build_crewai_approved_action_plan,
    )

    def fake_build_configured_approved_action_plan(health_state):
        return recommendation_engine_service.build_configured_approved_action_plan(
            health_state
        )

    import api.routes.recommendations as recommendation_routes

    monkeypatch.setattr(
        recommendation_routes,
        "build_configured_approved_action_plan",
        fake_build_configured_approved_action_plan,
        raising=False,
    )

    try:
        import services.coordinator_service as coordinator_service
    except ImportError:
        return

    monkeypatch.setattr(
        coordinator_service,
        "build_configured_approved_action_plan",
        fake_build_configured_approved_action_plan,
        raising=False,
    )
    monkeypatch.setattr(
        coordinator_service,
        "build_crewai_approved_action_plan",
        fake_build_crewai_approved_action_plan,
        raising=False,
    )
