import os
from django import template
from django.conf import settings
register = template.Library()

def extract_revision_file_from_head_file(gitHeadFileName):
    with open(gitHeadFileName) as fh:
        s = fh.read() or None
        if s.startswith('ref: '):
            return s[5:].strip('\n') or None
        else:
            return s

if 'OPENSHIFT_APP_NAME' in os.environ:
    OPENSHIFT_APP_NAME = os.environ['OPENSHIFT_APP_NAME']
    OPENSHIFT_HOMEDIR = os.environ['OPENSHIFT_HOMEDIR']
    gitBaseDir = os.path.join(OPENSHIFT_HOMEDIR, "git", OPENSHIFT_APP_NAME + ".git")
else:
    gitBaseDir = os.path.join(".git")

gitHeadFileName = os.path.join(gitBaseDir, "HEAD")

gitRevisionFileName = extract_revision_file_from_head_file(gitHeadFileName)
fqGitRevisionFileName = os.path.join(gitBaseDir, gitRevisionFileName)
if os.path.exists(fqGitRevisionFileName):
    with open(fqGitRevisionFileName) as fh:
        GIT_REVISION = fh.read() or "unknown"
else:
    GIT_REVISION = gitRevisionFileName

@register.simple_tag
def git_revision():
    return GIT_REVISION[:7]
