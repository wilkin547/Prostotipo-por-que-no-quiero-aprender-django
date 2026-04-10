from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

# Extensiones permitidas según requerimientos institucionales
EXTENSIONES_PERMITIDAS = ['pdf', 'docx']

# --- TABLAS MAESTRAS (CATÁLOGOS) ---

class Facultad(models.Model):
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre

class Departamento(models.Model):
    nombre = models.CharField(max_length=100)
    facultad = models.ForeignKey(Facultad, on_delete=models.CASCADE, related_name='departamentos')

    def __str__(self):
        return f"{self.nombre} ({self.facultad.nombre})"

class Carrera(models.Model):
    nombre = models.CharField(max_length=100)
    facultad = models.ForeignKey(Facultad, on_delete=models.CASCADE, related_name='carreras')

    def __str__(self):
        return self.nombre

class Especialidad(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Estatus(models.Model):
    """Modelo genérico para manejar estados de usuarios o procesos"""
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

# --- PERFILES DE USUARIO ---

class PerfilBase(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    correo_institucional = models.EmailField(max_length=100, unique=True) # Correo UNPHU
    telefono = models.CharField(max_length=15, blank=True)
    facultad = models.ForeignKey(Facultad, on_delete=models.SET_NULL, null=True)
    estatus = models.ForeignKey(Estatus, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        abstract = True

class Estudiante(PerfilBase):
    matricula = models.CharField(max_length=10, unique=True) # Ej: XX99-9999
    carrera = models.ForeignKey(Carrera, on_delete=models.PROTECT)
    
    def __str__(self):
        return f"{self.matricula} - {self.user.get_full_name()}"

class Profesor(PerfilBase):
    codigo_empleado = models.CharField(max_length=10, unique=True) # Matrícula de asesor
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT)
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT)
    disponibilidad = models.CharField(max_length=30) # Ej: Disponible, No Disponible
    disponibilidad_max = models.IntegerField(default=5)
    fecha_registro = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"Asesor: {self.user.get_full_name()}"

# --- GESTIÓN DE TESIS ---

class Tesis(models.Model):
    codigo = models.CharField(max_length=20, unique=True) # Ej: T-9999-99
    titulo = models.TextField()
    # Una tesis puede tener más de un estudiante (Relación Muchos a Muchos)
    estudiantes = models.ManyToManyField(Estudiante, related_name='tesis')
    asesor = models.ForeignKey(Profesor, on_delete=models.SET_NULL, null=True, related_name='tesis_asesoradas')
    estado = models.ForeignKey(Estatus, on_delete=models.PROTECT, related_name='tesis_estados')
    periodo = models.CharField(max_length=10) # Ej: 9999/9
    fecha_limite = models.DateField(null=True, blank=True)
    calificacion = models.IntegerField(null=True, blank=True) # Calificación (si aplica)
    link_descarga_final = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.codigo} - {self.titulo[:50]}..."

class VersionTesis(models.Model):
    tesis = models.ForeignKey(Tesis, on_delete=models.CASCADE, related_name='versiones')
    archivo = models.FileField(
        upload_to='tesis/versiones/', 
        validators=[FileExtensionValidator(allowed_extensions=EXTENSIONES_PERMITIDAS)]
    )
    codigo_version = models.CharField(max_length=20) # Ej: HV-99999
    nombre_entregable = models.CharField(max_length=255)
    link_descarga = models.URLField(max_length=500, blank=True)
    fecha = models.DateField(auto_now_add=True)
    estatus_version = models.ForeignKey(Estatus, on_delete=models.PROTECT)

    class Meta:
        ordering = ['-fecha']

class Comentario(models.Model):
    codigo = models.CharField(max_length=20, unique=True) # Ej: C-9999-99
    tesis = models.ForeignKey(Tesis, on_delete=models.CASCADE, related_name='comentarios')
    estatus_comentario = models.ForeignKey(Estatus, on_delete=models.SET_NULL, null=True)
    contenido = models.TextField()
    fecha = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
    
    # NUEVO: Se agrega null=True, blank=True para que las migraciones no den error
    version = models.ForeignKey(VersionTesis, on_delete=models.CASCADE, related_name='comentarios', null=True, blank=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Comentario {self.codigo} de Tesis {self.tesis.codigo}"