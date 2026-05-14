from django.db import migrations


EQUIPMENT_VALUES = [
    'bodyweight',
    'barbell',
    'dumbbell',
    'kettlebell',
    'medicine_ball',
    'box',
    'rig',
    'rings',
    'rope',
    'rower',
    'bike',
    'ski_erg',
    'assault_runner',
    'jump_rope',
    'sled',
    'sandbag',
    'pegboard',
    'other',
]


def seed_equipment_choices(apps, schema_editor):
    Equipment = apps.get_model('wodtrackr', 'Equipment')
    for value in EQUIPMENT_VALUES:
        Equipment.objects.get_or_create(equipment=value)


class Migration(migrations.Migration):

    dependencies = [
        ('wodtrackr', '0019_alter_equipment_equipment_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_equipment_choices, migrations.RunPython.noop),
    ]
