# login/management/commands/clear_sessions.py
from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session

class Command(BaseCommand):
    help = "Supprime toutes les sessions"

    def handle(self, *args, **kwargs):
        Session.objects.all().delete()
        self.stdout.write("Toutes les sessions ont été supprimées.")

