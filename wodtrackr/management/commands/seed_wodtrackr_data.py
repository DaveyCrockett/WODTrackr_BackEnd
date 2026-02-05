from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings
from django.db import transaction
import sys

from wodtrackr.models import Exercise, CustomExercise, ExerciseNote


class Command(BaseCommand):
    help = "Seed example custom exercises and exercise notes for development/test environments."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow seeding even when DEBUG is False.",
        )

    def handle(self, *args, **options):
        is_test = any(arg.startswith("test") for arg in sys.argv)
        if not (settings.DEBUG or is_test or options.get("force")):
            raise CommandError("Seeding is allowed only in DEBUG/test environments. Use --force to override.")

        with transaction.atomic():
            dev_user = self._get_or_create_user(
                username="dev_user",
                email="dev_user@example.com",
                password="dev_password_123",
                is_staff=False,
            )
            admin_user = self._get_or_create_user(
                username="dev_admin",
                email="dev_admin@example.com",
                password="dev_password_123",
                is_staff=True,
            )

            public_exercise, _ = Exercise.objects.get_or_create(
                name="Back Squat",
                defaults={
                    "description": "Classic barbell squat",
                    "category": "weightlifting",
                    "equipment": "barbell",
                    "primary_muscle_group": "legs",
                    "created_by": admin_user,
                    "is_public": True,
                },
            )

            custom_1, _ = CustomExercise.objects.get_or_create(
                created_by=dev_user,
                title="Tempo Front Squat",
                defaults={
                    "description": "3s descent, 1s pause at bottom",
                    "category": "weightlifting",
                    "equipment": "barbell",
                    "primary_muscle_group": "legs",
                },
            )

            custom_2, _ = CustomExercise.objects.get_or_create(
                created_by=admin_user,
                title="Ring Rows - Pause",
                defaults={
                    "description": "Pause 2s at top of each rep",
                    "category": "gymnastics",
                    "equipment": "rings",
                    "primary_muscle_group": "back",
                },
            )

            ExerciseNote.objects.get_or_create(
                user=dev_user,
                exercise=public_exercise,
                defaults={
                    "notes": "Drive through mid-foot and keep chest tall.",
                },
            )

            ExerciseNote.objects.get_or_create(
                user=dev_user,
                custom_exercise=custom_1,
                defaults={
                    "notes": "Use 60% 1RM; focus on tempo control.",
                },
            )

            ExerciseNote.objects.get_or_create(
                user=admin_user,
                custom_exercise=custom_2,
                defaults={
                    "notes": "Keep shoulders packed; pause every rep.",
                },
            )

        self.stdout.write(self.style.SUCCESS("Seed data created or already exists."))

    def _get_or_create_user(self, username, email, password, is_staff=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": is_staff,
                "is_active": True,
            },
        )

        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
        else:
            updates = []
            if user.email != email:
                user.email = email
                updates.append("email")
            if user.is_staff != is_staff:
                user.is_staff = is_staff
                updates.append("is_staff")
            if updates:
                user.save(update_fields=updates)

        return user
