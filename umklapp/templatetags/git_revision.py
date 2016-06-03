from django import template
register = template.Library()

with open(".git/refs/heads/master") as fh:
    GIT_REVISION = fh.read().decode("utf8") or "unknown"

@register.simple_tag
def git_revision():
    return GIT_REVISION
