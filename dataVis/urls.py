from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='dataVis-home'),
    path('about/', views.about, name='dataVis-about'),
]