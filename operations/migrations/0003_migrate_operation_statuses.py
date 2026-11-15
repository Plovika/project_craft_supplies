from django.db import migrations


def forwards(apps, schema_editor):
    operation = apps.get_model("operations", "Operation")
    records = operation.objects.using(schema_editor.connection.alias)
    records.filter(is_cancelled=True).update(status="cancelled")
    records.filter(is_cancelled=False).update(status="active")


def backwards(apps, schema_editor):
    operation = apps.get_model("operations", "Operation")
    records = operation.objects.using(schema_editor.connection.alias)
    records.filter(status="cancelled").update(is_cancelled=True)
    records.exclude(status="cancelled").update(is_cancelled=False)


class Migration(migrations.Migration):
    dependencies = [("operations", "0002_operation_status")]
    operations = [migrations.RunPython(forwards, backwards)]
