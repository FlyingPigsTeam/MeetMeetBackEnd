from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    path("register/", views.Register),
    path("email-verify/", views.verifyEmail, name='email-verify'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("login/", views.login),
    path("reset-password/", views.ResetPassword, name="reset-password"),
    path("forget-password/", views.ForgetPassword),
]
