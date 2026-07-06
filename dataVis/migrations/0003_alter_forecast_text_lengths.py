# Generated manually on 2026-07-06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dataVis", "0002_remove_forecast_entry_year_remove_forecast_semester_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="forecast",
            name="faculty_name",
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name="forecast",
            name="armi_category",
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name="forecast",
            name="fee_status",
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name="forecast",
            name="controlled",
            field=models.CharField(max_length=20),
        ),
    ]
