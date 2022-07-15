from django.db import models


class Voivodeships(models.Model):
    name = models.CharField(max_length=20, unique=True)
    code = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f'{self.name}'

    @classmethod
    def voivodeships_choices(cls):
        vivos = cls.objects.all()

        return tuple([(vivo.name, vivo.name) for vivo in vivos])
