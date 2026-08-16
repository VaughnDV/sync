from __future__ import annotations

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def live(request):
    return JsonResponse({"status": "live"})


@require_GET
def ready(request):
    checks = {"database": False}
    try:
        connection.ensure_connection()
        checks["database"] = True
    except Exception:  # noqa: BLE001
        checks["database"] = False
    status = 200 if all(checks.values()) else 503
    return JsonResponse({"status": "ready" if status == 200 else "not_ready", "checks": checks}, status=status)
