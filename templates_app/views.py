from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from .models import Template
from .serializers import TemplateCreateSerializer, TemplateOutSerializer
from .renderer import extract_required_variables, render_content

# global response helper to match project format
def api_response(success, data=None, error=None, message="", meta=None, status_code=status.HTTP_200_OK):
    payload = {
        "success": success,
        "data": data,
        "error": error,
        "message": message,
        "meta": meta or {}
    }
    return Response(payload, status=status_code)

def health_check(request):
    return JsonResponse({"status":"ok"})

class TemplateViewSet(viewsets.ModelViewSet):
    """
    list/create/retrieve/update/delete
    POST /api/v1/templates/<pk>/render/  -> render preview (synchronous)
    GET  /api/v1/templates/by_code/?template_code=...&language=...&version=...
    """
    queryset = Template.objects.all().order_by('-created_at')
    serializer_class = TemplateOutSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return TemplateCreateSerializer
        return TemplateOutSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new version automatically: version = latest + 1
        """
        data = request.data
        template_code = data.get('template_code')
        language = data.get('language', 'en')
        channel = data.get('channel', 'email')

        # validate body syntax and variables
        body = data.get('body', '')
        try:
            required_vars = extract_required_variables(body)
        except Exception as e:
            return api_response(False, error="template_syntax_error", message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

        declared_vars = data.get('variables', [])
        missing_declared = [v for v in required_vars if v not in declared_vars]
        if missing_declared:
            return api_response(False, error="missing_variables", message=f"Template contains variables not declared in 'variables': {missing_declared}", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # compute version (atomic)
        with transaction.atomic():
            latest = Template.objects.filter(template_code=template_code, language=language).order_by('-version').first()
            new_version = (latest.version + 1) if latest else 1
            data['version'] = new_version
            serializer = TemplateCreateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            obj = serializer.save()
        out = TemplateOutSerializer(obj).data
        return api_response(True, data=out, message="template_created", status_code=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def render(self, request, pk=None):
        """
        Render a specific template version with template_vars:
        POST /api/v1/templates/<uuid>/render/  body: {"template_vars": {...}}
        """
        obj = self.get_object()
        template_vars = request.data.get('template_vars', {})
        # validate required vars present
        required = extract_required_variables(obj.body)
        missing = [v for v in required if v not in template_vars]
        if missing:
            return api_response(False, error="missing_template_vars", message=f"Missing vars: {missing}", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        try:
            rendered_body = render_content(obj.body, template_vars)
            rendered_subject = None
            if obj.subject:
                # subject can also contain placeholders
                rendered_subject = render_content(obj.subject, template_vars)
        except Exception as e:
            return api_response(False, error="render_error", message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return api_response(True, data={"rendered_subject": rendered_subject, "rendered_body": rendered_body}, message="template_rendered")

    @action(detail=False, methods=['get'], url_path='by_code')
    def by_code(self, request):
        """
        GET /api/v1/templates/by_code/?template_code=code&language=en&version=1
        If version omitted, fetch latest active version.
        """
        template_code = request.query_params.get('template_code')
        language = request.query_params.get('language', 'en')
        version = request.query_params.get('version', None)
        if not template_code:
            return api_response(False, error="missing_param", message="template_code is required", status_code=status.HTTP_400_BAD_REQUEST)
        if version:
            obj = Template.objects.filter(template_code=template_code, language=language, version=version).first()
        else:
            obj = Template.objects.filter(template_code=template_code, language=language, is_active=True).order_by('-version').first()
        if not obj:
            return api_response(False, error="not_found", message="template_not_found", status_code=status.HTTP_404_NOT_FOUND)
        return api_response(True, data=TemplateOutSerializer(obj).data, message="template_fetched")
   

