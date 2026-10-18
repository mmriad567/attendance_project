from django.contrib import admin

from .models import Enrollment, Subject, SubjectOffering


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "department", "semester", "subject_type", "credit", "is_active")
    list_filter = ("department", "semester", "subject_type", "is_active")
    search_fields = ("code", "name")


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    autocomplete_fields = ("student",)


@admin.register(SubjectOffering)
class SubjectOfferingAdmin(admin.ModelAdmin):
    list_display = ("subject", "session", "semester", "shift", "section", "teacher")
    list_filter = ("session", "semester", "shift", "subject__department")
    search_fields = ("subject__code", "subject__name", "teacher__username")
    autocomplete_fields = ("subject", "session", "teacher")
    inlines = [EnrollmentInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "offering", "is_active", "enrolled_at")
    list_filter = ("is_active", "offering__session", "offering__subject__department")
    search_fields = ("student__roll_no", "offering__subject__code")
    autocomplete_fields = ("student", "offering")
