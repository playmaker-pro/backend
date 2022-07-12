from django.db import models


class Voivodeships(models.Model):
    name = models.CharField(max_length=20)
    code = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f'{self.name}'

    @staticmethod
    def voivodeships_choices():
        vivos = Voivodeships.objects.all()

        return tuple([(vivo.name, vivo.name) for vivo in vivos])
