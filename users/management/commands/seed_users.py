from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserProfile
from django.db import transaction


class Command(BaseCommand):
    help = 'Seeds initial admin and test user data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing test users before seeding',
        )

    def handle(self, *args, **options):
        """Seed initial user data"""
        
        if options['reset']:
            self.stdout.write(self.style.WARNING('Resetting test users...'))
            User.objects.filter(username__in=['admin', 'testuser', 'coach']).delete()
        
        users_created = 0
        
        with transaction.atomic():
            # Create admin user
            admin_user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@wodtrackr.com',
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            if created:
                admin_user.set_password('admin123')
                admin_user.save()
                UserProfile.objects.get_or_create(
                    user=admin_user,
                    defaults={
                        'role': 'admin',
                        'verified': True,
                        'bio': 'System Administrator',
                    }
                )
                users_created += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created admin user: admin / admin123'))
            else:
                self.stdout.write(self.style.WARNING(f'Admin user already exists'))
            
            # Create test user
            test_user, created = User.objects.get_or_create(
                username='testuser',
                defaults={
                    'email': 'testuser@wodtrackr.com',
                    'first_name': 'Test',
                    'last_name': 'User',
                }
            )
            if created:
                test_user.set_password('testpass123')
                test_user.save()
                UserProfile.objects.get_or_create(
                    user=test_user,
                    defaults={
                        'role': 'user',
                        'verified': True,
                        'bio': 'Regular test user',
                    }
                )
                users_created += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created test user: testuser / testpass123'))
            else:
                self.stdout.write(self.style.WARNING(f'Test user already exists'))
            
            # Create coach user
            coach_user, created = User.objects.get_or_create(
                username='coach',
                defaults={
                    'email': 'coach@wodtrackr.com',
                    'first_name': 'Coach',
                    'last_name': 'Smith',
                }
            )
            if created:
                coach_user.set_password('coach123')
                coach_user.save()
                UserProfile.objects.get_or_create(
                    user=coach_user,
                    defaults={
                        'role': 'coach',
                        'verified': True,
                        'bio': 'Certified CrossFit Coach',
                    }
                )
                users_created += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created coach user: coach / coach123'))
            else:
                self.stdout.write(self.style.WARNING(f'Coach user already exists'))
        
        if users_created > 0:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully created {users_created} new user(s)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✓ All seed users already exist'))
        
        self.stdout.write(self.style.SUCCESS('\nAvailable test accounts:'))
        self.stdout.write('  Admin:    admin / admin123')
        self.stdout.write('  Coach:    coach / coach123')
        self.stdout.write('  User:     testuser / testpass123')
