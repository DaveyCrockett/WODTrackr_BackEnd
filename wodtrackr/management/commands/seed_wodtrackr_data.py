from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings
from django.db import transaction
from django.utils.dateparse import parse_datetime
from pathlib import Path
import json
import shutil
import sys

from wodtrackr.models import Exercise


class Command(BaseCommand):
    help = "Seed Exercise rows from the ExerciseDataset JSON and copy media assets into MEDIA_ROOT."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow seeding even when DEBUG is False.",
        )
        parser.add_argument(
            "--dataset-root",
            default="",
            help="Absolute path to exercises-dataset root. If omitted, auto-detects sibling ExerciseDataset folder.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Optional number of records to import. 0 imports all records.",
        )
        parser.add_argument(
            "--skip-media-copy",
            action="store_true",
            help="Do not copy images/videos to MEDIA_ROOT; only seed database rows.",
        )

    def handle(self, *args, **options):
        is_test = any(arg.startswith("test") for arg in sys.argv)
        if not (settings.DEBUG or is_test or options.get("force")):
            raise CommandError("Seeding is allowed only in DEBUG/test environments. Use --force to override.")

        dataset_root = self._resolve_dataset_root(options.get("dataset_root", ""))
        dataset_file = dataset_root / "data" / "exercises.json"
        if not dataset_file.exists():
            raise CommandError(f"Dataset file not found: {dataset_file}")

        try:
            with dataset_file.open("r", encoding="utf-8") as f:
                exercises_payload = json.load(f)
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in dataset file: {exc}")

        if not isinstance(exercises_payload, list):
            raise CommandError("Expected exercises.json to contain a top-level JSON array.")

        limit = options.get("limit", 0)
        if limit and limit > 0:
            exercises_payload = exercises_payload[:limit]

        copy_media = not options.get("skip_media_copy", False)
        images_src_root = dataset_root / "images"
        videos_src_root = dataset_root / "videos"
        images_dst_root = Path(settings.MEDIA_ROOT) / "exercise_dataset" / "images"
        videos_dst_root = Path(settings.MEDIA_ROOT) / "exercise_dataset" / "videos"
        if copy_media:
            images_dst_root.mkdir(parents=True, exist_ok=True)
            videos_dst_root.mkdir(parents=True, exist_ok=True)

        with transaction.atomic():
            admin_user = self._get_or_create_user(
                username="dev_admin",
                email="dev_admin@example.com",
                password="dev_password_123",
                is_staff=True,
            )
            created_count = 0
            updated_count = 0
            copied_images = 0
            copied_videos = 0

            for payload in exercises_payload:
                dataset_id = (payload.get("id") or "").strip()
                name = (payload.get("name") or "").strip()
                if not dataset_id or not name:
                    continue

                raw_image = (payload.get("image") or "").strip()
                raw_gif = (payload.get("gif_url") or "").strip()
                image_value = raw_image
                gif_value = raw_gif

                if copy_media and raw_image:
                    src_image = dataset_root / raw_image
                    if src_image.exists() and src_image.is_file():
                        dst_image = images_dst_root / src_image.name
                        if not dst_image.exists():
                            shutil.copy2(src_image, dst_image)
                            copied_images += 1
                        image_value = f"{settings.MEDIA_URL.rstrip('/')}/exercise_dataset/images/{src_image.name}"

                if copy_media and raw_gif:
                    src_gif = dataset_root / raw_gif
                    if src_gif.exists() and src_gif.is_file():
                        dst_gif = videos_dst_root / src_gif.name
                        if not dst_gif.exists():
                            shutil.copy2(src_gif, dst_gif)
                            copied_videos += 1
                        gif_value = f"{settings.MEDIA_URL.rstrip('/')}/exercise_dataset/videos/{src_gif.name}"

                defaults = {
                    "name": name,
                    "category": payload.get("category") or payload.get("body_part"),
                    "body_part": payload.get("body_part") or payload.get("category"),
                    "equipment": payload.get("equipment"),
                    "muscle_group": payload.get("muscle_group"),
                    "secondary_muscles": payload.get("secondary_muscles") or [],
                    "target_muscle": payload.get("target"),
                    "instructions": payload.get("instructions") or {},
                    "instruction_steps": payload.get("instruction_steps") or {},
                    "media_id": payload.get("media_id"),
                    "image_url": image_value,
                    "image_upload": None,
                    "gif_url": gif_value,
                    "attribution": payload.get("attribution") or "",
                    "dataset_created_at": parse_datetime(payload.get("created_at") or "") if payload.get("created_at") else None,
                    "created_by": admin_user,
                    "is_public": True,
                }

                existing = Exercise.objects.filter(dataset_id=dataset_id).first()
                if existing is None:
                    existing = Exercise.objects.filter(name__iexact=name).first()

                if existing is not None:
                    for field_name, field_value in defaults.items():
                        setattr(existing, field_name, field_value)
                    existing.dataset_id = dataset_id
                    existing.save()
                    updated_count += 1
                else:
                    Exercise.objects.create(dataset_id=dataset_id, **defaults)
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Exercise dataset import complete. created={created_count}, updated={updated_count}, copied_images={copied_images}, copied_videos={copied_videos}"
            )
        )

    def _resolve_dataset_root(self, explicit_dataset_root):
        if explicit_dataset_root:
            resolved = Path(explicit_dataset_root).expanduser().resolve()
            if resolved.exists() and resolved.is_dir():
                return resolved
            raise CommandError(f"Invalid --dataset-root path: {explicit_dataset_root}")

        candidates = [
            Path(settings.BASE_DIR).parent / "ExerciseDataset" / "exercises-dataset",
            Path(settings.BASE_DIR) / "ExerciseDataset" / "exercises-dataset",
        ]
        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                return candidate

        raise CommandError(
            "Could not find ExerciseDataset folder automatically. Pass --dataset-root with the absolute path to exercises-dataset."
        )

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
