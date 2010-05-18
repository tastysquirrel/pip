import sys, os
from subprocess import check_call, PIPE
from path import Path
import shutil
from tempfile import mkdtemp, gettempdir

exe = '.EXE' if sys.platform == 'win32' else ''

def create_virtualenv(where):
    save_argv = sys.argv
    
    try:
        import virtualenv
        sys.argv = ['virtualenv', '--quiet', '--no-site-packages', where]
        virtualenv.main()
    finally: 
        sys.argv = save_argv

    return virtualenv.path_locations(where)

def rmtree(path):
    # From pathutils by Michael Foord: http://www.voidspace.org.uk/python/pathutils.html
    def onerror(func, path, exc_info):
        """
        Error handler for ``shutil.rmtree``.

        If the error is due to an access error (read only file)
        it attempts to add write permission and then retries.

        If the error is for another reason it re-raises the error.

        Usage : ``shutil.rmtree(path, onerror=onerror)``

        """
        import stat
        if not os.access(path, os.W_OK):
            # Is the error an access error ?
            os.chmod(path, stat.S_IWUSR)
            func(path)
        else:
            raise

    if Path(path).exists:
        shutil.rmtree(path, onerror=onerror)

def system(*args):
    check_call(args, stdout=PIPE, shell=(sys.platform=='win32'))

def call(*args):
    check_call(args)

def assert_in_path(exe):
    system(exe, '--version')

def main(argv):
    here = Path(sys.path[0])
    script_name = Path(__file__).name

    if not (here/script_name).exists:
        here = Path(__file__).abspath.folder
        assert (here/script_name).exists, "Can't locate directory of this script"

    # Make sure all external tools are set up to be used.
    print >> sys.stderr, 'Checking for installed prerequisites in PATH:',
    for tool in 'git', 'hg', 'bzr', 'svn':
        print >> sys.stderr, tool,'...',
        assert_in_path(tool)
    print >> sys.stderr, 'ok'

    pip_root = here.folder

    #
    # Delete everything that could lead to stale test results
    #
    print >> sys.stderr, 'Cleaning ...',
    for dirpath, dirnames, filenames in os.walk(pip_root):
        for f in filenames:
            if f.endswith('.pyc'):
                os.unlink(Path(dirpath)/f)
    rmtree(pip_root/'build')
    rmtree(pip_root/'dist')
    print >> sys.stderr, 'ok'
    
    save_dir = os.getcwd()
    temp_dir = mkdtemp('-pip_auto_test')
    try:
        os.chdir(temp_dir)

        #
        # Prepare a clean, writable workspace
        #
        print >> sys.stderr, 'Preparing test environment ...',
        venv, lib, include, bin = create_virtualenv(temp_dir)

        abs_bin = Path(bin).abspath

        # Make sure it's first in PATH
        os.environ['PATH'] = str(
            Path.pathsep.join(( abs_bin, os.environ['PATH'] ))
            )

        #
        # Install python module testing prerequisites
        #
        pip = abs_bin/'pip'+exe
        download_cache = '--download-cache=' \
            + Path(gettempdir())/'pip-test-download-cache'
        call(pip, 'install', '-q', download_cache, 'virtualenv')
        call(pip, 'install', '-q', download_cache, 'nose')
        # for now, we need a pre-release version of scripttest
        call(pip, 'install', '-q', download_cache, 'scripttest')
        print >> sys.stderr, 'ok'
        nosetests = abs_bin/'nosetests'+exe
        call( nosetests, '-w', pip_root/'tests', *argv[1:] )

    finally:
        os.chdir(save_dir)
        rmtree(temp_dir)


if __name__ == '__main__':
    main( sys.argv )