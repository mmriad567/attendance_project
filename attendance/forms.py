from datetime import timedelta

from django import forms
from django.conf import settings
from django.utils import timezone

from accounts.forms import StyledFormMixin

from .models import ClassSession


class ClassSessionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ClassSession
        fields = ("date", "period_no", "start_time", "end_time", "topic")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
            "topic": forms.TextInput(attrs={"placeholder": "Optional topic"}),
        }

    def __init__(self, *args, offering=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.offering = offering
        self.fields["start_time"].required = False
        self.fields["end_time"].required = False
        self.fields["topic"].required = False

    def clean_date(self):
        value = self.cleaned_data["date"]
        today = timezone.localdate()
        window = getattr(settings, "ATTENDANCE_EDIT_WINDOW_DAYS", 3)
        if value > today:
            raise forms.ValidationError("You cannot take attendance for a future date.")
        if value < today - timedelta(days=window):
            raise forms.ValidationError(
                f"Sessions older than {window} day(s) cannot be created."
            )
        return value

    def clean(self):
        cleaned = super().clean()
        if not self.offering:
            return cleaned
        date = cleaned.get("date")
        period_no = cleaned.get("period_no")
        if date and period_no:
            exists = ClassSession.objects.filter(
                offering=self.offering, date=date, period_no=period_no
            ).exists()
            if exists:
                raise forms.ValidationError(
                    "A session for this subject, date and period already exists."
                )
        return cleaned
