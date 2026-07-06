import pandas as pd
import numpy as np

major_countries = [
    "China", "Nigeria", "India", "Pakistan",
    "United States of America", "Ghana", "Canada",
    "Indonesia", "Malaysia", "France"
]

def region_group(region):
    if pd.isna(region):
        return "Unknown"
    if str(region).startswith("Scotland"):
        return "Scotland"
    if str(region).startswith("England"):
        return "England"
    if region in ["Wales", "Northern Ireland"]:
        return region
    if region in ["Sub-Saharan Africa", "Africa"]:
        return "Africa"
    if region in ["South Asia", "East Asia", "South East Asia", "South East Asia (ASEAN)", "Central Asia"]:
        return "Asia"
    if region in ["European Union (EU)", "Europe (European Union)", "Europe excluding European Union"]:
        return "Europe"
    if region == "Americas":
        return "Americas"
    if region == "Australasia":
        return "Australasia"
    return region


def process_df(df):

    # Create App ID
    df["APPLICATION_ID"] = (
        df["STUDENT_ID"].astype(str)
        + "_"
        + df["APF_SEQ_NUM"].astype(str)
        + "_"
        + df["CAP_SEQ_NUM"].astype(str)
    )

    matriculated_ids = set(
        df.loc[
            df["MATRICULATIONS"] == 1,
            "APPLICATION_ID"
        ]
    )

    df = df.drop(columns=[
    "STUDENT_ID", "APF_SEQ_NUM", "CAP_SEQ_NUM",  # used only for APPLICATION_ID
    "MATRICULATIONS",                               # used only for matriculated_ids
    "Kind", "Name",                                 # never used
    "COURSE_LEVEL", "COURSE_TYPE", "COURSE_TYPE_NAME",  # never used
    "CAP_PREF",                                     # never used
    "ACCEPTANCE_STATUS_NAME",                       # never used
    "ETHNICITY_GRP",                                # never used
])

    df["MATRICULATED"] = (
        df["APPLICATION_ID"].isin(matriculated_ids)
    ).astype(int)    

    # Parse Snapshot Date first, before any date calculations
    df["Snapshot Date"] = pd.to_datetime(df["Snapshot Date"], dayfirst=True)

    df["CREATED_DATE"] = pd.to_datetime(df["CREATED_DATE"], dayfirst=True, errors="coerce")

    df["days_since_created"] = (df["Snapshot Date"] - df["CREATED_DATE"]).dt.days

    # Start date lookup
    start_dates_df = pd.DataFrame([
        {"SEMESTER": "Semester 1", "ENTRY_YEAR": "2025/6", "start_date": pd.Timestamp("2025-09-22")},
        {"SEMESTER": "Semester 2", "ENTRY_YEAR": "2025/6", "start_date": pd.Timestamp("2026-01-19")},
        {"SEMESTER": "Semester 1", "ENTRY_YEAR": "2024/5", "start_date": pd.Timestamp("2024-09-16")},
        {"SEMESTER": "Semester 2", "ENTRY_YEAR": "2024/5", "start_date": pd.Timestamp("2025-01-20")},
        {"SEMESTER": "Semester 1", "ENTRY_YEAR": "2026/7", "start_date": pd.Timestamp("2026-09-22")},
        {"SEMESTER": "Semester 2", "ENTRY_YEAR": "2026/7", "start_date": pd.Timestamp("2027-01-19")},
    ])

    df = df.merge(start_dates_df, on=["SEMESTER", "ENTRY_YEAR"], how="left")

    df["days_before_start"] = (df["start_date"] - df["Snapshot Date"]).dt.days
    df["snapshot_week"] = df["days_before_start"] // 7

    # Drop rows more than a month after start
    df = df[df["days_before_start"] >= -30]
    df = df.drop(columns=["start_date"])

    # Stage decision dates
    date_cols = [
        "STAGE1DECISIONDATE",
        "STAGE2DECISIONDATE",
        "STAGE3DECISIONDATE"
    ]

    for col in date_cols:
        df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
        stage = col.replace("DECISIONDATE", "")
        df[f"days_since_{stage.lower()}"] = (df["Snapshot Date"] - df[col]).dt.days
        df[f"{stage.lower()}_missing"] = df[col].isna().astype(int)

    #Filling blank values

    df["STAGE1DECISION"] = df["STAGE1DECISION"].fillna("No Decision")
    df["STAGE1RESPONSE"] = df["STAGE1RESPONSE"].fillna("No Response")
    df["STAGE2DECISION"] = df["STAGE2DECISION"].fillna("No Decision")
    df["STAGE2RESPONSE"] = df["STAGE2RESPONSE"].fillna("No Response")
    df["STAGE3DECISION"] = df["STAGE3DECISION"].fillna("No Decision")
    df["STAGE3RESPONSE"] = df["STAGE3RESPONSE"].fillna("No Response")

    df["DISCIPLINE"] = df["DISCIPLINE"].fillna("Unknown")
    df["FEE_STATUS_CAPS"] = df["FEE_STATUS_CAPS"].fillna("Unknown")
    df["MAS_COURSE_GROUP_NAME"] = df["MAS_COURSE_GROUP_NAME"].fillna("Unknown")

    df["DOMICILE"] = df["DOMICILE"].fillna("Unknown")
    df["REGION"] = df["REGION"].fillna("Unknown")
    df["CLEARING_CYCLE"] = df["CLEARING_CYCLE"].fillna("Unknown")

    df["DECISION_RESPONSE_CODE"] = df["DECISION_RESPONSE_CODE"].fillna("No Decision")
    df["NON_ACADEMIC_CONDITIONS"] = df["NON_ACADEMIC_CONDITIONS"].fillna("No NAC")

    df["UCAS_CYCLE"] = df["UCAS_CYCLE"].astype(str).replace("nan", "Unknown")
    df["CONTEXTUAL_DATA_SCORE"] = df["CONTEXTUAL_DATA_SCORE"].fillna("No Contextual Score")
    df["DEFERRAL_INDICATOR"] = df["DEFERRAL_INDICATOR"].fillna("Not Deferred")
    df["FUNDING_CATAGORY_CODE"] = df["FUNDING_CATAGORY_CODE"].fillna("No Funding Catagory Code")

    df["AGE_ON_ENTRY"] = pd.to_numeric(df["STUDENT_AGE_ON_ENTRY"], errors="coerce")
    df["AGE_ON_ENTRY"] = df["AGE_ON_ENTRY"].fillna(df["AGE_ON_ENTRY"].median())
    
    df["AGE_MISSING"] = (
        df["STUDENT_AGE_ON_ENTRY"]
        .isna()
        .astype(int)
    )

    df["WITHDRAWN"] = (
        df["WITHDRAWAL"].notna()
    ).astype(int)

    df["days_since_stage1"] = (
        df["days_since_stage1"].fillna(-1)
    )

    df["days_since_stage2"] = (
        df["days_since_stage2"].fillna(-1)
    )

    df["days_since_stage3"] = (
        df["days_since_stage3"].fillna(-1)
    )

    # Vectorised domicile grouping
    conditions = [
        df["DOMICILE"].isin(major_countries),
        df["REGION"].str.startswith("Scotland", na=False),
        df["REGION"].str.startswith("England", na=False),
        df["REGION"] == "Wales",
        df["REGION"] == "Northern Ireland",
        df["REGION"] == "Republic of Ireland (Eire)",
        df["REGION"].isin(["Middle East", "Middle East/North Africa (MENA)"]),
        df["REGION"].isin(["Sub-Saharan Africa", "Africa"]),
        df["REGION"].isin(["South Asia", "East Asia", "South East Asia", "South East Asia (ASEAN)", "Central Asia"]),
        df["REGION"].isin(["European Union (EU)", "Europe (European Union)", "Europe excluding European Union"]),
        df["REGION"] == "Americas",
        df["REGION"] == "Australasia",
        df["REGION"] == "Channel Islands & Isle of Man",
        df["REGION"] == "British Overseas Territory",
        df["REGION"] == "UK - not known",
    ]

    choices = [
        df["DOMICILE"],       # keeps the actual country name for major countries
        "Scotland", "England", "Wales", "Northern Ireland",
        "Republic of Ireland",
        "Other MENA",
        "Other Africa",
        "Other Asia",
        "Other Europe",
        "Other Americas",
        "Other Oceania",
        "Channel Islands & Isle of Man",
        "British Overseas Territory",
        "United Kingdom",
    ]

    df["DOMICILE_GROUP"] = np.select(conditions, choices, default="Unknown")
    region_conditions = [
        df["REGION"].str.startswith("Scotland", na=False),
        df["REGION"].str.startswith("England", na=False),
        df["REGION"].isin(["Wales", "Northern Ireland"]),
        df["REGION"].isin(["Sub-Saharan Africa", "Africa"]),
        df["REGION"].isin(["South Asia", "East Asia", "South East Asia", "South East Asia (ASEAN)", "Central Asia"]),
        df["REGION"].isin(["European Union (EU)", "Europe (European Union)", "Europe excluding European Union"]),
        df["REGION"] == "Americas",
        df["REGION"] == "Australasia",
    ]

    region_choices = [
        "Scotland", "England",
        df["REGION"],   # keeps Wales/Northern Ireland as-is
        "Africa", "Asia", "Europe", "Americas", "Australasia",
    ]

    df["REGION_GROUP"] = np.select(region_conditions, region_choices, default="Unknown")
    
    
    df = df.drop(columns=[
        "DOMICILE", "REGION",
        "MAS_COURSE_TITLE",
        "CONTEXTUAL_DATA_SCORE",
        "CREATED_DATE",              # now safe to drop
        "STAGE1DECISIONDATE", "STAGE1RESPONSEDATE",
        "STAGE2DECISIONDATE", "STAGE2RESPONSEDATE",
        "STAGE3RESPONSEDATE", "STAGE3DECISIONDATE",
        "WITHDRAWAL",
        "Snapshot Date",
        "STUDENT_AGE_ON_ENTRY",
    ])        
    return df