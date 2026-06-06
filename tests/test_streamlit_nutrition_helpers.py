from __future__ import annotations

import ast
from pathlib import Path

STREAMLIT_HELPER_NAMES = {
    "humanize_label",
    "nutrition_public_text",
    "nutrition_amount_parts",
    "format_nutrition_value",
    "first_present_value",
    "nutrition_metric_value",
    "target_comparison_value",
    "macro_comparison_from_summary",
    "comparison_is_displayable",
    "display_nutrition_actuals",
    "nutrition_comparison_rows_from_summary",
}


def load_streamlit_nutrition_helpers() -> dict:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    helper_nodes = [
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name in STREAMLIT_HELPER_NAMES
    ]
    namespace: dict = {}
    compiled = ast.Module(body=helper_nodes, type_ignores=[])
    ast.fix_missing_locations(compiled)
    exec(compile(compiled, "ui/streamlit_app.py", "exec"), namespace)
    return namespace


class FakeColumn:
    def __init__(self) -> None:
        self.metrics: list[tuple[str, str]] = []

    def metric(self, label: str, value: str) -> None:
        self.metrics.append((label, value))


class FakeStreamlit:
    def __init__(self) -> None:
        self.columns_created = [FakeColumn() for _ in range(4)]
        self.captions: list[str] = []
        self.markdown_calls: list[str] = []

    def markdown(self, text: str) -> None:
        self.markdown_calls.append(text)

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def columns(self, count: int) -> list[FakeColumn]:
        assert count == 4
        return self.columns_created


def test_display_nutrition_actuals_accepts_logged_actual_keys() -> None:
    helpers = load_streamlit_nutrition_helpers()
    fake_st = FakeStreamlit()
    helpers["st"] = fake_st

    helpers["display_nutrition_actuals"](
        {
            "logged_calories": 2095.4,
            "logged_protein": 128.8,
            "logged_carbs": 306.8,
            "logged_fat": 137.6,
        },
        {"logged_meal_count": 11, "entry_count": 11},
    )

    metrics = [column.metrics[0] for column in fake_st.columns_created]
    assert metrics == [
        ("Calories", "2095.4 kcal"),
        ("Protein", "128.8 g"),
        ("Carbs", "306.8 g"),
        ("Fat", "137.6 g"),
    ]
    assert fake_st.captions == ["Logged today: 11 meals / 11 entries"]


def test_macro_comparison_from_summary_accepts_comparisons_dict_shape() -> None:
    helpers = load_streamlit_nutrition_helpers()
    comparison = {"nutrient": "protein", "actual": 128.8, "target_min": 150.0}
    summary = {"comparisons": {"protein": comparison}}

    assert (
        helpers["macro_comparison_from_summary"](
            summary,
            ["protein", "protein_g", "protein_grams"],
        )
        == comparison
    )


def test_target_vs_actual_rows_render_from_accepted_api_shape() -> None:
    helpers = load_streamlit_nutrition_helpers()
    summary = {
        "comparisons": {
            "protein": {
                "nutrient": "protein",
                "actual": 128.8,
                "target_min": 150.0,
                "target_max": 190.0,
                "delta_min": -21.2,
                "delta_max": -61.2,
                "target_status": "below_target",
                "comparison_available": True,
                "confidence": "Low",
            },
            "calories": {
                "nutrient": "calories",
                "actual": 2095.4,
                "target_min": 2600.0,
                "target_max": 2800.0,
                "target_status": "unavailable",
                "comparison_available": False,
                "limitations": [
                    "Calories are not compared because logging is not complete enough."
                ],
            },
        }
    }

    rows = helpers["nutrition_comparison_rows_from_summary"](summary)

    assert rows[0] == {
        "Nutrient": "Calories",
        "Logged": "2095.4 kcal",
        "Target": "Limited",
        "Difference": "Limited",
        "Status": "Calories Are Not Compared Because Logging Is Not Complete Enough.",
    }
    assert rows[1]["Nutrient"] == "Protein"
    assert rows[1]["Logged"] == "128.8 g"
    assert rows[1]["Target"] == "150–190 g"
    assert rows[1]["Status"] == "Below Target."
