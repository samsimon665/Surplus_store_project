from django.db import models


class FAQ(models.Model):
    SECTION_CHOICES = [
        ("ordering", "Ordering & Payment"),
        ("shipping", "Shipping & Delivery"),
        ("returns", "Returns & Exchanges"),
    ]

    section = models.CharField(
        max_length=20,
        choices=SECTION_CHOICES
    )
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["section", "display_order"]

    def __str__(self):
        return self.question
