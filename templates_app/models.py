import uuid
from django.db import models

class Template(models.Model):
    """
    Store templates with versioning and language support.
    template_code: logical identifier (e.g., "welcome_email" or path-like "emails/welcome")
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template_code = models.CharField(max_length=200)  # unique logical code e.g. "welcome_email"
    name = models.CharField(max_length=150, blank=True, null=True)
    channel = models.CharField(max_length=10, choices=[('email','email'),('push','push')], default='email')
    language = models.CharField(max_length=10, default='en')
    subject = models.CharField(max_length=255, null=True, blank=True)  # used for email
    body = models.TextField()  # template body (Jinja2)
    variables = models.JSONField(default=list)  # e.g., ["name", "order_id"]
    version = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)  # optional user id or service
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('template_code','language','version')
        indexes = [
            models.Index(fields=['template_code','language','version']),
        ]

    def __str__(self):
        return f"{self.template_code} ({self.language}) v{self.version}"

