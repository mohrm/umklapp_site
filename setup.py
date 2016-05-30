import os
from setuptools import setup, find_packages

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

setup(name='Umklapp',
      version='1.0',
      author='Martin Mohr',
      author_email='martin.mohr@posteo.de',
      url='http://github.com/mohrm/umklapp_site',
      packages=find_packages(),
      include_package_data=True,
      description='A Story-Continuation Game',
      install_requires=open('%s/requirements.txt' %
                            os.environ.get('OPENSHIFT_REPO_DIR',
                                           PROJECT_ROOT
                                          )
                           ).readlines(),
     )
