from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from umklapp.models import Story
import django.utils.timezone

class Command(BaseCommand):
    help = 'Auto-Skips all stories that are too old'

    def handle(self, *args, **options):
        if not settings.AUTOSKIP:
            self.stdout.write(self.style.WARNING('AUTOSKIP not set'))
            return

        # pre-filter stories, although try_autoskip repeats the check, for
        # efficiency.
        for s in Story.objects.filter(last_action__lt = django.utils.timezone.now() - settings.AUTOSKIP):
            if s.try_autoskip():
                self.stdout.write(self.style.SUCCESS('Auto-skipping %s' % s))
