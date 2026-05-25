from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from pandera import Check

from catalog_engine import CatalogEngine
from schemas import DataValidationReport


REQUIRED_COLUMNS = {
    "product_category",
    "semantic_category",
    "preferred_category",
    "product_title",
    "product_type",
    "product_price",
    "rating",
    "key_ingredients",
    "product_tags",
    "target_concerns",
    "routine_step",
    "pregnancy_safe",
    "minimum_recommended_age",
}


CATALOG_SCHEMA = pa.DataFrameSchema(
    {
        "product_category": pa.Column(str, Check.isin(["skincare"]), coerce=True),
        "semantic_category": pa.Column(str, Check.isin(["skincare"]), coerce=True),
        "preferred_category": pa.Column(str, Check.isin(["skincare"]), coerce=True),
        "product_title": pa.Column(str, Check.str_length(min_value=1), coerce=True),
        "product_type": pa.Column(str, Check.str_length(min_value=1), coerce=True),
        "product_price": pa.Column(float, Check.ge(0), coerce=True),
        "rating": pa.Column(float, Check.in_range(0, 5), coerce=True),
        "pregnancy_safe": pa.Column(int, Check.isin([0, 1]), coerce=True),
        "minimum_recommended_age": pa.Column(int, Check.in_range(0, 90), coerce=True),
    },
    strict=False,
    coerce=True,
)


def validate_catalog_dataset(path=CatalogEngine.DEFAULT_DATASET):
    path = Path(path)
    errors = []
    warnings = []

    if not path.exists():
        return DataValidationReport(
            valid=False,
            dataset_path=str(path),
            errors=[f"Dataset does not exist: {path}"],
        )

    try:
        df = pd.read_csv(path)
    except (OSError, pd.errors.ParserError) as exc:
        return DataValidationReport(
            valid=False,
            dataset_path=str(path),
            errors=[f"Could not read dataset: {exc}"],
        )

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        errors.append("Missing required columns: " + ", ".join(sorted(missing)))

    if not errors:
        try:
            CATALOG_SCHEMA.validate(df, lazy=True)
        except pa.errors.SchemaErrors as exc:
            failures = exc.failure_cases.head(12)
            for _, row in failures.iterrows():
                column = row.get("column", "<dataframe>")
                check = row.get("check", "schema")
                failure = row.get("failure_case", "")
                errors.append(f"{column}: failed {check} with value {failure}")

    if not errors:
        warnings.extend(_domain_warnings(df))

    return DataValidationReport(
        valid=not errors,
        dataset_path=str(path),
        row_count=len(df),
        column_count=len(df.columns),
        errors=errors,
        warnings=warnings,
    )


def _domain_warnings(df):
    warnings = []

    if len(df) < 700:
        warnings.append("Dataset has fewer than 700 rows.")
    if len(df.columns) < 170:
        warnings.append("Dataset has fewer than 170 columns.")

    retinol_mask = df["key_ingredients"].fillna("").str.lower().str.contains("retinol|retinal|retinoid", regex=True)
    if retinol_mask.any():
        retinol_rows = df[retinol_mask]
        if "usage_time" in retinol_rows.columns:
            unsafe_time = retinol_rows[~retinol_rows["usage_time"].fillna("").str.lower().isin(["night", "pm"])]
            if not unsafe_time.empty:
                warnings.append("Some retinoid products are not marked night-only.")
        if "sunscreen_required_after_use" in retinol_rows.columns:
            no_spf_flag = retinol_rows[retinol_rows["sunscreen_required_after_use"].fillna(0).astype(int) != 1]
            if not no_spf_flag.empty:
                warnings.append("Some retinoid products do not require follow-up sunscreen.")

    pregnancy_unsafe = df[
        (df["pregnancy_safe"].fillna(0).astype(int) == 1)
        & df["key_ingredients"].fillna("").str.lower().str.contains("retinol|retinal|retinoid", regex=True)
    ]
    if not pregnancy_unsafe.empty:
        warnings.append("Some pregnancy-safe rows contain retinoid ingredients.")

    return warnings
