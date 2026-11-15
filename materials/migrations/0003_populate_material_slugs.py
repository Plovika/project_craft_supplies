from django.db import migrations
from django.utils.text import slugify
from unidecode import unidecode


def populate_slugs(apps, schema_editor):
    material = apps.get_model("materials", "Material")
    for record in material.objects.using(
        schema_editor.connection.alias,
    ).order_by("pk"):
        base = slugify(unidecode(record.name))[:150].strip("-") or "material"
        record.slug = f"{base}-{record.pk}"
        record.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("materials", "0002_material_is_low_stock_material_slug_and_more"),
    ]
    operations = [
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
    ]
