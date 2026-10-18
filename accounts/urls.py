from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import HomeView, RoleLoginView

app_name = "accounts"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("login/", RoleLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
