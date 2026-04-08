from django.contrib import admin
from .models import Facultad, Departamento, Carrera, Especialidad, Estatus, Estudiante, Profesor, Tesis, VersionTesis, Comentario

# 1. Agrupamos TODA la personalización en una sola clase
class TesisAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'titulo', 'asesor', 'estado', 'periodo')
    search_fields = ('codigo', 'titulo')


class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'carrera', 'correo_institucional')
    search_fields = ('matricula', 'user__first_name', 'user__last_name')

# 2. Registramos los modelos (¡Siempre DESPUÉS de definir las clases!)
admin.site.register(Facultad)
admin.site.register(Departamento)
admin.site.register(Carrera)
admin.site.register(Especialidad)
admin.site.register(Estatus)
admin.site.register(Estudiante, EstudianteAdmin)
admin.site.register(Profesor)
admin.site.register(Tesis, TesisAdmin) # <--- Ahora registrará la vista con el CSS incluido
admin.site.register(VersionTesis)
admin.site.register(Comentario)

# 3. Personalización de textos globales
admin.site.site_header = "Sistema de Gestión de Tesis UNPHU"
admin.site.site_title = "Panel Administrativo UNPHU"
admin.site.index_title = "Bienvenido al Gestor de Tesis"