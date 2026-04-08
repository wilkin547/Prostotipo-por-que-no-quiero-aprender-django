from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import CustomLoginView, asesor_dashboard, estudiante_dashboard

urlpatterns = [
    # Login y Logout
    path('', CustomLoginView.as_view(), name='login'), 
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    
    # Dashboards
    path('asesor/dashboard/', asesor_dashboard, name='asesor_dashboard'),
    path('estudiante/dashboard/', estudiante_dashboard, name='estudiante_dashboard'),
]