from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import User, Profile

class Command(BaseCommand):
    help = 'Ensure all users have a Profile object.'

    def handle(self, *args, **options):
        created_count = 0
        for user in User.objects.all():
            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                created_count += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} missing Profile objects.'))
