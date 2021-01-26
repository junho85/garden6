from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('attendance/', include('attendance.urls')),
    path('common/', include('common.urls')),
    path('tools/', include('tools.urls')),
    path('', RedirectView.as_view(url="/attendance/")),
]
