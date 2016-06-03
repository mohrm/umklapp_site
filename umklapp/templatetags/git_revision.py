import os
from django import template
from django.conf import settings
register = template.Library()

with open(os.path.join(settings.BASE_DIR, ".git", "refs", "heads", "master")) as fh:
    GIT_REVISION = fh.read().decode("utf8") or "unknown"

@register.simple_tag
def git_revision():
    return GIT_REVISION
