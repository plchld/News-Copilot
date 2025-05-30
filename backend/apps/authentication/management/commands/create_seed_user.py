from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Create seed users for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='admin@newscopilot.com',
            help='Email for the admin user'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123!',
            help='Password for the admin user'
        )
        parser.add_argument(
            '--create-test-users',
            action='store_true',
            help='Create additional test users'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        
        # Create or update admin user
        admin_user, created = User.objects.update_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'first_name': 'Admin',
                'last_name': 'User'
            }
        )
        
        if created:
            admin_user.set_password(password)
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Admin user created: {email}'))
        else:
            admin_user.set_password(password)
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Admin user updated: {email}'))
        
        # Create test users if requested
        if options['create_test_users']:
            test_users = [
                {
                    'email': 'user@newscopilot.com',
                    'username': 'user',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'is_staff': False,
                    'is_superuser': False,
                },
                {
                    'email': 'premium@newscopilot.com',
                    'username': 'premium',
                    'first_name': 'Premium',
                    'last_name': 'User',
                    'is_staff': False,
                    'is_superuser': False,
                }
            ]
            
            for user_data in test_users:
                user, created = User.objects.update_or_create(
                    email=user_data['email'],
                    defaults=user_data
                )
                if created:
                    user.set_password('user123!')
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'Test user created: {user_data["email"]}'))
        
        self.stdout.write(self.style.SUCCESS('\nSeed users created successfully!'))
        self.stdout.write(self.style.SUCCESS(f'Admin login: {email} / {password}'))
        if options['create_test_users']:
            self.stdout.write(self.style.SUCCESS('Test users: user@newscopilot.com / user123!'))
            self.stdout.write(self.style.SUCCESS('           premium@newscopilot.com / user123!'))