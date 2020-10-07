from django.urls import path
from . import views

urlpatterns = [
    path('NameServer/', views.send_request),
]