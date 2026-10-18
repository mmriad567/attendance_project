"""URLConf with guarded views, used only by the mixin tests."""

from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import View

from accounts.mixins import RoleRequiredMixin
from accounts.models import Role


class AdminOnlyView(RoleRequiredMixin, View):
    allowed_roles = (Role.ADMIN,)

    def get(self, request):
        return HttpResponse("admin-ok")


class TeacherOrAdminView(RoleRequiredMixin, View):
    allowed_roles = (Role.TEACHER, Role.ADMIN)

    def get(self, request):
        return HttpResponse("teacher-ok")


class AnyRoleView(RoleRequiredMixin, View):
    allowed_roles = ()

    def get(self, request):
        return HttpResponse("any-ok")


urlpatterns = [
    path("accounts/", include("accounts.urls")),
    path("admin-only/", AdminOnlyView.as_view(), name="admin_only"),
    path("teacher/", TeacherOrAdminView.as_view(), name="teacher_only"),
    path("any/", AnyRoleView.as_view(), name="any_role"),
]
