from django.urls import path
from django.contrib.auth import views as auth_views

from .views import register

urlpatterns = [
    # Login page
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html"
        ),
        name="login",
    ),

    # Logout
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    # Registration page
    path(
        "register/",
        register,
        name="register",
    ),
]