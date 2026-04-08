from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy

# 1. Vista de Login Inteligente
class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user
        
        # Si es Superusuario o Staff, va al Admin
        if user.is_superuser or user.is_staff:
            return reverse_lazy('admin:index')
            
        # Si tiene un perfil de Profesor/Asesor, va a su panel
        elif hasattr(user, 'profesor'):
            return reverse_lazy('asesor_dashboard')
            
        # Si tiene un perfil de Estudiante, va a su panel
        elif hasattr(user, 'estudiante'):
            return reverse_lazy('estudiante_dashboard')
            
        # Por defecto, recarga el login
        return reverse_lazy('login')

# 2. Vista del Panel del Asesor
@login_required
def asesor_dashboard(request):
    # Aquí cargamos el HTML del Asesor que hicimos antes
    return render(request, 'asesor_dashboard.html')

# 3. Vista del Panel del Estudiante
@login_required
def estudiante_dashboard(request):
    # Asumiendo que guardaste el HTML del estudiante con este nombre
    return render(request, 'Estudiantes.html')