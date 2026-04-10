from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('core.urls')), # Conecta las URLs de core a la raíz PRIMERO
    path('admin/', admin.site.urls),
]

# NUEVO: Esto es VITAL para poder ver los PDFs en el navegador
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)