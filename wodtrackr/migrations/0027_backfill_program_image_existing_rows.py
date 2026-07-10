from django.db import migrations


def backfill_program_image(apps, schema_editor):
    ExerciseProgram = apps.get_model('wodtrackr', 'ExerciseProgram')
    default_image = 'exercise_program_images/Defaultbanner.jpg'

    ExerciseProgram.objects.filter(program_image__isnull=True).update(program_image=default_image)
    ExerciseProgram.objects.filter(program_image='').update(program_image=default_image)


class Migration(migrations.Migration):

    dependencies = [
        ('wodtrackr', '0026_backfill_program_image'),
    ]

    operations = [
        migrations.RunPython(backfill_program_image, migrations.RunPython.noop),
    ]
