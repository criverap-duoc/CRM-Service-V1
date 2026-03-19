from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import connection
from django.db.utils import OperationalError
from drf_spectacular.utils import extend_schema


class HealthCheckView(APIView):
    """
    Endpoint para verificar el estado del servidor y la base de datos.
    Usado por load balancers y sistemas de monitoreo.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Health check",
        responses={
            200: {"type": "object", "properties": {
                "status": {"type": "string"},
                "database": {"type": "string"},
            }},
            503: {"type": "object", "properties": {
                "status": {"type": "string"},
                "database": {"type": "string"},
            }},
        },
        tags=["Health"],
    )
    def get(self, request):
        # Verificar conexión a la base de datos
        try:
            connection.ensure_connection()
            db_status = "ok"
        except OperationalError:
            db_status = "unavailable"

        healthy = db_status == "ok"

        payload = {
            "status": "ok" if healthy else "degraded",
            "database": db_status,
        }

        return Response(payload, status=200 if healthy else 503)
