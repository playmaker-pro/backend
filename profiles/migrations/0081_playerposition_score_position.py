from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def populate_score_position(apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """
    Populates the `score_position` field of all `PlayerPosition` objects with their corresponding
    position name. Uses a mapping of position names to score position names to achieve this.
    """
    PlayerPosition = apps.get_model("profiles", "PlayerPosition")
    mapping = {
        "Bramkarz": "Bramkarz",
        "Wahadłowy lewy": "Obrońca",
        "Wahadłowy prawy": "Obrońca",
        "Obrońca Lewy": "Obrońca",
        "Obrońca Prawy": "Obrońca",
        "Obrońca Środkowy": "Obrońca",
        "Pomocnik Defensywny (6)": "Defensywny pomocnik",
        "Pomocnik Środkowy (8)": "Ofensywny pomocnik",
        "Pomocnik Ofensywny (10)": "Ofensywny pomocnik",
        "Skrzydłowy": "Ofensywny pomocnik",
        "Napastnik": "Napastnik",
    }
    for obj in PlayerPosition.objects.all():
        obj.score_position = mapping.get(obj.name, "")
        obj.save()


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0080_auto_20230318_0028"),
    ]

    operations = [
        migrations.AddField(
            model_name="playerposition",
            name="score_position",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.RunPython(populate_score_position),
    ]
