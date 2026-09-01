from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings
from django.db import transaction
import sys

from wodtrackr.models import Exercise


class Command(BaseCommand):
    help = "Seed example Exercise rows aligned with the ExerciseDataset schema."

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
                    "dataset_id": "9001",
                    "category": "upper legs",
                    "body_part": "upper legs",
                    "equipment": "barbell",
                    "muscle_group": "quadriceps",
                    "secondary_muscles": ["glutes", "hamstrings", "core"],
                    "target_muscle": "quadriceps",
                    "instructions": {
                        "en": "Set the bar on your upper back, brace your core, squat until hip crease passes knees, then stand back up.",
                    },
                    "instruction_steps": {
                        "en": [
                            "Set barbell across upper back and stand tall.",
                            "Brace core and descend by bending hips and knees.",
                            "Reach full depth and drive up through the mid-foot.",
                        ]
                    },
                    "media_id": "sampleBackSquat",
                    "image": "images/sample-backsquat.jpg",
                    "gif_url": "videos/sample-backsquat.gif",
                    "attribution": "© Gym visual - https://gymvisual.com/",
                    "created_by": admin_user,
                    "is_public": True,
                },
            )

            Exercise.objects.get_or_create(
                name="Ring Row",
                defaults={
                    "dataset_id": "9002",
                    "category": "back",
                    "body_part": "back",
                    "equipment": "body weight",
                    "muscle_group": "lats",
                    "secondary_muscles": ["rhomboids", "biceps"],
                    "target_muscle": "lats",
                    "instructions": {
                        "en": "Keep your body rigid, pull chest toward rings, then lower with control.",
                    },
                    "instruction_steps": {
                        "en": [
                            "Grip rings with straight body and heels anchored.",
                            "Pull elbows back until chest reaches the rings.",
                            "Lower under control while maintaining a rigid torso.",
                        ]
                    },
                    "media_id": "sampleRingRow",
                    "image": "images/sample-ringrow.jpg",
                    "gif_url": "videos/sample-ringrow.gif",
                    "attribution": "© Gym visual - https://gymvisual.com/",
                    "created_by": dev_user,
                    "is_public": True,
                },
            )

            Exercise.objects.get_or_create(
                name="Air Bike Sprint",
                defaults={
                    "dataset_id": "9003",
                    "category": "cardio",
                    "body_part": "cardio",
                    "equipment": "bike",
                    "muscle_group": "cardiovascular system",
                    "secondary_muscles": ["quads", "glutes", "shoulders"],
                    "target_muscle": "full body",
                    "instructions": {
                        "en": "Sprint hard for the interval, breathe rhythmically, and recover at low cadence between efforts.",
                    },
                    "instruction_steps": {
                        "en": [
                            "Adjust seat and grip for full leg extension.",
                            "Accelerate to max sustainable cadence.",
                            "Recover at easy pace before the next sprint.",
                        ]
                    },
                    "media_id": "sampleAirBikeSprint",
                    "image": "images/sample-airbike.jpg",
                    "gif_url": "videos/sample-airbike.gif",
                    "attribution": "© Gym visual - https://gymvisual.com/",
                    "created_by": admin_user,
                    "is_public": True,
                },
            )

        self.stdout.write(self.style.SUCCESS(f"Seed data created or already exists. Primary record id={public_exercise.id}"))

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
