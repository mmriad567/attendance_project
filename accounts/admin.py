from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    AcademicSession,
    Department,
    StudentProfile,
    TeacherProfile,
    User,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Attendance profile", {"fields": ("role", "phone", "avatar")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Attendance profile", {"fields": ("role", "phone")}),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "short_name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_current")
    list_filter = ("is_current",)
    search_fields = ("name",)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "roll_no",
        "user",
        "department",
        "session",
        "shift",
        "section",
        "current_semester",
        "status",
    )
    list_filter = ("department", "session", "shift", "status")
    search_fields = ("roll_no", "registration_no", "user__username", "user__first_name")
    autocomplete_fields = ("user",)


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "user", "department", "designation")
    list_filter = ("department", "designation")
    search_fields = ("employee_id", "user__username", "user__first_name")
    autocomplete_fields = ("user",)
