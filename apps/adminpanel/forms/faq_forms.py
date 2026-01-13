from django import forms
from apps.support.models import FAQ


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = [
            "section",
            "question",
            "answer",
            "is_active",
            "display_order",
        ]
