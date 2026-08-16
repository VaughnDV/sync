from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.playlist_sync.models import SyncJob


@login_required
def dashboard(request):
    recent_syncs = SyncJob.objects.filter(user=request.user).order_by("-created_at")[:10]
    context = {"recent_syncs": recent_syncs}
    return render(request, "dashboard/dashboard.html", context)
