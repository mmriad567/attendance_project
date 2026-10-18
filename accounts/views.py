from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView

from .forms import LoginForm


class RoleLoginView(LoginView):
    """Login page with a Tailwind-styled form."""

    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class HomeView(LoginRequiredMixin, TemplateView):
    """Entry point after login; role-specific dashboards replace this later."""

    template_name = "accounts/dashboard.html"
