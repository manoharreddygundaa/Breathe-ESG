"""
Creates a demo company, analyst user, and sample CSV files for testing.
Run: python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from emissions.models import Company, UserProfile


class Command(BaseCommand):
    help = 'Create demo company and analyst user'

    def handle(self, *args, **options):
        company, _ = Company.objects.get_or_create(
            slug='acme-corp',
            defaults={'name': 'Acme Corporation'}
        )

        user, created = User.objects.get_or_create(
            username='analyst',
            defaults={
                'email': 'analyst@acme.com',
                'first_name': 'Demo',
                'last_name': 'Analyst',
            }
        )
        if created:
            user.set_password('password123')
            user.save()

        UserProfile.objects.get_or_create(user=user, defaults={'company': company})

        self.stdout.write(self.style.SUCCESS(
            f'Demo user created: analyst / password123 (company: {company.name})'
        ))
