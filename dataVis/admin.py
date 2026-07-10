from django.contrib import admin
from .models import Forecast, ForecastModel

admin.site.register(Forecast)
admin.site.register(ForecastModel)
