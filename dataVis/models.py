from django.db import models

class Forecast(models.Model):
    
    faculty_name = models.CharField(max_length=100)
    armi_category = models.CharField(max_length=50)
    region = models.CharField(max_length=100)
    fee_status = models.CharField(max_length=20)
    controlled = models.CharField(max_length=20)
    total_applications = models.IntegerField()
    avg_matric_prob = models.FloatField()
    expected_matriculations = models.FloatField()
    snapshot_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    forecast_model = models.ForeignKey(
        "ForecastModel",
        on_delete=models.PROTECT,
        related_name="forecasts",
    )
    
    def __str__(self):
        return (
            f"{self.snapshot_date} | "
            f"{self.faculty_name} |"
            f"{self.armi_category} | "
            f"{self.region} "
            f"{self.expected_matriculations:.1f}"
        )

class ForecastModel(models.Model):
    
    name = models.CharField(max_length=50)
    version = models.CharField(max_length = 15)
    algorithm = models.CharField(max_length=50)
    calibration = models.CharField(max_length = 50)
    training_years = models.CharField(max_length = 25)
    training_semesters = models.CharField(max_length=25)
    test_period = models.CharField(max_length= 25)
    roc_auc = models.FloatField()
    brier = models.FloatField()
    created = models.DateField()

    def __str__(self):
        return (
            f"{self.name} v{self.version} "
            f"[{self.training_years}]"

        )
