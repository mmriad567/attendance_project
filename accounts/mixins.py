from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin):
    """Restrict a class-based view to users whose role is in ``allowed_roles``.

    Unauthenticated users are redirected to the login page (via
    ``LoginRequiredMixin``); authenticated users without a matching role get a
    ``403 PermissionDenied``.
    """

    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.allowed_roles and request.user.role not in self.allowed_roles:
            raise PermissionDenied("You do not have access to this page.")
        return super().dispatch(request, *args, **kwargs)
