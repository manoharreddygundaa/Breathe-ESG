from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from emissions.models import Company, UserProfile


class Command(BaseCommand):
    help = 'Create demo company and analyst user if they do not exist'

    def handle(self, *args, **options):
        company, _ = Company.objects.get_or_create(
            slug='acme-corp',
            defaults={
                'name': 'Acme Corporation'
            }
        )

        # Only create if analyst doesn't exist
        if User.objects.filter(username='analyst').exists():
            self.stdout.write(
                self.style.SUCCESS(
                    'Demo user already exists: analyst / password123'
                )
            )
            return

        # Create fresh user
        user = User.objects.create_user(
            username='analyst',
            password='password123',
            email='analyst@acme.com',
            first_name='Demo',
            last_name='Analyst',
        )

        user.is_staff = True
        user.save()

        UserProfile.objects.get_or_create(
            user=user,
            defaults={'company': company}
        )

        self.stdout.write(
            self.style.SUCCESS(
                'Demo user created: analyst / password123'
            )
        )