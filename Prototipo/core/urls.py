from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    CustomLoginView, 
    asesor_dashboard, 
    estudiante_dashboard, 
    admin_dashboard, 
    subir_version,
    registrar_estudiante,
    actualizar_estudiante,
    registrar_asesor,
    actualizar_asesor,
    registrar_tesis,
    actualizar_tesis,
    descargar_pdf_tesis
)

urlpatterns = [
    # Login y Logout
    path('', CustomLoginView.as_view(), name='login'), 
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    
    # Dashboards
    path('asesor/dashboard/', asesor_dashboard, name='asesor_dashboard'),
    path('estudiante/dashboard/', estudiante_dashboard, name='estudiante_dashboard'),
    path('administrador/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('estudiante/subir-version/', subir_version, name='subir_version'),
    
    # Funciones Administrativas - Estudiantes
    path('admin/registrar-estudiante/', registrar_estudiante, name='registrar_estudiante'),
    path('admin/actualizar-estudiante/<int:estudiante_id>/', actualizar_estudiante, name='actualizar_estudiante'),
    
    # Funciones Administrativas - Asesores
    path('admin/registrar-asesor/', registrar_asesor, name='registrar_asesor'),
    path('admin/actualizar-asesor/<int:asesor_id>/', actualizar_asesor, name='actualizar_asesor'),
    
    # Funciones Administrativas - Tesis
    path('admin/registrar-tesis/', registrar_tesis, name='registrar_tesis'),
    path('admin/actualizar-tesis/<int:tesis_id>/', actualizar_tesis, name='actualizar_tesis'),
    path('admin/descargar-pdf/<int:tesis_id>/', descargar_pdf_tesis, name='descargar_pdf_tesis'),
]