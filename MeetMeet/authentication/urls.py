from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.Register),
    path("email-verify/", views.verifyEmail, name='email-verify'),
]
