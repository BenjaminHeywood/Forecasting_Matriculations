import joblib
import pandas as pd
from pathlib import Path

from ..src.preprocessing import process_df

MODEL_PATH = Path(__file__).resolve().parent / "matriculation_model.joblib"
model = joblib.load(MODEL_PATH)


def score_dataframe(df):

    snapshot_date = pd.to_datetime(df["Snapshot Date"].iloc[0], dayfirst=True).date()

    df = process_df(df)

    X = df.drop(
        columns=[
            "APPLICATION_ID",
            "MATRICULATED",
            "ENTRY_YEAR"
        ],
        errors="ignore"
    )

    df["MATRIC_PROB"] = model.predict_proba(X)[:,1]

    summary = (
        df.groupby(
            [
                "FACULTY_NAME",
                "ARMI_CATEGORY",
                "FEE_STATUS_CAPS",
                "Controlled",
                "REGION_GROUP",
            ]
        )
        .agg(
            Applications=("MATRIC_PROB","size"),
            Expected_Matriculations=("MATRIC_PROB","sum"),
            Average_Probability=("MATRIC_PROB","mean")
        )
        .reset_index()
    )

    return summary, snapshot_date
