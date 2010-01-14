from paver.easy import *
import os

options(
    current_env = path(os.environ.get('VIRTUAL_ENV', '.')),
    virtualenv=Bunch(
        packages=["pip",
                  "virtualenv",
                  "urlgrabber"], #not using packages_to_install to
                                 #override default behavior behavior
        install_paver=True,
        script_name='bootstrap.py',
        paver_command_line='after_bootstrap'
        ),
    redis = Bunch(url="http://redis.googlecode.com/files/redis-1.2.0.tar.gz",
                  script="%(venv)/bin/",
                  default_port='',
                  default_conf=''),
    )

@task
def install_build_reqs(options):
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
    from urlgrabber.grabber import urlgrab, URLGrabError
    from urlgrabber.progress import text_progress_meter
    urlgrab(url, dest, progress_obj=text_progress_meter())
    filename, dirname = get_filename_and_dir(url)
    with pushd(dest): #necessary?
        mode = "r:gz"
        tarball = tarfile.open(filename, mode)
        tarball.extractall()
    return path(dest) / dirname


@task
@needs('install_build_reqs')
def install_redis(options):
    dest = options.current_env / 'src'
    filename, dirname = get_filename_and_dir(url)
    redis_dir = dest / dirname
    if not redis_dir.exists():
        redis_dir = grab_unpack(options.redis.url, dest)
        with pushd(redis_dir):
            sh('make')
    else:
        info("%s exists" %redis_dir)

    bin = options.current_env / path('bin')

    server = bin / 'redis-server'
    cli = bin / 'redis-cli'
    if not cli.exists():
        # symlink
        import pdb;pdb.set_trace()
    if not server.exists():
        import pdb;pdb.set_trace()


# add conf flag
@task
@needs('install_redis')
def launch_redis(options):
    sh("redis-server %s" %options.redis.default_config)

try:
    from paver.virtual import bootstrap
except ImportError:
    pass
