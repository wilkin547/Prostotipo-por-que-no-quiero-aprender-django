from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from .models import Tesis

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
            
        # SOLUCIÓN: Si el usuario no tiene ningún rol, va al admin
        return reverse_lazy('admin:index')

# 2. Vista del Panel del Asesor
@login_required
def asesor_dashboard(request):
    # Obtenemos al profesor logueado
    profesor = request.user.profesor
    
    # Buscamos las tesis donde este profesor es el asesor
    tesis_asignadas = Tesis.objects.filter(asesor=profesor).prefetch_related('estudiantes', 'versiones')
    
    # Lógica para saber qué tesis estamos viendo en el centro
    tesis_id = request.GET.get('tesis')
    if tesis_id:
        tesis_activa = tesis_asignadas.filter(id=tesis_id).first()
    else:
        # Si no selecciona ninguna, muestra la primera de la lista por defecto
        tesis_activa = tesis_asignadas.first() 
    
    # Le enviamos esos datos al HTML
    context = {
        'tesis_asignadas': tesis_asignadas,
        'tesis_activa': tesis_activa,
    }
    
    # Apuntamos a tu archivo físico Asesor.html
    return render(request, 'Asesor.html', context)

# 3. Vista del Panel del Estudiante
@login_required
def estudiante_dashboard(request):
    # Apuntamos a tu archivo físico Estudiantes.html
    return render(request, 'Estudiantes.html')