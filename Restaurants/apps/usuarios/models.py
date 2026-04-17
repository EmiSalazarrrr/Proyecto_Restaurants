from django.db import models

# Create your models here.
class Perfiles(models.Model):
    id_tipo_de_usuario = models.AutoField(primary_key=True)
    tipo_de_usuario = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'perfiles'


class Cliente(models.Model):
    nombre_usuario = models.CharField(primary_key=True, max_length=20)
    numero_celular = models.CharField(unique=True, max_length=15)
    nombre = models.CharField(max_length=30)
    apellido_paterno = models.CharField(db_column='apellido_Paterno', max_length=30)
    apellido_materno = models.CharField(max_length=30, blank=True, null=True)
    contrase_a = models.CharField(db_column='contrase??a', max_length=255)
    id_tipo_de_usuario = models.ForeignKey(Perfiles, models.DO_NOTHING, db_column='id_tipo_de_usuario', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cliente'