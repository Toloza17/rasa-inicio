from django.db import models

class pregunta(models.Model):
    frase = models.TextField(unique=True, verbose_name="Pregunta")  # Se agrega verbose_name
    respuesta = models.TextField()

    def __str__(self):
        return self.frase  # Devuelve el contenido de la pregunta
    class Meta:
        managed = False
        db_table = 'preguntas'  # Nombre de la tabla existente en tu base de datos original

class palabrabaneada(models.Model):
    palabra = models.CharField(max_length=100, unique=True, verbose_name="Palabra prohibida")

    def __str__(self):
        return self.palabra  # Devuelve la palabra prohibida
    class Meta:
        managed = False
        db_table = 'ban'  # Nombre de la tabla existente en tu base de datos original