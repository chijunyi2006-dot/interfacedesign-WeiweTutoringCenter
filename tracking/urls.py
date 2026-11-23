from django.urls import path

from . import views

urlpatterns = [
    path("api/events/", views.receive_event, name="receive_event"),
    path("api/feedback/", views.receive_feedback, name="receive_feedback"),
]
