import pandas as pd
 
 
class SchemaValidationError(Exception):
    """Raised when an uploaded CSV fails schema validation."""
 
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))
 
 
# ---------------------------------------------------------------------------
# String columns
# ---------------------------------------------------------------------------
READ_CSV_DTYPES = {
    "Name": str,
    "STUDENT_ID": str,
    "ENTRY_YEAR": str,
    "APF_SEQ_NUM": str,
    "CAP_SEQ_NUM": str,
    "CAP_PREF": str,
}
 
 
# ---------------------------------------------------------------------------
# Categorical, non-null columns
# ---------------------------------------------------------------------------
REQUIRED_STRING_COLS = [
    "Name",
    "STUDENT_ID",
    "FACULTY_NAME",
    "APPLICANT_STATUS_NAME",
    "APPLICANT_CODE_OF_ATTENDANCE",
    "COURSE_LEVEL",
    "COURSE_TYPE",
    "COURSE_TYPE_NAME",
    "MAS_COURSE_TITLE",
    "GENDER",
    "ARMI_CATEGORY",
    "Kind",
]
 
# ---------------------------------------------------------------------------
# Categorical, can be null
# ---------------------------------------------------------------------------
OPTIONAL_STRING_COLS = [
    "DISCIPLINE",
    "ENTRY_YEAR",
    "DOMICILE",
    "REGION",
    "ETHNICITY_GRP",
    "FEE_STATUS_CAPS",
    "ENTRY_MONTH_NAME",
    "CLEARING_CYCLE",
    "MAS_COURSE_GROUP_NAME",
    "DECISION_RESPONSE_CODE",
    "ACCEPTANCE_STATUS_NAME",
    "NON_ACADEMIC_CONDITIONS",
    "FUNDING_CATAGORY_CODE",
    "DEFERRAL_INDICATOR",
    "CAP_PREF",
    "SEMESTER",
    "STAGE1DECISION",
    "STAGE1RESPONSE",
    "STAGE2DECISION",
    "STAGE2RESPONSE",
    "STAGE3DECISION",
    "STAGE3RESPONSE",
    "WITHDRAWAL",
    "APF_SEQ_NUM",
    "CAP_SEQ_NUM",
    "Controlled",
    "CONTEXTUAL_DATA_SCORE"
]
 
# ---------------------------------------------------------------------------
# Whole-number columns, with (min, max) range checks.
# ---------------------------------------------------------------------------
INT_COLS = {
    "STUDENT_AGE_ON_ENTRY": (0, 100),
    "UCAS_CYCLE": (2000, 2100),
    "MATRICULATIONS": (0, 1),  #
}

NULLABLE_INT_COLS = {"STUDENT_AGE_ON_ENTRY", "UCAS_CYCLE"}
 
# ---------------------------------------------------------------------------
# Date columns, all in dd/mm/yyyy format based on the sample data.
# The two listed as required must be present on every row; the rest are
# nullable because in-flight applications won't have later stage dates yet.
# ---------------------------------------------------------------------------
DATE_COLS = [
    "CREATED_DATE",
    "STAGE1DECISIONDATE",
    "STAGE1RESPONSEDATE",
    "STAGE2DECISIONDATE",
    "STAGE2RESPONSEDATE",
    "STAGE3DECISIONDATE",
    "STAGE3RESPONSEDATE",
    "Snapshot Date",
]
REQUIRED_DATE_COLS = {"CREATED_DATE", "Snapshot Date"}
 
ALL_EXPECTED_COLUMNS = (
    REQUIRED_STRING_COLS
    + OPTIONAL_STRING_COLS
    + list(INT_COLS.keys())
    + DATE_COLS
)
 
 
def validate_upload_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate `df` against the expected upload schema.
 
    Returns a copy of the DataFrame with int/date columns coerced to the
    right dtype on success.
    Raises SchemaValidationError with a list of human-readable messages
    on failure (missing columns, bad types, out-of-range values).
    """
    errors: list[str] = []
 
    # 1. Missing columns 
    missing = [col for col in ALL_EXPECTED_COLUMNS if col not in df.columns]
    if missing:
        raise SchemaValidationError(
            [f"Missing required column(s): {', '.join(missing)}"]
        )
 
    df = df.copy()
 
    # 2. Required strings: must not be null/blank.
    for col in REQUIRED_STRING_COLS:
        blank_mask = df[col].isna() | (df[col].astype(str).str.strip() == "")
        if blank_mask.any():
            bad_rows = df.index[blank_mask].tolist()
            errors.append(
                f"Column '{col}' has empty values in row(s): "
                f"{bad_rows[:5]}{'...' if len(bad_rows) > 5 else ''}"
            )
 
    # 3. Integer columns: coerce to numeric, check range.
    for col, (min_val, max_val) in INT_COLS.items():
        coerced = pd.to_numeric(df[col], errors="coerce")

        originally_blank = df[col].isna() | (df[col].astype(str).str.strip() == "")
        if col in NULLABLE_INT_COLS:
            bad_mask = coerced.isna() & ~originally_blank
        else:
            bad_mask = coerced.isna()

        if bad_mask.any():
            bad_rows = df.index[bad_mask].tolist()
            errors.append(
                f"Column '{col}' must be a whole number "
                f"(bad row(s): {bad_rows[:5]}{'...' if len(bad_rows) > 5 else ''})"
            )
        else:
            out_of_range = pd.Series(False, index=df.index)
            if min_val is not None:
                out_of_range |= coerced < min_val
            if max_val is not None:
                out_of_range |= coerced > max_val
            out_of_range &= ~coerced.isna()
            if out_of_range.any():
                bad_rows = df.index[out_of_range].tolist()
                errors.append(
                    f"Column '{col}' has values outside the expected range "
                    f"({min_val}-{max_val}) in row(s): "
                    f"{bad_rows[:5]}{'...' if len(bad_rows) > 5 else ''}"
                )
            df[col] = coerced.astype("Int64")  
    # 4. Date columns: parse as dd/mm/yyyy.
    for col in DATE_COLS:
        parsed = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
        # A parse failure only counts as an error if the original value
        # wasn't already blank/null (blanks are fine for optional dates).
        originally_blank = df[col].isna() | (df[col].astype(str).str.strip() == "")
        bad_mask = parsed.isna() & ~originally_blank
        if bad_mask.any():
            bad_rows = df.index[bad_mask].tolist()
            errors.append(
                f"Column '{col}' has values that aren't valid dd/mm/yyyy dates "
                f"(bad row(s): {bad_rows[:5]}{'...' if len(bad_rows) > 5 else ''})"
            )
        if col in REQUIRED_DATE_COLS and originally_blank.any():
            bad_rows = df.index[originally_blank].tolist()
            errors.append(
                f"Column '{col}' is required but blank in row(s): "
                f"{bad_rows[:5]}{'...' if len(bad_rows) > 5 else ''}"
            )
        df[col] = parsed
 
    if errors:
        raise SchemaValidationError(errors)
 
    return df
 
