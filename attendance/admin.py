from django.contrib import admin

from .models import AttendanceRecord, ClassSession


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    autocomplete_fields = ("student",)


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ("offering", "date", "period_no", "present_count", "total_count")
    list_filter = ("date", "offering__subject__department", "offering__session")
    search_fields = ("offering__subject__code", "offering__subject__name")
    autocomplete_fields = ("offering", "created_by")
    inlines = [AttendanceRecordInline]
    date_hierarchy = "date"

    @admin.display(description="Present")
    def present_count(self, obj):
        return obj.present_count

    @admin.display(description="Total")
    def total_count(self, obj):
        return obj.total_count


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("class_session", "student", "status", "marked_by", "marked_at")
    list_filter = ("status", "class_session__date")
    search_fields = ("student__roll_no", "student__user__username")
    autocomplete_fields = ("class_session", "student", "marked_by")
