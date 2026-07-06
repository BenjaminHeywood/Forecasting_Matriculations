import json

import pandas as pd
from django.db.models import Max, Sum
from django.db.models.functions import Trim
from django.db import transaction
from django.shortcuts import render

from .forms import UploadCSVForm
from .model.predictor import score_dataframe
from .models import Forecast

ARMI_CATEGORIES = ["UG", "RPG", "TPG"]
ALL_FILTER_VALUE = "all"
FEE_STATUS_GROUPS = {
    "Channel Islands /Isle of Man": "Home Rest of UK (RUK)",
    "Home Rest of UK (RUK)": "Home Rest of UK (RUK)",
    "Overseas student charged home fees": "Other",
    "Query": "Other",
    "Unknown": "Other",
}


def get_distinct_trimmed_values(queryset, field_name):
    return list(
        queryset.annotate(value=Trim(field_name))
        .values_list("value", flat=True)
        .distinct()
        .order_by("value")
    )


def get_fee_status_filter_options(queryset):
    fee_statuses = get_distinct_trimmed_values(queryset, "fee_status")
    options = sorted({FEE_STATUS_GROUPS.get(status, status) for status in fee_statuses})

    return [
        {
            "value": option,
            "label": option,
        }
        for option in options
    ]


def get_fee_status_values_for_filter(selected_fee_status):
    grouped_values = [
        fee_status
        for fee_status, group in FEE_STATUS_GROUPS.items()
        if group == selected_fee_status
    ]

    return grouped_values or [selected_fee_status]


def apply_data_filters(request, queryset):
    selected_controlled = request.GET.get("controlled", ALL_FILTER_VALUE)
    selected_fee_status = request.GET.get("fee_status", ALL_FILTER_VALUE)

    controlled_options = get_distinct_trimmed_values(queryset, "controlled")
    fee_status_options = get_fee_status_filter_options(queryset)

    queryset = queryset.annotate(
        controlled_value=Trim("controlled"),
        fee_status_value=Trim("fee_status"),
    )

    if selected_controlled != ALL_FILTER_VALUE:
        queryset = queryset.filter(controlled_value=selected_controlled)

    if selected_fee_status != ALL_FILTER_VALUE:
        queryset = queryset.filter(
            fee_status_value__in=get_fee_status_values_for_filter(selected_fee_status)
        )

    filter_context = {
        "show_data_filters": True,
        "all_filter_value": ALL_FILTER_VALUE,
        "controlled_options": controlled_options,
        "fee_status_options": fee_status_options,
        "selected_controlled": selected_controlled,
        "selected_fee_status": selected_fee_status,
    }

    return queryset, filter_context


def build_armi_summary(queryset, row_field):
    rows = {}
    totals = {
        "label": "Total",
        "UG": 0,
        "RPG": 0,
        "TPG": 0,
    }

    summary_rows = (
        queryset.annotate(category=Trim("armi_category"))
        .values(row_field, "category")
        .annotate(expected_matriculations=Sum("expected_matriculations"))
        .order_by(row_field)
    )

    for summary_row in summary_rows:
        row_label = summary_row[row_field]
        category = summary_row["category"]

        if category not in ARMI_CATEGORIES:
            continue

        if row_label not in rows:
            rows[row_label] = {
                "label": row_label,
                "UG": 0,
                "RPG": 0,
                "TPG": 0,
            }

        rows[row_label][category] = summary_row["expected_matriculations"] or 0
        totals[category] += summary_row["expected_matriculations"] or 0

    return {
        "rows": rows.values(),
        "totals": totals,
    }


def home(request):
    latest_snapshot = Forecast.objects.aggregate(
        latest_snapshot=Max("snapshot_date")
    )["latest_snapshot"]

    latest_forecasts = Forecast.objects.none()
    filter_context = {
        "show_data_filters": False,
        "all_filter_value": ALL_FILTER_VALUE,
        "controlled_options": [],
        "fee_status_options": [],
        "selected_controlled": ALL_FILTER_VALUE,
        "selected_fee_status": ALL_FILTER_VALUE,
    }

    if latest_snapshot:
        latest_forecasts = Forecast.objects.filter(snapshot_date=latest_snapshot)
        latest_forecasts, filter_context = apply_data_filters(request, latest_forecasts)

    context = {
        "latest_snapshot": latest_snapshot,
        "armi_categories": ARMI_CATEGORIES,
        "faculty_summary": build_armi_summary(latest_forecasts, "faculty_name"),
        "region_summary": build_armi_summary(latest_forecasts, "region"),
    }
    context.update(filter_context)

    return render(request, "dataVis/home.html", context)


def forecast(request):
    forecasts, filter_context = apply_data_filters(request, Forecast.objects.all())

    summary_rows = (
        forecasts.annotate(category=Trim("armi_category"))
        .values("snapshot_date", "category")
        .annotate(expected_matriculations=Sum("expected_matriculations"))
        .order_by("snapshot_date", "category")
    )

    snapshot_dates = sorted(
        {
            summary_row["snapshot_date"].isoformat()
            for summary_row in summary_rows
            if summary_row["category"] in ARMI_CATEGORIES
        }
    )

    totals_by_category = {
        category: {snapshot_date: 0 for snapshot_date in snapshot_dates}
        for category in ARMI_CATEGORIES
    }

    for summary_row in summary_rows:
        category = summary_row["category"]

        if category not in ARMI_CATEGORIES:
            continue

        snapshot_date = summary_row["snapshot_date"].isoformat()
        totals_by_category[category][snapshot_date] = summary_row["expected_matriculations"] or 0

    chart_data = {
        "labels": snapshot_dates,
        "datasets": [
            {
                "label": category,
                "data": [
                    totals_by_category[category][snapshot_date]
                    for snapshot_date in snapshot_dates
                ],
            }
            for category in ARMI_CATEGORIES
        ],
    }

    return render(
        request,
        "dataVis/forecast.html",
        {
            "chart_data_json": json.dumps(chart_data),
            **filter_context,
        },
    )


def about(request):
    return render(request, "dataVis/about.html")


def upload(request):
    form = UploadCSVForm()
    table = None
    saved_count = None

    if request.method == "POST":
        form = UploadCSVForm(request.POST, request.FILES)

        if form.is_valid() and form.cleaned_data["file"]:
            uploaded_file = form.cleaned_data["file"]
            df = pd.read_csv(uploaded_file)
            summary, snapshot_date = score_dataframe(df)

            forecasts = [
                Forecast(
                    faculty_name=row["FACULTY_NAME"],
                    armi_category=row["ARMI_CATEGORY"],
                    region=row["REGION_GROUP"],
                    fee_status=row["FEE_STATUS_CAPS"],
                    controlled=str(row["Controlled"]),
                    total_applications=int(row["Applications"]),
                    avg_matric_prob=float(row["Average_Probability"]),
                    expected_matriculations=float(row["Expected_Matriculations"]),
                    snapshot_date=snapshot_date,
                )
                for _, row in summary.iterrows()
            ]

            with transaction.atomic():
                Forecast.objects.bulk_create(forecasts)

            saved_count = len(forecasts)
            table = summary.to_html(index=False, classes="table table-striped")

    return render(
        request,
        "dataVis/upload.html",
        {
            "form": form,
            "table": table,
            "saved_count": saved_count,
        },
    )
