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
    
    def __str__(self):
        return f"{self.armi_category} - {self.region} - {self.faculty_name} ({self.expected_matriculations})"
