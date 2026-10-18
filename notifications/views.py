from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, View


class NotificationListView(LoginRequiredMixin, ListView):
    template_name = "notifications/list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        return self.request.user.notifications.all()


class NotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(request.user.notifications, pk=pk)
        notification.mark_read()
        return HttpResponse(status=204, headers={"HX-Refresh": "true"})


class NotificationReadAllView(LoginRequiredMixin, View):
    def post(self, request):
        request.user.notifications.filter(is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return HttpResponse(status=204, headers={"HX-Refresh": "true"})
