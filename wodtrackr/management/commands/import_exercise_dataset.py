import json
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_datetime

from wodtrackr.models import Exercise


class Command(BaseCommand):
    help = "Import full exercise dataset JSON into wodtrackr.Exercise."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default="../ExerciseDataset/exercises-dataset/data/exercises.json",
            help="Path to exercises JSON file.",
        )
        parser.add_argument(
            "--owner",
            type=str,
            default="",
            help="Optional username to set as created_by for imported exercises.",
        )
        parser.add_argument(
            "--private",
            action="store_true",
            help="Import rows as private (default is public).",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Skip updates for existing rows and only create missing rows.",
        )

    def handle(self, *args, **options):
        file_path = Path(options["path"]).expanduser().resolve()
        if not file_path.exists():
            raise CommandError(f"Dataset file not found: {file_path}")

        owner_username = str(options.get("owner") or "").strip()
        owner = self._resolve_owner(owner_username)
        is_public = not options.get("private", False)
        skip_existing = bool(options.get("skip_existing", False))

        try:
            with file_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in dataset file: {exc}") from exc

        if not isinstance(payload, list):
            raise CommandError("Dataset payload must be a JSON array.")

        created_count = 0
        updated_count = 0
        skipped_count = 0
        invalid_count = 0

        with transaction.atomic():
            for index, raw_item in enumerate(payload, start=1):
                if not isinstance(raw_item, dict):
                    invalid_count += 1
                    self.stderr.write(f"Skipping non-object row at index {index}.")
                    continue

                normalized = self._normalize_item(raw_item, owner=owner, is_public=is_public)
                name = normalized.get("name")
                if not name:
                    invalid_count += 1
                    self.stderr.write(f"Skipping row {index} with empty name.")
                    continue

                dataset_id = normalized.get("dataset_id")
                exercise = self._find_existing(dataset_id=dataset_id, name=name)

                if exercise is None:
                    Exercise.objects.create(**normalized)
                    created_count += 1
                    continue

                if skip_existing:
                    skipped_count += 1
                    continue

                for field_name, field_value in normalized.items():
                    setattr(exercise, field_name, field_value)
                exercise.save()
                updated_count += 1

        total_count = Exercise.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"Import complete. created={created_count}, updated={updated_count}, "
                    f"skipped={skipped_count}, invalid={invalid_count}, total={total_count}"
                )
            )
        )

    def _resolve_owner(self, owner_username):
        if owner_username:
            try:
                return User.objects.get(username=owner_username)
            except User.DoesNotExist as exc:
                raise CommandError(f"Owner user not found: {owner_username}") from exc

        default_owner = User.objects.filter(is_staff=True).order_by("id").first()
        if default_owner:
            return default_owner

        return None

    def _normalize_item(self, item, owner, is_public):
        raw_name = str(item.get("name") or "").strip()
        name = raw_name[:120]

        dataset_id = str(item.get("id") or "").strip() or None
        if dataset_id and len(dataset_id) > 16:
            dataset_id = dataset_id[:16]

        created_at_raw = item.get("created_at")
        dataset_created_at = parse_datetime(created_at_raw) if isinstance(created_at_raw, str) else None

        return {
            "dataset_id": dataset_id,
            "name": name,
            "category": self._to_nullable_string(item.get("category"), max_len=100),
            "body_part": self._to_nullable_string(item.get("body_part"), max_len=100),
            "equipment": self._to_nullable_string(item.get("equipment"), max_len=100),
            "muscle_group": self._to_nullable_string(item.get("muscle_group"), max_len=120),
            "secondary_muscles": self._to_string_list(item.get("secondary_muscles")),
            "target_muscle": self._to_nullable_string(item.get("target"), max_len=100),
            "instructions": item.get("instructions") if isinstance(item.get("instructions"), dict) else None,
            "instruction_steps": item.get("instruction_steps") if isinstance(item.get("instruction_steps"), dict) else None,
            "media_id": self._to_nullable_string(item.get("media_id"), max_len=64),
            "image": self._to_nullable_string(item.get("image"), max_len=500),
            "gif_url": self._to_nullable_string(item.get("gif_url"), max_len=500),
            "attribution": self._to_nullable_string(item.get("attribution"), max_len=255),
            "dataset_created_at": dataset_created_at,
            "created_by": owner,
            "is_public": is_public,
        }

    def _find_existing(self, dataset_id, name):
        if dataset_id:
            existing = Exercise.objects.filter(dataset_id=dataset_id).first()
            if existing:
                return existing

        return Exercise.objects.filter(name__iexact=name).first()

    def _to_nullable_string(self, value, max_len):
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        return text[:max_len]

    def _to_string_list(self, value):
        if not isinstance(value, list):
            return []
        result = []
        for entry in value:
            text = str(entry).strip()
            if text:
                result.append(text)
        return result
