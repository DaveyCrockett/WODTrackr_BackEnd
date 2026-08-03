from pathlib import Path
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import stripe

# Authenticate the SDK with your secret token
stripe.api_key = settings.STRIPE_SECRET_KEY

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

@csrf_exempt
def create_billing_session(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)
        
    try:
        # Build fully qualified success/cancel paths for the hosted checkout UI
        domain_url = request.build_absolute_uri("/").rstrip("/")
        
        checkpoint = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",  # Enables ongoing Stripe Billing cycles
            line_items=[
                {
                    "price": "price_1QxXYZ...YourPriceID...",  # From your Product Catalog
                    "quantity": 1,
                }
            ],
            success_url=f"{domain_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{domain_url}/billing/cancel/",
        )
        
        # Return the secure destination URL directly to your React or HTML client
        return JsonResponse({"url": checkpoint.url})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
