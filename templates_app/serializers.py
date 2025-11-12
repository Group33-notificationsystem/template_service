from rest_framework import serializers
from .models import Template

class TemplateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = [
            "template_code",
            "name",
            "channel",
            "language",
            "subject",
            "body",
            "variables",
            "version",
            "is_active",
            "created_by"
        ]
        read_only_fields = ("version",)  # version auto-incremented on create

class TemplateOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = "__all__"
