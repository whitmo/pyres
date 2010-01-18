from __future__ import with_statement

from paver.easy import *
from paver import doctools
from paver.setuputils import setup
import os
import tarfile

options(
    sphinx=Bunch(docroot='docs',
                 builddir="_build",
                 sourcedir=""
                 ),
    current_env = path(os.environ.get('VIRTUAL_ENV', '.')),
    virtualenv=Bunch(packages_to_install=["pip"],
                     packages=["virtualenv",
                               "urlgrabber",
                               ], #not using packages_to_install to
                     #override default behavior behavior
                     install_paver=True,
                     script_name='bootstrap.py',
                     paver_command_line='after_bootstrap'
                     ),
    redis = Bunch(url="http://redis.googlecode.com/files/redis-1.2.0.tar.gz",
                  script="%(venv)/bin/",
                  default_port='6379',
                  default_conf=''),
    minilib = Bunch(extra_files=["virtual"])
    )


setup(
    name='pyres',
    version='0.4.1',
    description='Python Resque clone',
    author='Matt George',
    license='MIT',
    author_email='mgeorge@gmail.com',
    url='http://github.com/binarydud/pyres',
    packages=['pyres', 'resweb', 'pyres/failure'],
    package_data={'resweb': ['templates/*.mustache','media/*']},
    scripts=['scripts/pyres_worker', 'scripts/pyres_web'],
    zip_safe = True,
    install_requires=[
        'simplejson>=2.0.9',
        'itty>=0.6.2',
        'redis>=0.6.0',
        'pystache>=0.1.0'
    ],
)


@task
def install_build_reqs(options):
    """
    Installs requirements for building
    """
    for pkg in options.virtualenv.packages:
        sh("pip install %s" %pkg)


@task
@needs('install_build_reqs')
def after_bootstrap(options):
    pass


def get_filename_and_dir(url):
    filename = url.split("/")[-1]
    dirname = filename.split('.tar.gz')[0]
    return filename, dirname


def grab_unpack(url, dest):
    from urlgrabber.grabber import urlgrab
    from urlgrabber.progress import text_progress_meter
    filename, dirname = get_filename_and_dir(url)
    urlgrab(url, dest / filename, progress_obj=text_progress_meter())
    with pushd(dest): #necessary?
        mode = "r:gz"
        tarball = tarfile.open(filename, mode)
        tarball.extractall()
    return path(dest) / dirname


@task
@needs('install_build_reqs')
def install_redis(options):
    """
    Download, unpack and build redis
    """
    dest = options.current_env / 'src'
    filename, dirname = get_filename_and_dir(options.redis.url)
    redis_dir = dest / dirname
    if not redis_dir.exists():
        grab_unpack(options.redis.url, dest)
        with pushd(redis_dir):
            sh('make')
    else:
        info("%s exists" %redis_dir)

    options.redis.redis_dir = redis_dir
    call_task('make_redis_links')


@task
def make_redis_links(options):
    """
    Symlink redis executables into virtualenv bin
    """
    bin = options.current_env / path('bin')    
    server = bin / 'redis-server'
    cli = bin / 'redis-cli'
    dest = options.current_env / 'src'
    filename, dirname = get_filename_and_dir(options.redis.url)
    redis_dir = dest / dirname
    if not cli.exists():
        (redis_dir / 'redis-cli').symlink(cli)
        
    if not server.exists():
        (redis_dir / 'redis-server').symlink(server)


# add conf flag
@task
@needs('install_redis')
def launch_redis(options):
    """
    launches the redis server with default config
    """
    try:
        sh("redis-server %s" %options.redis.default_conf)
    except KeyboardInterrupt:
        info("\nredis exiting")

@task
@needs('install_redis')
def install_w_redis(options):
    """
    Install pyres and redis into your current virtualenv
    """
    call_task('setuptools.command.install')

@task
@needs('install_redis')
def develop_w_redis(options):
    """
    Install pyres as a development install and redis into your current
    virtualenv
    """
    call_task('setuptools.command.develop')


@task
def html(options):
    try:
        import sphinx
    except ImportError:
        sh('pip install sphinx')
    call_task("paver.doctools.html")
html.__doc__ = paver.doctools.html.__doc__


@task
def test(options):
    try:
        import nose
    except ImportError:
        sh('pip install nose')

    call_task('nose.commands.nosetests')
    path('tests/dump.rdb').rm()
    path('tests/redis-test.log').rm()


try:
    from paver.virtual import bootstrap
except ImportError:
    pass
