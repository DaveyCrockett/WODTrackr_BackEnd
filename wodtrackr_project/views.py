from pathlib import Path

from django.conf import settings
from django.http import HttpResponse


def openapi_yaml(request):
    """
    Serve the OpenAPI spec as YAML.
    """
    spec_path = Path(settings.BASE_DIR) / 'openapi.yaml'
    if not spec_path.exists():
        return HttpResponse('OpenAPI spec not found', status=404)
    return HttpResponse(spec_path.read_text(encoding='utf-8'), content_type='application/yaml')


def swagger_ui(request):
    """
    Serve Swagger UI using a CDN, pointing to the local OpenAPI spec.
    """
    html = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>WODTrackr API Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.onload = () => {
        SwaggerUIBundle({
          url: '/api/openapi.yaml',
          dom_id: '#swagger-ui'
        });
      };
    </script>
  </body>
</html>
"""
    return HttpResponse(html, content_type='text/html')
