from django.db import models

class Forecast(models.Model):
    entry_year = models.CharField(max_length = 6)
    semester = models.CharField(max_length = 1)
    armi_category = models.CharField(max_length=10)
    region = models.CharField(max_length=100)
    total_applications = models.IntegerField()
    avg_matric_prob = models.FloatField()
    expected_matriculations = models.FloatField()
    week_num = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    controlled = models.CharField(max_length = 1)

    def __str__(self):
        return f"{self.armi_category} - {self.region} ({self.expected_matriculations})"