from django import forms
from .models import AvailabilityRule


class AvailabilityRuleForm(forms.ModelForm):
    class Meta:
        model = AvailabilityRule
        fields = ["weekday", "start_time", "end_time", "slot_duration"]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }
        help_texts = {
            "slot_duration": "Length of each appointment slot, in minutes.",
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")

        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")

        return cleaned