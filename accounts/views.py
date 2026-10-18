from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views import View

from .forms import LoginForm


class RoleLoginView(LoginView):
    """Login page with a Tailwind-styled form."""

    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class HomeView(LoginRequiredMixin, View):
    """Send each role to its own landing page."""

    def get(self, request):
        if request.user.is_teacher:
            return redirect("attendance:dashboard")
        if request.user.is_student:
            return redirect("students:dashboard")
        return render(request, "accounts/dashboard.html")
