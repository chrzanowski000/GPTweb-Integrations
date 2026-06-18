from pydantic import BaseModel, field_validator


class Ingredient(BaseModel):
    ingredient: str
    pct: float


class Formula(BaseModel):
    formula_name: str
    version: str = "1"
    description: str = ""
    ingredients: list[Ingredient]

    @field_validator("ingredients")
    @classmethod
    def must_have_at_least_one(cls, v: list[Ingredient]) -> list[Ingredient]:
        if not v:
            raise ValueError("ingredients list must not be empty")
        return v

    @field_validator("formula_name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("formula_name must not be blank")
        return v


def validate_formula(raw: dict) -> Formula:
    """Parse and validate a raw dict from LM Studio into a Formula.

    Raises ValueError if is_formula is False.
    Raises pydantic.ValidationError if required fields are missing or invalid.
    """
    if not raw.get("is_formula", False):
        raise ValueError("LM Studio indicated no formula was found in the conversation")
    return Formula.model_validate(raw)


if __name__ == "__main__":
    # Standalone verification
    from pydantic import ValidationError

    cases = [
        # Valid
        {
            "is_formula": True,
            "formula_name": "Forest Chypre",
            "version": "2",
            "ingredients": [
                {"ingredient": "Iso E Super", "pct": 40},
                {"ingredient": "Hedione", "pct": 25},
            ],
        },
        # No formula found
        {"is_formula": False, "formula_name": "", "version": "", "ingredients": []},
        # Missing formula_name
        {"is_formula": True, "ingredients": [{"ingredient": "X", "pct": 10}]},
        # Empty ingredients
        {"is_formula": True, "formula_name": "Test", "ingredients": []},
        # Non-numeric pct
        {
            "is_formula": True,
            "formula_name": "Test",
            "ingredients": [{"ingredient": "X", "pct": "not-a-number"}],
        },
    ]

    for i, case in enumerate(cases, 1):
        try:
            formula = validate_formula(case)
            print(f"Case {i}: VALID — {formula.formula_name}, {len(formula.ingredients)} ingredient(s)")
        except (ValueError, ValidationError) as exc:
            print(f"Case {i}: INVALID — {exc}")
