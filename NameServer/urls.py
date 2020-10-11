from django.urls import path
from . import views

urlpatterns = [
    path('NameServer/', views.send_request),
    path('connect/', views.connect_storage_server),
]