from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from emissions.models import Company, UserProfile


class Command(BaseCommand):
    help = 'Create demo company and analyst user with properly hashed password'

    def handle(self, *args, **options):
        company, _ = Company.objects.get_or_create(
            slug='breathe-esg',
            defaults={
                'name': 'Breathe ESG'
            }
        )

        # Get or create user with empty defaults
        user, created = User.objects.get_or_create(
            username='analyst',
            defaults={
                'email': 'analyst@acme.com',
                'first_name': 'Demo',
                'last_name': 'Analyst',
            }
        )

        # Properly hash and set password
        user.set_password('password123')
        user.is_staff = True
        user.save()

        # Ensure UserProfile exists
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'company': company}
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    'Demo user created: analyst / password123'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    'Demo user updated with hashed password: analyst / password123'
                )
            )