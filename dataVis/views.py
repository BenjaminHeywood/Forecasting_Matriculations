import pandas as pd
from django.db import transaction
from django.shortcuts import render

from .forms import UploadCSVForm
from .model.predictor import score_dataframe
from .models import Forecast


def home(request):
    return render(request, "dataVis/home.html")


def forecast(request):
    return render(request, "dataVis/forecast.html")


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
