from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wodtrackr', '0020_seed_equipment_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='exerciseprogram',
            name='program_image',
            field=models.ImageField(blank=True, null=True, upload_to='exercise_program_images/'),
        ),
    ]
