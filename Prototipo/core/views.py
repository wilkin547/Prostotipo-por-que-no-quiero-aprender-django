import uuid
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from .models import Tesis, Estatus, Comentario

# 1. Vista de Login Inteligente
class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user
        
        # Redirección según el rol del usuario
        if user.is_superuser or user.is_staff:
            return reverse_lazy('admin:index')
        elif hasattr(user, 'profesor'):
            return reverse_lazy('asesor_dashboard')
        elif hasattr(user, 'estudiante'):
            return reverse_lazy('estudiante_dashboard')
            
        return reverse_lazy('admin:index')

# 2. Vista del Panel del Asesor
@login_required
def asesor_dashboard(request):
    profesor = request.user.profesor
    
    # Obtenemos las tesis asignadas a este profesor
    tesis_asignadas = Tesis.objects.filter(asesor=profesor).prefetch_related('estudiantes', 'versiones')
    
    # Lógica para saber qué tesis está seleccionada
    tesis_id = request.GET.get('tesis')
    if tesis_id:
        tesis_activa = tesis_asignadas.filter(id=tesis_id).first()
    else:
        tesis_activa = tesis_asignadas.first() 

    # ==========================================
    # PROCESAR FORMULARIOS (NUEVO O ACTUALIZAR)
    # ==========================================
    if request.method == 'POST' and tesis_activa:
        accion = request.POST.get('action') # Identificamos qué botón del HTML se pulsó

        # ACCIÓN A: Actualizar el estado de un comentario específico
        if accion == 'update_comment_status':
            comentario_id = request.POST.get('comentario_id')
            nuevo_estado_nombre = request.POST.get('estado_comentario')
            
            if comentario_id and nuevo_estado_nombre:
                # Buscamos el comentario exacto en la base de datos
                comentario_editar = Comentario.objects.filter(id=comentario_id).first()
                if comentario_editar:
                    # Obtenemos o creamos el estatus ("Corregido", "No Atendido", etc.)
                    estado_obj, _ = Estatus.objects.get_or_create(nombre=nuevo_estado_nombre)
                    # Lo guardamos de verdad en la base de datos
                    comentario_editar.estatus_comentario = estado_obj
                    comentario_editar.save()

        # ACCIÓN B: Crear un comentario nuevo
        elif accion == 'new_comment':
            texto_comentario = request.POST.get('comentario')
            nuevo_estado_tesis = request.POST.get('estado')
            ultima_version = tesis_activa.versiones.first()

            # 1. Guardar el nuevo comentario
            if texto_comentario and texto_comentario.strip() and ultima_version:
                codigo_generado = f"C-{uuid.uuid4().hex[:6].upper()}"
                estado_pendiente, _ = Estatus.objects.get_or_create(nombre="Pendiente")
                
                Comentario.objects.create(
                    codigo=codigo_generado,
                    tesis=tesis_activa,
                    version=ultima_version,
                    autor=request.user,
                    contenido=texto_comentario.strip(),
                    estatus_comentario=estado_pendiente
                )

            # 2. Actualizar estado general de la tesis
            if nuevo_estado_tesis:
                nuevo_estado, _ = Estatus.objects.get_or_create(nombre=nuevo_estado_tesis)
                tesis_activa.estado = nuevo_estado
                tesis_activa.save()

        # Redirigimos a la misma página para "limpiar" la petición POST y ver los datos nuevos
        return redirect(f"{reverse('asesor_dashboard')}?tesis={tesis_activa.id}")

    # Enviar los datos actualizados a la plantilla HTML
    context = {
        'tesis_asignadas': tesis_asignadas,
        'tesis_activa': tesis_activa,
    }
    
    # Renderizamos la plantilla (asegúrate de que el nombre aquí coincida con tu archivo HTML)
    return render(request, 'asesor.html', context)
# 3. Vista del Panel del Estudiante
@login_required
def estudiante_dashboard(request):
    return render(request, 'Estudiantes.html')