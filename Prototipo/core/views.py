import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse_lazy, reverse
from django.contrib.auth.models import User
from .models import Tesis, Estatus, Comentario, Estudiante, Profesor, VersionTesis, Carrera, Facultad, Departamento, Especialidad

# 1. VISTA DE LOGIN: Redirección automática por rol
class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user
        # Si es admin (superusuario), va al dashboard de administrador
        if user.is_superuser or user.is_staff:
            return reverse_lazy('admin_dashboard')
        # Si es profesor, va a su panel de asesor
        elif hasattr(user, 'profesor'):
            return reverse_lazy('asesor_dashboard')
        # Si es estudiante, va a su panel
        elif hasattr(user, 'estudiante'):
            return reverse_lazy('estudiante_dashboard')
            
        return reverse_lazy('login')

# 2. VISTA DEL ADMINISTRADOR (CON DATOS REALES)
@staff_member_required
def admin_dashboard(request):
    # Obtener datos para el dashboard
    total_estudiantes = Estudiante.objects.all().count()
    total_asesores = Profesor.objects.all().count()
    total_tesis = Tesis.objects.all().count()
    tesis_aprobadas = Tesis.objects.filter(estado__nombre='Aprobada').count()
    tesis_en_proceso = Tesis.objects.filter(estado__nombre__in=['Borrador', 'En Revisión']).count()
    
    # Obtener listados
    estudiantes = Estudiante.objects.all().select_related('carrera', 'facultad', 'estatus')
    asesores = Profesor.objects.all().select_related('especialidad', 'facultad', 'estatus')
    tesis_list = Tesis.objects.all().select_related('asesor', 'estado').prefetch_related('estudiantes')
    comentarios = Comentario.objects.all().select_related('autor', 'tesis', 'version').order_by('-fecha')
    versiones = VersionTesis.objects.all().select_related('tesis').order_by('-fecha')
    
    context = {
        'total_estudiantes': total_estudiantes,
        'total_asesores': total_asesores,
        'total_tesis': total_tesis,
        'tesis_aprobadas': tesis_aprobadas,
        'tesis_en_proceso': tesis_en_proceso,
        'estudiantes': estudiantes,
        'asesores': asesores,
        'tesis_list': tesis_list,
        'comentarios': comentarios,
        'versiones': versiones,
        'carreras': Carrera.objects.all(),
        'facultades': Facultad.objects.all(),
        'departamentos': Departamento.objects.all(),
        'especialidades': Especialidad.objects.all(),
        'estatus': Estatus.objects.all(),
    }
    return render(request, 'administrador.html', context)

# 3. VISTA DEL ASESOR (CON HISTORIAL Y COMENTARIOS)
@login_required
def asesor_dashboard(request):
    profesor = request.user.profesor
    tesis_asignadas = Tesis.objects.filter(asesor=profesor).prefetch_related('estudiantes', 'versiones')
    
    tesis_id = request.GET.get('tesis')
    version_id = request.GET.get('version')
    
    if tesis_id:
        tesis_activa = tesis_asignadas.filter(id=tesis_id).first()
    else:
        tesis_activa = tesis_asignadas.first() 

    version_activa = None
    if tesis_activa:
        if version_id:
            version_activa = tesis_activa.versiones.filter(id=version_id).first()
        if not version_activa:
            version_activa = tesis_activa.versiones.first()

    if request.method == 'POST' and tesis_activa:
        accion = request.POST.get('action') 

        if accion == 'update_comment_status':
            comentario_id = request.POST.get('comentario_id')
            nuevo_estado_nombre = request.POST.get('estado_comentario')
            
            if comentario_id and nuevo_estado_nombre:
                comentario_editar = Comentario.objects.filter(id=comentario_id).first()
                if comentario_editar:
                    estado_obj, _ = Estatus.objects.get_or_create(nombre=nuevo_estado_nombre)
                    comentario_editar.estatus_comentario = estado_obj
                    comentario_editar.save()

        elif accion == 'new_comment':
            texto_comentario = request.POST.get('comentario')
            nuevo_estado_tesis = request.POST.get('estado')
            version_form_id = request.POST.get('version_id')

            if version_form_id:
                version_comentada = tesis_activa.versiones.filter(id=version_form_id).first()
            else:
                version_comentada = tesis_activa.versiones.first()

            if texto_comentario and texto_comentario.strip() and version_comentada:
                codigo_generado = f"C-{uuid.uuid4().hex[:6].upper()}"
                estado_pendiente, _ = Estatus.objects.get_or_create(nombre="Pendiente")
                
                Comentario.objects.create(
                    codigo=codigo_generado,
                    tesis=tesis_activa,
                    version=version_comentada,
                    autor=request.user,
                    contenido=texto_comentario.strip(),
                    estatus_comentario=estado_pendiente
                )

            if nuevo_estado_tesis:
                nuevo_estado, _ = Estatus.objects.get_or_create(nombre=nuevo_estado_tesis)
                tesis_activa.estado = nuevo_estado
                tesis_activa.save()

        url_redirect = f"{reverse('asesor_dashboard')}?tesis={tesis_activa.id}"
        if version_activa:
            url_redirect += f"&version={version_activa.id}"
        return redirect(url_redirect)

    context = {
        'tesis_asignadas': tesis_asignadas,
        'tesis_activa': tesis_activa,
        'version_activa': version_activa,
    }
    return render(request, 'asesor.html', context)

# 4. VISTA DEL ESTUDIANTE
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Tesis, VersionTesis

@login_required
def estudiante_dashboard(request):
    estudiante = request.user.estudiante
    # Obtenemos la tesis del estudiante con sus relaciones
    tesis_principal = Tesis.objects.filter(estudiantes=estudiante).prefetch_related('versiones', 'asesor').first()
    
    version_activa = None
    if tesis_principal:
        # 1. Intentamos obtener el ID de la versión desde la URL (?version=ID)
        version_id = request.GET.get('version')
        
        if version_id:
            # Si el usuario hizo clic en una versión específica, la buscamos
            version_activa = tesis_principal.versiones.filter(id=version_id).first()
        
        # 2. Si no hay ID en la URL o no se encontró, mostramos la última (la más reciente)
        if not version_activa:
            version_activa = tesis_principal.versiones.first()

    context = {
        'tesis_principal': tesis_principal,
        'version_activa': version_activa, # Esta es la versión que el iframe debe mostrar
    }
    return render(request, 'Estudiantes.html', context)

@login_required
def subir_version(request):
    if request.method == 'POST':
        tesis_id = request.POST.get('tesis_id')
        archivo = request.FILES.get('archivo')
        nombre_entregable = request.POST.get('nombre_entregable')
        
        # Validar que el archivo no supere 10MB (10 * 1024 * 1024 bytes)
        MAX_FILE_SIZE = 10 * 1024 * 1024
        
        if tesis_id and archivo and nombre_entregable:
            if archivo.size <= MAX_FILE_SIZE:
                try:
                    tesis = Tesis.objects.get(id=tesis_id)
                    
                    # Generar código de versión
                    codigo_version = f"V-{uuid.uuid4().hex[:6].upper()}"
                    
                    # Obtener o crear estatus "Entregado"
                    estatus_entregado, _ = Estatus.objects.get_or_create(nombre="Entregado")
                    
                    # Crear la versión
                    version = VersionTesis.objects.create(
                        tesis=tesis,
                        archivo=archivo,
                        codigo_version=codigo_version,
                        nombre_entregable=nombre_entregable,
                        estatus_version=estatus_entregado
                    )
                    
                except Tesis.DoesNotExist:
                    pass
        
        return redirect('estudiante_dashboard')

# 5. FUNCIONES ADMINISTRATIVAS

@staff_member_required
def registrar_estudiante(request):
    """Registra un nuevo estudiante en el sistema"""
    if request.method == 'POST':
        matricula = request.POST.get('matricula')
        nombres = request.POST.get('nombres')
        apellidos = request.POST.get('apellidos')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        carrera_id = request.POST.get('carrera')
        
        try:
            carrera = Carrera.objects.get(id=carrera_id)
            
            # Crear usuario para el estudiante
            user = User.objects.create_user(
                username=matricula.lower(),
                email=email,
                first_name=nombres,
                last_name=apellidos,
                password='temporal123'  # Contraseña temporal que debe cambiar
            )
            
            # Crear perfil de estudiante
            estatus, _ = Estatus.objects.get_or_create(nombre='Activo')
            facultad = carrera.facultad
            
            Estudiante.objects.create(
                user=user,
                matricula=matricula,
                carrera=carrera,
                correo_institucional=email,
                telefono=telefono,
                facultad=facultad,
                estatus=estatus
            )
        except Exception as e:
            pass
    
    return redirect('admin_dashboard')

@staff_member_required
def actualizar_estudiante(request, estudiante_id):
    """Actualiza datos de un estudiante"""
    if request.method == 'POST':
        try:
            estudiante = Estudiante.objects.get(id=estudiante_id)
            estudiante.telefono = request.POST.get('telefono', estudiante.telefono)
            estudiante.correo_institucional = request.POST.get('email', estudiante.correo_institucional)
            
            # Actualizar carrera si aplica
            carrera_id = request.POST.get('carrera')
            if carrera_id:
                try:
                    carrera = Carrera.objects.get(id=carrera_id)
                    estudiante.carrera = carrera
                except Carrera.DoesNotExist:
                    pass
            
            # Actualizar estado si aplica
            estatus_nombre = request.POST.get('estatus')
            if estatus_nombre:
                estatus, _ = Estatus.objects.get_or_create(nombre=estatus_nombre)
                estudiante.estatus = estatus
            
            estudiante.save()
            estudiante.user.first_name = request.POST.get('nombres', estudiante.user.first_name)
            estudiante.user.last_name = request.POST.get('apellidos', estudiante.user.last_name)
            estudiante.user.save()
            
            return JsonResponse({'success': True, 'message': 'Estudiante actualizado exitosamente'})
        except Estudiante.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Estudiante no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@staff_member_required
def registrar_asesor(request):
    """Registra un nuevo profesor/asesor"""
    if request.method == 'POST':
        codigo_empleado = request.POST.get('codigo_empleado')
        nombres = request.POST.get('nombres')
        apellidos = request.POST.get('apellidos')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        especialidad_id = request.POST.get('especialidad')
        departamento_id = request.POST.get('departamento')
        disponibilidad_max = int(request.POST.get('disponibilidad_max', 5))
        
        try:
            especialidad = Especialidad.objects.get(id=especialidad_id)
            departamento = Departamento.objects.get(id=departamento_id)
            facultad = departamento.facultad
            
            # Crear usuario
            user = User.objects.create_user(
                username=codigo_empleado.lower(),
                email=email,
                first_name=nombres,
                last_name=apellidos,
                password='temporal123'
            )
            
            estatus, _ = Estatus.objects.get_or_create(nombre='Disponible')
            
            Profesor.objects.create(
                user=user,
                codigo_empleado=codigo_empleado,
                correo_institucional=email,
                telefono=telefono,
                especialidad=especialidad,
                departamento=departamento,
                facultad=facultad,
                disponibilidad='Disponible',
                disponibilidad_max=disponibilidad_max,
                estatus=estatus
            )
        except Exception as e:
            pass
    
    return redirect('admin_dashboard')

@staff_member_required
def actualizar_asesor(request, asesor_id):
    """Actualiza datos de un asesor"""
    if request.method == 'POST':
        try:
            profesor = Profesor.objects.get(id=asesor_id)
            profesor.telefono = request.POST.get('telefono', profesor.telefono)
            profesor.correo_institucional = request.POST.get('email', profesor.correo_institucional)
            profesor.disponibilidad_max = int(request.POST.get('disponibilidad_max', profesor.disponibilidad_max))
            
            # Actualizar disponibilidad
            disponibilidad_nombre = request.POST.get('disponibilidad')
            if disponibilidad_nombre:
                profesor.disponibilidad = disponibilidad_nombre
            
            profesor.save()
            profesor.user.first_name = request.POST.get('nombres', profesor.user.first_name)
            profesor.user.last_name = request.POST.get('apellidos', profesor.user.last_name)
            profesor.user.save()
            
            return JsonResponse({'success': True, 'message': 'Asesor actualizado exitosamente'})
        except Profesor.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Asesor no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@staff_member_required
def registrar_tesis(request):
    """Registra una nueva tesis"""
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        titulo = request.POST.get('titulo')
        periodo = request.POST.get('periodo')
        asesor_id = request.POST.get('asesor')
        estado_nombre = request.POST.get('estado', 'Borrador')
        fecha_limite = request.POST.get('fecha_limite')
        
        # Obtener estudiantes (puede ser múltiple)
        estudiantes_ids = request.POST.getlist('estudiantes')
        
        try:
            estado, _ = Estatus.objects.get_or_create(nombre=estado_nombre)
            asesor = Profesor.objects.get(id=asesor_id) if asesor_id else None
            
            tesis = Tesis.objects.create(
                codigo=codigo,
                titulo=titulo,
                periodo=periodo,
                asesor=asesor,
                estado=estado,
                fecha_limite=fecha_limite if fecha_limite else None
            )
            
            # Agregar estudiantes
            for est_id in estudiantes_ids:
                try:
                    estudiante = Estudiante.objects.get(id=est_id)
                    tesis.estudiantes.add(estudiante)
                except Estudiante.DoesNotExist:
                    pass
        except Exception as e:
            pass
    
    return redirect('admin_dashboard')

@staff_member_required
def actualizar_tesis(request, tesis_id):
    """Actualiza datos de una tesis"""
    if request.method == 'POST':
        try:
            tesis = Tesis.objects.get(id=tesis_id)
            tesis.titulo = request.POST.get('titulo', tesis.titulo)
            tesis.periodo = request.POST.get('periodo', tesis.periodo)
            tesis.fecha_limite = request.POST.get('fecha_limite', tesis.fecha_limite)
            
            # Actualizar estado
            estado_nombre = request.POST.get('estado')
            if estado_nombre:
                estado, _ = Estatus.objects.get_or_create(nombre=estado_nombre)
                tesis.estado = estado
            
            # Actualizar calificación si existe
            calificacion = request.POST.get('calificacion')
            if calificacion:
                tesis.calificacion = int(calificacion)
            
            # Actualizar asesor si existe
            asesor_id = request.POST.get('asesor')
            if asesor_id:
                tesis.asesor = Profesor.objects.get(id=asesor_id)
            
            tesis.save()
            
            return JsonResponse({'success': True, 'message': 'Tesis actualizada exitosamente'})
        except Tesis.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Tesis no encontrada'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@login_required
def descargar_pdf_tesis(request, tesis_id):
    """Descarga el PDF de la versión más reciente de una tesis"""
    try:
        tesis = Tesis.objects.get(id=tesis_id)
        
        # Obtener la primera versión (la más reciente)
        version = tesis.versiones.first()
        
        if version and version.archivo:
            # Devolver el archivo
            response = FileResponse(version.archivo.open('rb'), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{tesis.codigo}_{version.codigo_version}.pdf"'
            return response
        else:
            return JsonResponse({'error': 'No hay versión disponible para descargar'}, status=404)
    except Tesis.DoesNotExist:
        return JsonResponse({'error': 'Tesis no encontrada'}, status=404)

# 6. VISTAS DE CONFIGURACIÓN - Gestión de Catálogos

@staff_member_required
def crear_facultad(request):
    """Crea una nueva facultad"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if nombre:
            Facultad.objects.create(nombre=nombre)
            return JsonResponse({'success': True, 'message': 'Facultad creada exitosamente'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@staff_member_required
def actualizar_facultad(request, facultad_id):
    """Actualiza una facultad"""
    if request.method == 'POST':
        try:
            facultad = Facultad.objects.get(id=facultad_id)
            nombre = request.POST.get('nombre')
            if nombre:
                facultad.nombre = nombre
                facultad.save()
                return JsonResponse({'success': True, 'message': 'Facultad actualizada exitosamente'})
        except Facultad.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Facultad no encontrada'}, status=404)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@staff_member_required
def crear_departamento(request):
    """Crea un nuevo departamento"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        facultad_id = request.POST.get('facultad')
        if nombre and facultad_id:
            try:
                facultad = Facultad.objects.get(id=facultad_id)
                Departamento.objects.create(nombre=nombre, facultad=facultad)
                return JsonResponse({'success': True, 'message': 'Departamento creado exitosamente'})
            except Facultad.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Facultad no encontrada'}, status=404)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@staff_member_required
def actualizar_departamento(request, departamento_id):
    """Actualiza un departamento"""
    if request.method == 'POST':
        try:
            depto = Departamento.objects.get(id=departamento_id)
            nombre = request.POST.get('nombre')
            facultad_id = request.POST.get('facultad')
            if nombre:
                depto.nombre = nombre
            if facultad_id:
                facultad = Facultad.objects.get(id=facultad_id)
                depto.facultad = facultad
            depto.save()
            return JsonResponse({'success': True, 'message': 'Departamento actualizado exitosamente'})
        except Departamento.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Departamento no encontrado'}, status=404)
        except Facultad.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Facultad no encontrada'}, status=404)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@staff_member_required
def crear_carrera(request):
    """Crea una nueva carrera"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        facultad_id = request.POST.get('facultad')
        if nombre and facultad_id:
            try:
                facultad = Facultad.objects.get(id=facultad_id)
                Carrera.objects.create(nombre=nombre, facultad=facultad)
                return JsonResponse({'success': True, 'message': 'Carrera creada exitosamente'})
            except Facultad.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Facultad no encontrada'}, status=404)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@staff_member_required
def actualizar_carrera(request, carrera_id):
    """Actualiza una carrera"""
    if request.method == 'POST':
        try:
            carrera = Carrera.objects.get(id=carrera_id)
            nombre = request.POST.get('nombre')
            facultad_id = request.POST.get('facultad')
            if nombre:
                carrera.nombre = nombre
            if facultad_id:
                facultad = Facultad.objects.get(id=facultad_id)
                carrera.facultad = facultad
            carrera.save()
            return JsonResponse({'success': True, 'message': 'Carrera actualizada exitosamente'})
        except Carrera.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Carrera no encontrada'}, status=404)
        except Facultad.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Facultad no encontrada'}, status=404)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@staff_member_required
def crear_especialidad(request):
    """Crea una nueva especialidad"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if nombre:
            Especialidad.objects.create(nombre=nombre)
            return JsonResponse({'success': True, 'message': 'Especialidad creada exitosamente'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@staff_member_required
def actualizar_especialidad(request, especialidad_id):
    """Actualiza una especialidad"""
    if request.method == 'POST':
        try:
            esp = Especialidad.objects.get(id=especialidad_id)
            nombre = request.POST.get('nombre')
            if nombre:
                esp.nombre = nombre
                esp.save()
                return JsonResponse({'success': True, 'message': 'Especialidad actualizada exitosamente'})
        except Especialidad.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Especialidad no encontrada'}, status=404)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@staff_member_required
def crear_estatus(request):
    """Crea un nuevo estado/estatus"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if nombre:
            Estatus.objects.create(nombre=nombre)
            return JsonResponse({'success': True, 'message': 'Estatus creado exitosamente'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@staff_member_required
def actualizar_estatus(request, estatus_id):
    """Actualiza un estatus"""
    if request.method == 'POST':
        try:
            estatus = Estatus.objects.get(id=estatus_id)
            nombre = request.POST.get('nombre')
            if nombre:
                estatus.nombre = nombre
                estatus.save()
                return JsonResponse({'success': True, 'message': 'Estatus actualizado exitosamente'})
        except Estatus.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Estatus no encontrado'}, status=404)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)