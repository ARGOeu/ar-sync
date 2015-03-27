from distutils.core import setup
import glob

setup(name='argo-egi-connectors',
      version='1.4.0',
      author='SRCE',
      author_email='dvrcic@srce.hr, lgjenero@gmail.com',
      description='Connector between ARGO Compute Engine and GOCDB topology, POEM profiles, ',
      url='http://argoeu.github.io/guides/sync/',
      package_dir={'argo_egi_connectors': 'modules/'},
      packages=['argo_egi_connectors'],
      scripts=glob.glob('bin/*.py'),
      data_files=[('/etc/argo-egi-connectors', glob.glob('etc/*.conf')),
                  ('/etc/argo-egi-connectors/schemas', glob.glob('etc/schemas/*.avsc')),
                  ('/etc/cron.d', glob.glob('cronjobs/*'))])
