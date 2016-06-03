import os
from django import template
from django.conf import settings
register = template.Library()

if 'OPENSHIFT_APP_NAME' in os.environ:
    OPENSHIFT_APP_NAME = os.environ['OPENSHIFT_APP_NAME']
    OPENSHIFT_HOMEDIR = os.environ['OPENSHIFT_HOMEDIR']
    with open(os.path.join(OPENSHIFT_HOMEDIR, "git", OPENSHIFT_APP_NAME + ".git", "refs", "heads", "master")) as fh:
        GIT_REVISION = fh.read().decode("utf8") or "unknown"
else:
    with open(os.path.join(".git", "refs", "heads", "master")) as fh:
        GIT_REVISION = fh.read().decode("utf8") or "unknown"

@register.simple_tag
def git_revision():
    return GIT_REVISION
