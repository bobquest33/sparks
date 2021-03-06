# -*- coding: utf8 -*-

import os
import pwd
import uuid
import logging

from fabric.api              import env, run, sudo, local, task
from fabric.operations       import get, put
from fabric.contrib.console  import confirm
from fabric.decorators       import runs_once
from fabric.contrib.files    import contains, append, exists, sed
from fabric.context_managers import cd, lcd, settings, hide
from fabric.colors           import yellow, cyan

from sparks.fabric import QUIET
from .. import pkg, version as sparks_version
from .utils import (with_remote_configuration,  # dsh_to_roledefs,
                    tilde, symlink, dotfiles)

# ===================================================== Local variables

LOGGER = logging.getLogger(__name__)
local_osx_apps = '~/Downloads/{Mac,OSX}*/'
central_osx_apps = 'duncan:oliviercortes.com/sparks/osx'
is_olive = pwd.getpwuid(os.getuid()).pw_name in ('olive', 'karmak23')

# ================================================ Fabric configuration

env.use_ssh_config = True
env.skip_bad_hosts = True
env.pool_size      = 10
#env.roledefs.update(dsh_to_roledefs())


def info(text):
    print(cyan(text))


def github():
    return 'git@github.com:' if is_olive else 'https://github.com/'

# ====================================================== Fabric targets

# -------------------------------------- Standalone application recipes


@task
@with_remote_configuration
def install_chrome(remote_configuration=None):
    """ Install Google Chrome via .DEB packages from Google. """

    if remote_configuration.is_osx:
        if not exists('/Applications/Google Chrome.app'):
            # TODO: implement me.
            info("Please install Google Chrome manually.")

    else:
        print('XXX on Arch/BSD…')

        if exists('/usr/bin/google-chrome'):
            return

        if remote_configuration.is_ubuntu:
            pkg.apt.key('https://dl-ssl.google.com/linux/linux_signing_key.pub')
            append('/etc/apt/sources.list.d/google-chrome.list',
                   'deb http://dl.google.com/linux/chrome/deb/ stable main',
                   use_sudo=True)
            pkg.pkg_update()
            pkg.pkg_add('google-chrome-stable')


@task
@with_remote_configuration
def install_skype(remote_configuration=None):
    """ Install Skype 32bit via Ubuntu partner repository. """

    if remote_configuration.is_osx:
        if not exists('/Applications/Skype.app'):
            # TODO: implement me.
            info("Please install %s manually." % yellow('Skype'))

    else:
        pkg.apt.ppa_pkg('deb http://archive.canonical.com/ubuntu %s partner'
                        % remote_configuration.lsb.CODENAME,
                        'skype', '/usr/bin/skype')


@task
@with_remote_configuration
def install_bitcoin(remote_configuration=None):
    """ Install Bitcoind via Ubuntu PPA. """

    if remote_configuration.is_osx:
        return

    else:
        if not exists('/etc/apt/sources.list.d/bitcoin-bitcoin-{0}.list'.format(
                      remote_configuration.lsb.CODENAME)):
            pkg.apt.ppa('ppa:bitcoin/bitcoin')

            if exists('/usr/bin/bitcoind'):
                pkg.apt_upgrade()
                LOGGER.warning('You probably need to upgrade your wallet '
                               'with -upgradewallet option.')

            else:
                pkg.apt_add('bitcoind')


@task
@with_remote_configuration
def install_sublime(remote_configuration=None, overwrite=False):
    """ Install Sublime Text 2 in /opt via a downloaded .tar.bz2. """

    if remote_configuration.is_osx:
        if not exists('/Applications/Sublime Text.app'):
            # TODO: implement me.
            info("Please install Sublime Text manually.")

    else:
        if overwrite or not exists('/opt/sublime2'):
            if remote_configuration.uname.machine == 'x86_64':
                url = 'http://c758482.r82.cf2.rackcdn.com/' \
                      + 'Sublime%20Text%202.0.2%20x64.tar.bz2'

            else:
                url = 'http://c758482.r82.cf2.rackcdn.com/' \
                      + 'Sublime%20Text%202.0.2.tar.bz2'

            run('wget -q -O /var/tmp/sublime.tar.bz2 %s' % url, quiet=QUIET)

            with cd('/opt'):
                sudo('tar -xjf /var/tmp/sublime.tar.bz2', quiet=QUIET)
                sudo('mv "Sublime Text 2" sublime2', quiet=QUIET)

        executable = tilde('bin/sublime')

        if overwrite or not exists(executable):
            run('echo -e "#!/bin/sh\ncd /opt/sublime2\n./sublime_text\n" > %s'
                % executable, quiet=QUIET)

        # Always be sure the executable *IS* executable ;-)
        run('chmod 755 %s' % executable, quiet=QUIET)

        if overwrite or not exists('/usr/share/applications/sublime2.desktop'):
            put(os.path.join(os.path.expanduser('~'), 'Dropbox',
                'configuration', 'data', 'sublime2.desktop'),
                '/usr/share/applications', use_sudo=True)


@task
@with_remote_configuration
def install_spotify(remote_configuration=None, overwrite=False):
    """ Install on Linux via the Labs repository. """

    if remote_configuration.is_osx:
        if not exists('/Applications/Spotify.app'):
            info("Please install Spotify manually.")

    else:
        if overwrite or not exists('/usr/bin/spotify'):

            sudo(u'apt-key adv --keyserver keyserver.ubuntu.com '
                 u'--recv-keys 94558F59', quiet=QUIET)

            append('/etc/apt/sources.list.d/spotify.list',
                   'deb http://repository.spotify.com stable non-free',
                   use_sudo=True)

            pkg.apt_update()
            pkg.apt_add('spotify-client')


@task
@with_remote_configuration
def install_homebrew(remote_configuration=None):
    """ Install Homebrew on OSX from http://mxcl.github.com/homebrew/ """

    if not remote_configuration.is_osx:
        return

    if exists('/usr/local/bin/brew'):

        if confirm('Update Brew Formulæ?', default=False):
            pkg.brew_update()

        if confirm('Upgrade outdated Brew packages?',
                   default=False):
            pkg.brew_upgrade()

    else:
        sudo('ruby -e "$(curl -fsSL https://raw.github.com/mxcl/homebrew/go)"',
             quiet=QUIET)

        sudo('brew doctor', quiet=QUIET)
        pkg.pkg_add(('git', ))

        # TODO: implement this.
        info('Please install OSX CLI tools for Xcode manually.')

        if confirm('Is the installation OK?'):
            pkg.brew_update()

    LOGGER.warning('You still have to install Xcode and its CLI tools.')


@task
@with_remote_configuration
def install_1password(remote_configuration=None):
    """ NOT IMPLEMENTED: Install 1Password. """

    if remote_configuration.is_osx:
        if not exists('/Applications/1Password.app'):
            info('Please install %s manually.' % yellow('1Password'))

    else:
        # TODO: implement me
        pkg.apt_add('wine')


@task
@with_remote_configuration
def install_powerline(remote_configuration=None):
    """ Install the Ubuntu Mono patched font and powerline. """

    if remote_configuration.is_osx:
        if not exists(tilde('Library/Fonts/UbuntuMono-B-Powerline.ttf')):
            git_clone_or_update('ubuntu-mono-powerline-ttf',
                                'https://github.com/pdf/'
                                'ubuntu-mono-powerline-ttf.git')

            with cd(tilde('sources')):
                run('cp ubuntu-mono-powerline-ttf/*.ttf %s'
                    % tilde('Library/Fonts'), quiet=QUIET)

    else:
        if not exists(tilde('.fonts/ubuntu-mono-powerline-ttf')):
            run('git clone https://github.com/pdf/ubuntu-mono-powerline-ttf.git'
                ' ~/.fonts/ubuntu-mono-powerline-ttf', quiet=QUIET)
            run('fc-cache -vf', warn_only=True, quiet=QUIET)

    git_clone_or_update('powerline-shell',
                        '{0}Karmak23/powerline-shell.git'.format(github()))

# ---------------------------------------------------- Sysadmin recipes


@task
@with_remote_configuration
def test(remote_configuration=None):
    """ Just run `uname -a; uptime` remotely, to test the connection,
        and the sparks remote detection engine. """

    run('uname -a; uptime; echo $USER — $PWD — Sparks v%s' % sparks_version,
        quiet=QUIET)


@task
@with_remote_configuration
def sys_easy_sudo(remote_configuration=None):
    """ Allow sudo to run without password for @sudo members. """

    LOGGER.info('Checking sys_easy_sudo()…')

    if remote_configuration.is_osx:
        # GNU sed is needed for fabric `sed` command to succeed.
        pkg.pkg_add('gnu-sed')
        symlink('/usr/local/bin/gsed', '/usr/local/bin/sed')

        sudoers = '/private/etc/sudoers'
        group   = 'admin'

    else:
        # Debian / Ubuntu
        sudoers = '/etc/sudoers'
        group   = 'sudo'

    with settings(hide('warnings', 'running',
                  'stdout', 'stderr'), warn_only=True):
        sed(sudoers,
            '%%%s\s+ALL\s*=\s*\(ALL(:ALL)?\)\s+ALL' % group,
            '%%%s    ALL = (ALL:ALL) NOPASSWD: ALL' % group,
            use_sudo=True, backup='.bak')


@task
@with_remote_configuration
def sys_unattended(remote_configuration=None):
    """ Install unattended-upgrades and set it up for daily auto-run. """

    if remote_configuration.is_osx:
        info("Skipped unattended-upgrades (not on LSB).")
        return

    if not remote_configuration.is_arch:
        pkg.apt_add('unattended-upgrades')

    # always install the files, in case they
    # already exist and have different contents.
    put(os.path.join(os.path.expanduser('~'), 'Dropbox', 'configuration',
        'data', 'uu-periodic.conf'),
        '/etc/apt/apt.conf.d/10periodic', use_sudo=True)
    put(os.path.join(os.path.expanduser('~'), 'Dropbox', 'configuration',
        'data', 'uu-upgrades.conf'),
        '/etc/apt/apt.conf.d/50unattended-upgrades', use_sudo=True)

    # Too long. It will be done by CRON anyway.
    #sudo('unattended-upgrades', quiet=QUIET)


@task
@with_remote_configuration
def sys_del_useless(remote_configuration=None):
    """ Remove useless or annoying packages (LSB only).

        .. note:: cannot remove these, they remove world: ``at-spi2-core``
            ``qt-at-spi``.
    """

    if remote_configuration.is_osx:
        return

    LOGGER.info('Checking sys_del_useless() components…')

    if remote_configuration.lsb and not remote_configuration.is_arch:
        pkg.pkg_del(('apport', 'python-apport',
                    'landscape-client-ui-install', 'gnome-orca',
                    'brltty', 'libbrlapi0.5', 'python3-brlapi',
                    'python-brlapi', 'ubuntuone-client',
                    'ubuntuone-control-panel', 'rhythmbox-ubuntuone',
                    'python-ubuntuone-client', ))


@task
@with_remote_configuration
def sys_low_resources_purge(remote_configuration=None):
    """ Remove more packages on a low-resource system (LSB only). """

    if remote_configuration.is_osx:
        return

    LOGGER.info('Removing packages for a low-resource system…')

    if remote_configuration.lsb and not remote_configuration.is_arch:
        pkg.pkg_del(('bluez', 'blueman', 'oneconf', 'colord',
                     'zeitgeist', ))


@task
@with_remote_configuration
def sys_default_services(remote_configuration=None):
    """ Activate some system services I need / use. """

    if remote_configuration.is_osx:
        # Activate locate on OSX.
        sudo('launchctl load -w '
             '/System/Library/LaunchDaemons/com.apple.locate.plist',
             quiet=QUIET)


@task
@with_remote_configuration
def sys_admin_pkgs(remote_configuration=None):
    """ Install some sysadmin related applications. """

    pkg.pkg_add(('wget', 'multitail', ))

    if remote_configuration.is_osx:
        # See https://github.com/mperham/lunchy
        pkg.gem_add(('lunchy', ))

    elif remote_configuration.lsb:
        pkg.pkg_add(('fail2ban', 'acl', 'attr',
                    'colordiff', 'telnet', 'psmisc', 'host',
                     'duply', 'ncftp', 'arptables', 'iptables', ))

    else:
        raise NotImplementedError('implement sysadmin pkgs for BSD.')


@task
@with_remote_configuration
def sys_ssh_powerline(remote_configuration=None):
    """ Make remote SSHd accept the POWERLINE_SHELL environment variable. """

    git_clone_or_update('powerline-shell',
                        '{0}Karmak23/powerline-shell.git'.format(github()))

    if remote_configuration.is_osx:
        # No need to reload on OSX, cf. http://superuser.com/q/478035/206338
        config     = '/private/etc/sshd_config'
        reload_ssh = None

    else:
        config     = '/etc/ssh/sshd_config'
        reload_ssh = 'reload ssh'

    if not contains(config, 'AcceptEnv.*POWERLINE_SHELL', use_sudo=True):
        append(config, 'AcceptEnv POWERLINE_SHELL', use_sudo=True)
        if reload_ssh:
            sudo(reload_ssh, quiet=QUIET)


@task
@with_remote_configuration
def sys_mongodb(remote_configuration=None):
    """ Install the MongoDB APT repository if on Ubuntu and 12.04. """

    if remote_configuration.is_ubuntu:
        major_distro_version = \
            int(remote_configuration.lsb.RELEASE.split('.')[0])

        if major_distro_version < 12:
            LOGGER.warning('Unsupported (too old) Ubuntu version for MongoDB.')

        elif major_distro_version in (12, 13):
            if not exists('/etc/apt/sources.list.d/10gen.list'):
                sudo('apt-key adv --keyserver keyserver.ubuntu.com '
                     '--recv 7F0CEB10', quiet=QUIET)
                append('/etc/apt/sources.list.d/10gen.list',
                       'deb http://downloads-distro.mongodb.org/'
                       'repo/ubuntu-upstart dist 10gen', use_sudo=True)
                pkg.apt_update()
            return 'mongodb-10gen'
        else:
            LOGGER.warning('Installing mongodb package, hope this is the good '
                           'version!')
            return 'mongodb'

    elif remote_configuration.lsb.ID.lower() == 'debian':
        return 'mongodb'

    else:
        print('MongoDB install not implemented on anything else than '
              'Ubuntu. Please submit a patch.')


@task(aliases=('lperms', ))
@with_remote_configuration
def local_perms(remote_configuration=None):
    """ Re-apply correct permissions on well-known files (eg .ssh/*) """

    with lcd(tilde()):
        local('chmod 700 .ssh; chmod 600 .ssh/*', capture=QUIET)


@task(aliases=('dupe_perms', 'dupe_acls', 'acls', ))
@with_remote_configuration
def replicate_acls(remote_configuration=None,
                   origin=None, path=None, apply=False):
    """ Replicate locally the ACLs and Unix permissions of a given path on
        a remote machine. When everything is borked locally, and you have
        a remote clone in a good health, this is handy.

        This helps correcting strange permissions errors from a well-known
        good machine.

        Usage:

            fab … acls:origin=10.0.3.37,path=/bin
            # Then:
            fab … acls:origin=10.0.3.37,path=/bin,apply=True
    """

    if origin is None or path is None:
        raise ValueError('Missing arguments')

    sys_admin_pkgs()

    local_perms_file  = str(uuid.uuid4())
    remote_perms_file = str(uuid.uuid4())

    with cd('/tmp'):

        # GET correct permissions form origin server.
        with settings(host_string=origin):
            with cd('/tmp'):
                sudo('getfacl -pR "%s" > "%s"' % (path, remote_perms_file),
                     quiet=QUIET)
                get(remote_perms_file, '/tmp')
                sudo('rm "%s"' % remote_perms_file, quiet=QUIET)

        if env.host_string != 'localhost':
            # TODO: find a way to transfer from one server to another directly.
            put(remote_perms_file)

        # gather local permissions, compare them, and reapply
        sudo('getfacl -pR "%s" > "%s"' % (path, local_perms_file), quiet=QUIET)
        sudo('colordiff -U 3 "%s" "%s" || true' % (local_perms_file,
                                                   remote_perms_file),
             quiet=QUIET)

        sudo('setfacl --restore="%s" %s || true' % (remote_perms_file,
             '' if apply else '--test'), quiet=QUIET)

        sudo('rm "%s" "%s"' % (remote_perms_file, local_perms_file),
             quiet=QUIET)


# ------------------------------------------------- Development recipes


@with_remote_configuration
def git_clone_or_update(project, github_source, remote_configuration=None):
    """ Clones or update a repository. """

    dev_mini()

    with cd(tilde('sources')):
        if exists(project):
            with cd(project):
                print('Updating GIT repository %s…' % yellow(project))
                run('git up || git pull', quiet=QUIET)
        else:
            print('Creating GIT repository %s…' % yellow(project))
            run('git clone %s %s' % (github_source, project), quiet=QUIET)


@task
@with_remote_configuration
def dev_graphviz(remote_configuration=None):
    """ Graphviz and required packages for PYgraphviz. """

    # graphviz-dev will fail on OSX, but graphiv will install
    # the -dev requisites via brew.
    pkg.pkg_add(('graphviz', 'pkg-config', 'graphviz-dev'))

    pkg.pip2_add(('pygraphviz', ))


@task
@with_remote_configuration
def dev_pil(virtualenv=None, remote_configuration=None):
    """ Required packages to build Python PIL. """

    if remote_configuration.is_osx:
        pilpkgs = ('jpeg', 'libpng', 'libxml2',
                   'freetype', 'libxslt', 'lzlib',
                   'imagemagick')
    else:
        pilpkgs = ('libjpeg-dev', 'libjpeg62', 'libpng12-dev', 'libxml2-dev',
                   'libfreetype6-dev', 'libxslt1-dev', 'zlib1g-dev',
                   'imagemagick')

    pkg.pkg_add(pilpkgs)

    if not remote_configuration.is_osx:
        # Be protective by default, this should be done
        # only in LXC / Virtual machines guests, in order
        # not to pollute the base host system.
        if confirm('Create symlinks in /usr/lib?', default=False):

            with cd('/usr/lib'):
                # TODO: check it works (eg. it suffices
                # to correctly build PIL via PIP).
                for libname in ('libjpeg', 'libfreetype', 'libz'):
                    symlink('/usr/lib/%s-linux-gnu/%s.so'
                            % (remote_configuration.arch, libname),
                            '%s.so' % libname)

            # TODO:     with prefix('workon myvenv'):
            # This must be done in the virtualenv, not system-wide.
            #sudo('pip install -U PIL', quiet=QUIET)

# TODO: rabbitmq-server


@task
@with_remote_configuration
def dev_tildesources(remote_configuration=None):
    """ Create ~/sources if not existing. """

    with cd(tilde()):
        if not exists('sources'):
            if remote_configuration.is_vm:
                if remote_configuration.is_parallel:
                    symlink('/media/psf/Home/sources', 'sources')
            else:
                run('mkdir sources', quiet=QUIET)


@task
@with_remote_configuration
def dev_sqlite(remote_configuration=None):
    """ SQLite development environment (for python packages build). """

    if remote_configuration.is_deb:
        pkg.pkg_add(('libsqlite3-dev', 'python-all-dev', ))

    pkg.pip2_add(('pysqlite', ))


@task
@with_remote_configuration
def dev_mysql(remote_configuration=None):
    """ MySQL development environment (for python packages build). """


    pkg.pkg_add('libmysqlclient-dev' if remote_configuration.is_deb else '')

@task
@with_remote_configuration
def dev_postgresql(remote_configuration=None):
    """ PostgreSQL development environment (for python packages build). """

    LOGGER.info('Checking dev_postgresql() components…')

    if remote_configuration.is_osx:
        pass

    elif remote_configuration.is_ubuntu:
        major_distro_version = \
            int(remote_configuration.lsb.RELEASE.split('.')[0])

        if major_distro_version >= 14:
            pkg.pkg_add(('postgresql-client-9.3', 'postgresql-server-dev-9.3',
                         'postgresql-server-dev-all'))
        else:
            pkg.pkg_add(('postgresql-client-9.1', 'postgresql-server-dev-9.1',
                         'postgresql-server-dev-all'))

    elif remote_configuration.is_arch:
        pkg.pkg_add(('postgresql-libs', ))

    elif remote_configuration.is_freebsd:
        pkg.pkg_add(('postgresql9-client', ))

    # This should be done in the virtualenv.
    #pkg.pip2_add(('psycopg2', ))


@task
@with_remote_configuration
def dev_mongodb(remote_configuration=None):
    """ MongoDB development environment (for python packages build). """

    LOGGER.info('Checking dev_mongodb() components…')

    if remote_configuration.is_deb:
        sys_mongodb()
        #pkg.pkg_add(('mongodb-10gen-dev', ))

    pass


@task
@runs_once
@with_remote_configuration
def dev_mini(remote_configuration=None):
    """ Git and ~/sources/

        .. todo:: use the ``@runs_once`` decorator
            when it works with parallel execution.
    """

    LOGGER.info('Checking dev_mini() components…')

    # Avoid a crash during install because xmlcatmgr is missing.
    if remote_configuration.is_freebsd:
        pkg.pkg_add(('xmlcatmgr', ))

    pkg.pkg_add(('git-core' if remote_configuration.is_deb else 'git'))

    dev_tildesources()

    if remote_configuration.is_osx:
        return

    pkg.pkg_add(('gmake' if remote_configuration.is_bsd else 'make', ))


@task
@with_remote_configuration
def dev_django_full(remote_configuration=None):
    """ Django full stack system packages (for python packages build). """

    LOGGER.info('Checking dev_django_full() components…')

    dev_postgresql()
    dev_memcached()
    dev_python_deps()


@task
@with_remote_configuration
def dev_memcached(remote_configuration=None):
    """ Memcache development environment (for python packages build). """

    LOGGER.info('Checking dev_memcached() components…')

    pkg.pkg_add(('libmemcached-dev' if remote_configuration.is_deb
                else 'libmemcached' if remote_configuration.is_arch
                else 'databases/libmemcached', ))


@task
@with_remote_configuration
def dev_python_deps(remote_configuration=None):
    """ Other non-Python development packages (for python packages build). """

    LOGGER.info('Checking dev_python_deps() components…')

    if remote_configuration.is_osx:
        pkg.pkg_add(('zmq', ))

    elif remote_configuration.is_freebsd:
        pkg.pkg_add(('libzmq4', ))

    elif remote_configuration.is_deb:
        pkg.pkg_add(('libxml2-dev', 'libxslt-dev',
                    'libzmq-dev', 'python-dev', ))

    elif remote_configuration.is_arch:
        pkg.pkg_add(('zeromq', ))

    # PIP version is probably more recent.
    pkg.pip2_add(('cython', ))


@task
@with_remote_configuration
def dev_web_nodejs(remote_configuration=None):
    """ Web development packages (NodeJS, Less, Compass…). """

    dev_mini()

    # This is needed when run from the Django tasks, else some
    # packages could fail to install because of outdate indexes.
    pkg.pkg_update()

    LOGGER.info('Checking NodeJS & NPM components…')

    # ———————————————————————————————————————————————————————————— NodeJS & NPM

    if remote_configuration.is_ubuntu:
        major_distro_version = \
            int(remote_configuration.lsb.RELEASE.split('.')[0])

        if major_distro_version >= 12 and major_distro_version <= 13:
            if not exists('/etc/apt/sources.list.d/'
                          'chris-lea-node_js-{0}.list'.format(
                              remote_configuration.lsb.CODENAME)):
                # Because of http://stackoverflow.com/q/7214474/654755
                pkg.apt.ppa('ppa:chris-lea/node.js')

                # We need to remove it first, because pkg_add won't
                # upgrade it, unlike `apt-get install nodejs` does.
                pkg.pkg_del(('nodejs', ))

        else:
            pkg.pkg_add(('npm', ))

            if major_distro_version == 14:
                # On Ubuntu 14.04, `django-pipeline` miss the `/usr/bin/node`
                # executable; we only have `nodejs` left in recent versions.
                pkg.pkg_add(('nodejs-legacy', ))

    if remote_configuration.is_deb:
        # NOTE: `nodejs` PPA version already includes `npm`,
        # no need to install it via a separate package on Ubuntu.
        # If not using the PPA, `npm` has already been installed.
        pkg.pkg_add(('nodejs',
                    # PySide build-deps, for Ghost.py text parsing.
                    'cmake', ))

    elif remote_configuration.is_arch:
        pkg.pkg_add(('nodejs', 'cmake', ))

    elif remote_configuration.is_freebsd:
        pkg.pkg_add(('node', 'npm', 'cmake', ))

    # But on OSX/BSD, we need NPM too. For Ubuntu, this has already been handled.
    elif remote_configuration.is_osx:
        pkg.pkg_add(('nodejs', 'npm', ))

    # ——————————————————————————————————————————————————————————— Node packages

    pkg.npm_add(('coffee-script',       # used in Django-pipeline
                 'yuglify',             # used in Django-pipeline
                 'less',                # used in Django-pipeline

                 # Not used yet
                 #'bower', 'grunt-cli',

                 # Not yet ready (package throws exceptions on install)
                 #'yo',
                 #'yeoman-bootstrap',

                 # duplicates of coffee-script ?
                 #'coffeescript-compiler',
                 #'coffeescript-concat',
                 #'coffeescript_compiler_tools',
                 ))


@task
@with_remote_configuration
def dev_web_pyside(remote_configuration=None):

    # ——————————————————————————————————————————————— PySide build-deps (again)
    # for Ghost.py text parsing.

    LOGGER.info('Checking QT4 & webkit components…')

    if remote_configuration.is_osx and not exists('/opt'):

        # Even this doesn't work, we need to official binary,
        # else PySide won't find it…
        #run('brew install qt --developer', quiet=QUIET)

        LOGGER.critical('You need to install PySide and Qt from '
                        'http://qt-project.org/wiki/PySide_Binaries_MacOSX '
                        '(eg. http://pyside.markus-ullmann.de/pyside-1.1.1-qt48-py27apple.pkg)') # NOQA

    elif remote_configuration.is_deb:
        pkg.pkg_add(('libqt4-dev', ))

    elif remote_configuration.is_arch:
        pkg.pkg_add(('qt4', 'qtwebkit', ))

    elif remote_configuration.is_freebsd:
        pkg.pkg_add(('qt4', 'qt4-webkit', ))


@task
@with_remote_configuration
def dev_web_ruby(remote_configuration=None):

    dev_mini()

    # This is needed when run from the Django tasks, else some
    # packages could fail to install because of outdate indexes.
    pkg.pkg_update()

    LOGGER.info('Checking dev_web_ruby() components…')

    if remote_configuration.is_arch:
        pkg.pkg_add(('ruby', ))

    elif remote_configuration.is_deb:
        pkg.pkg_add(('ruby', 'ruby-dev', ))

        major_distro_version = \
            int(remote_configuration.lsb.RELEASE.split('.')[0])

        if major_distro_version < 14:
            pkg.pkg_add(('rubygems', ))

    elif remote_configuration.is_freebsd:
        # Ruby 2.1 is the recommended version for new
        # projects. Other version are just legacy.
        pkg.pkg_add(('ruby21', 'ruby19-gems', 'rubygem-rake', ))
        # install ruby-gdbm too ?

    pkg.gem_add(('bundler', ))


@task
@with_remote_configuration
def dev(remote_configuration=None):
    """ Generic Python development (dev_mini + git-flow & other tools
        + Python2/3 & PIP/virtualenv utils). """

    dev_mini()

    LOGGER.info('Checking dev():base components…')

    if remote_configuration.is_osx:
        # On OSX:
        #    - ruby & gem are already installed.
        #     - via Brew, python will install PIP.
        #     - virtualenv* come only via PIP.
        #    - git-flow-avh brings small typing enhancements.

        pkg.pkg_add(('git-flow-avh', 'ack', 'python', ))

    elif remote_configuration.is_freebsd:
        # NOTE: git-flow doesn't seem to have a port
        # on FreeBSD (searched on 9.2, 20140821).
        pkg.pkg_add(('ack', 'python', ))

    elif remote_configuration.is_deb:
        # On Ubuntu, `ack` is `ack-grep`.
        pkg.pkg_add(('git-flow', 'ack-grep', 'python-pip', ))

        # Remove eventually DEB installed old packages (see just after).
        pkg.pkg_del(('python-virtualenv', 'virtualenvwrapper', ))

    elif remote_configuration.is_arch:
        # gitflow-git is in AUR (via yaourt),
        # thus not yet automatically installed.
        # Arch has no Python 2.x by default.
        pkg.pkg_add(('ack', 'python2', 'python2-pip', ))

    # ——————————————————————————————————————————————————————— Python virtualenv

    #LOGGER.info('Checking dev():python components…')

    #TODO: if exists virtualenv and is_lxc(machine):

    # We remove the system packages to avoid duplicates and import
    # misses/conflicts in virtualenvs. Anyway, the system packages
    # are usually older than the PIP ones.
    #LOGGER.info('Removing system python packages…')
    #pkg.pkg_del(('ipython', 'ipython2', 'ipython3', 'devel/ipython' ))

    # —————————————————————————————————————————————————————————————— Python 3.x

    LOGGER.info('Checking Python 3.x components…')

    if remote_configuration.is_osx:
        # The brew python3 receipe installs pip3 and development files.
        py3_pkgs = ('python3', )

    elif remote_configuration.is_deb:
        # TODO: 'python3-pip',
        # NOTE: zlib1g-dev is required to build git-up.
        py3_pkgs = ('python3', 'python3-dev', 'python3-examples',
                    'python3-minimal', 'zlib1g-dev', )

        if int(remote_configuration.lsb.RELEASE.split('.', 1)[0]) > 13:
            py3_pkgs += ('python3.4', 'python3.4-dev', 'python3.4-examples',
                         'python3.4-minimal', )

        elif int(remote_configuration.lsb.RELEASE.split('.', 1)[0]) > 12:
            py3_pkgs += ('python3.3', 'python3.3-dev', 'python3.3-examples',
                         'python3.3-minimal', )


    elif remote_configuration.is_arch:
        # Arch has already Python 3 as the default.
        py3_pkgs = ()

    elif remote_configuration.is_freebsd:
        py3_pkgs = ('python3', )

    # ——————————————————————————————————————————————————————— Build environment

    LOGGER.info('Checking build environment…')

    # Gettext is used nearly everywhere, and Django
    # {make,compile}messages commands need it.
    pkg.pkg_add(('gettext', ))

    if remote_configuration.is_arch:
        pkg.pkg_add(('gcc', 'make', 'autogen', 'autoconf'))

    elif remote_configuration.is_freebsd:
        pkg.pkg_add(('gcc48', 'gmake', 'autogen', 'autoconf'))

    elif remote_configuration.is_deb:
        pkg.pkg_add(('build-essential', 'python-all-dev', ))

    pkg.pkg_add(py3_pkgs)
    pkg.pip2_add(('git-up', 'virtualenvwrapper', ))
    pkg.pip3_add(('virtualenvwrapper', ))


# --------------------------------------------------- Databases recipes


@task
@with_remote_configuration
def db_sqlite(remote_configuration=None):
    """ SQLite database library. """

    LOGGER.info('Installing SQLite…')

    pkg.pkg_add('sqlite' if remote_configuration.is_osx else 'sqlite3')


@task
@with_remote_configuration
def db_redis(remote_configuration=None):
    """ Redis server. """

    LOGGER.info('Installing Redis…')

    if remote_configuration.is_osx:
        pkg.pkg_add(('redis', ))

        run('ln -sfv /usr/local/opt/redis/*.plist ~/Library/LaunchAgents',
            quiet=QUIET)
        run('launchctl load ~/Library/LaunchAgents/homebrew.*.redis.plist',
            quiet=QUIET)

    elif remote_configuration.is_bsd:
        pkg.pkg_add(('redis', ))

        LOGGER.warning('Please ensure Redis is enabled and running.')

    elif remote_configuration.is_arch:
        pkg.pkg_add(('redis', ))

        # This won't hurt beiing done more than once (tested 20140821).
        sudo('systemctl enable redis', quiet=QUIET)
        sudo('systemctl start redis', quiet=QUIET)

    elif remote_configuration.is_deb:

        if remote_configuration.is_ubuntu:
            if remote_configuration.lsb.RELEASE.startswith('12') \
                    or remote_configuration.lsb.RELEASE.startswith('13'):
                if not exists('/etc/apt/sources.list.d/'
                              'chris-lea-redis-server-{0}.list'.format(
                                  remote_configuration.lsb.CODENAME)):
                    pkg.apt.ppa('ppa:chris-lea/redis-server')

                    if exists('/usr/bin/redis-cli'):
                        pkg.apt_upgrade()

                    else:
                        pkg.pkg_add('redis-server')

            else:
                pkg.pkg_add('redis-server')

        else:
            pkg.pkg_add('redis-server')


@task
@with_remote_configuration
def db_mysql(remote_configuration=None):
    """ MySQL database server. """

    LOGGER.info('Installing MySQL…')

    pkg.pkg_add('mysql' if remote_configuration.is_osx else 'mysql-server')


@task(aliases=('db_memcache', ))
@with_remote_configuration
def db_memcached(remote_configuration=None):
    """ Memcache key-value volatile store. """

    LOGGER.info('Installing Memcached…')

    pkg.pkg_add('memcached')

    if remote_configuration.is_arch:

        # This won't hurt beiing done more than once (tested 20140821).
        sudo('systemctl enable memcached', quiet=QUIET)
        sudo('systemctl start memcached', quiet=QUIET)

    elif remote_configuration.is_osx:
        run('ln -sfv /usr/local/opt/memcached/*.plist ~/Library/LaunchAgents',
            quiet=QUIET)
        run('launchctl load ~/Library/LaunchAgents/homebrew.*.memcached.plist',
            quiet=QUIET)

    elif remote_configuration.is_freebsd:
        LOGGER.warning('Please ensure Memcached is enabled and running.')

@task(aliases=('db_postgres', ))
@with_remote_configuration
def db_postgresql(remote_configuration=None):
    """ PostgreSQL database server. """

    LOGGER.info('Installing PostgreSQL…')

    if remote_configuration.is_osx:
        if pkg.pkg_add(('postgresql', )):
            run('initdb /usr/local/var/postgres -E utf8', quiet=QUIET)
            run('ln -sfv /usr/local/opt/postgresql/*.plist '
                '~/Library/LaunchAgents', quiet=QUIET)
            run('launchctl load ~/Library/LaunchAgents/'
                'homebrew.*.postgresql.plist', quiet=QUIET)

            # Test connection
            # psql template1

    elif remote_configuration.is_bsd:
        pkg.pkg_add(('postgresql9-server', ))

        LOGGER.warning('Please ensure PostgreSQL is enabled and running.')

        if not exists('/usr/local/pgsql/data'):
            run('su - pgsql -c "initdb --locale en_US.UTF-8 '
                '-E UTF8 -D /usr/local/pgsql/data"', quiet=QUIET)
            append('/usr/local/pgsql/data/postmaster.opts',
                   '/usr/local/bin/postgres -D /usr/local/pgsql/data',
                   use_sudo=True)
            sudo('chown pgsql:pgsql /usr/local/pgsql/data/postmaster.optparse',
                 quiet=QUIET)
            append('/etc/rc.conf', 'postgresql_enable="YES"', use_sudo=True)
            sudo('/usr/local/etc/rc.d/postgresql start', quiet=QUIET)

    elif remote_configuration.is_arch:
        pkg.pkg_add(('postgresql', ))

        # We use_sudo because PG files are ultra protected on ArchLinux.
        if not exists('/var/lib/postgres/data/pg_hba.conf', use_sudo=True):
            # TODO: /var/lib/postgres/data/postgresql.conf
            # stats_temp_directory = '/run/postgresql'
            #
            run('su - postgres -c "initdb --locale en_US.UTF-8 '
                '-E UTF8 -D /var/lib/postgres/data"', quiet=QUIET)

        # This won't hurt beiing done more than once (tested 20140821).
        sudo('systemctl enable postgresql', quiet=QUIET)
        sudo('systemctl start postgresql', quiet=QUIET)

    elif remote_configuration.is_deb:

        major_distro_version = \
            int(remote_configuration.lsb.RELEASE.split('.')[0])

        if major_distro_version >= 14:
            pkg.pkg_add(('postgresql-9.3', ))

        else:
            pkg.pkg_add(('postgresql-9.1', ))

    LOGGER.warning('You still have to tweak pg_hba.conf yourself.')


@task(aliases=('db_mongo', ))
@with_remote_configuration
def db_mongodb(remote_configuration=None):
    """ MongoDB database server. """

    if remote_configuration.is_osx:
        if pkg.pkg_add(('mongodb', )):
            run('ln -sfv /usr/local/opt/mongodb/*.plist ~/Library/LaunchAgents',
                quiet=QUIET)
            run('launchctl load '
                '~/Library/LaunchAgents/homebrew.*.mongodb.plist', quiet=QUIET)

    elif remote_configuration.is_arch:
        pkg.pkg_add(('mongodb', ))

        # This won't hurt beiing done more than once (tested 20140821).
        sudo('systemctl enable mongodb', quiet=QUIET)
        sudo('systemctl start mongodb', quiet=QUIET)

    elif remote_configuration.is_freebsd:
        pkg.pkg_add(('mongodb', ))

        LOGGER.warning('PLEASE ENSURE MongoDB is configured/running…')

    elif remote_configuration.is_deb:
        package_name = sys_mongodb()
        pkg.pkg_add((package_name, ))

    LOGGER.warning('You still have to tweak mongodb.conf yourself '
                   '(eg. `bind_ip=…`).')


# -------------------------------------- Server or console applications


@task
@with_remote_configuration
def base(remote_configuration=None, upgrade=True):
    """ sys_* + brew (on OSX) + byobu, bash-completion, htop. """

    LOGGER.info('Checking base() components…')

    sys_easy_sudo()
    sys_admin_pkgs()

    install_homebrew()

    if upgrade:
        pkg.pkg_update()
        pkg.pkg_upgrade()

    sys_unattended()
    sys_del_useless()
    sys_default_services()
    sys_ssh_powerline()

    pkg.pkg_add(('byobu', 'bash-completion',
                'htop-osx' if remote_configuration.is_osx else 'htop'))


@task
@with_remote_configuration
def deployment(remote_configuration=None):
    """ Install Fabric (via PIP for latest paramiko). """

    # We remove the system packages in case they were previously
    # installed, because PIP's versions are nearly always more recent.
    # Paramiko <1.8 doesn't handle SSH agent correctly and we need it.
    pkg.pkg_del(('fabric', 'python-paramiko', ))

    if not remote_configuration.is_osx:
        pkg.pkg_add(('python-all-dev', ))

    pkg.pip2_add(('fabric', ))


@task
@with_remote_configuration
def docker(remote_configuration=None):
    """ Docker local runner (containers manager). """

    LOGGER.warning("This functions is not yet implemented.")

    """
    # http://docs.docker.io/en/latest/installation/ubuntulinux/#ubuntu-precise

    sudo apt-get update
    sudo apt-get install linux-image-generic-lts-raring linux-headers-generic-lts-raring
    sudo reboot

    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
    sudo sh -c "echo deb http://get.docker.io/ubuntu docker main > /etc/apt/sources.list.d/docker.list"
    sudo apt-get update
    sudo apt-get install lxc-docker

    sudo docker run -i -t ubuntu /bin/bash
        exit

    docker images




    """

    return


@task(aliases=('lxc_runner', ))
@with_remote_configuration
def lxc_host(remote_configuration=None):
    """ LXC local runner (guests manager). """

    if remote_configuration.is_osx or remote_configuration.is_bsd:
        info("Skipped LXC host setup (not on LSB).")
        return

    pkg.pkg_add(('lxc', ))

    if remote_configuration.is_deb:
        pkg.pkg_add(('cgroup-lite', 'debootstrap', ))

    if remote_configuration.is_ubuntu:
        major_distro_version = \
            int(remote_configuration.lsb.RELEASE.split('.')[0])

        if major_distro_version >= 14:
            pkg.pkg_add(('lxc-templates', ))

# ------------------------------------ Client or graphical applications

# TODO: rename and refactor these 3 tasks.


@task
@with_remote_configuration
def graphdev(remote_configuration=None):
    """ Graphical applications for the typical development environment.

        .. todo:: clean / refactor contents (OSX mainly).
    """

    #pkg.pkg_add(('pdksh', 'zsh', ))

    if remote_configuration.is_osx:
        # TODO: download/install on OSX:
        for app in ('iTerm', 'TotalFinder', 'Google Chrome', 'Airfoil', 'Adium',
                    'iStat Menus', 'LibreOffice', 'Firefox', 'Aperture',
                    'MPlayerX'):
            if not exists('/Applications/%s.app' % app):
                info("Please install %s manually." % yellow(app))
        return

    print('XXX on Arch/BSD…')

    pkg.pkg_add(('gitg', 'meld', 'regexxer', 'cscope', 'exuberant-ctags',
                'vim-gnome', 'terminator', 'gedit-developer-plugins',
                'gedit-plugins', 'geany', 'geany-plugins', ))


@task
@with_remote_configuration
def graphdb(remote_configuration=None):
    """ Graphical and client packages for databases. """

    if remote_configuration.is_osx:
        info("Skipped graphical DB-related packages (not on LSB).")
        return

    print('XXX on Arch/BSD…')

    pkg.pkg_add('pgadmin3')


@task
@with_remote_configuration
def graph(remote_configuration=None):
    """ Poweruser graphical applications. """

    if remote_configuration.is_osx:
        info("Skipped graphical APT packages (not on LSB).")
        return

    if remote_configuration.is_ubuntu:
        info("Skipped graph PPA packages (not on Ubuntu).")
        return

    pkg.pkg_add(('synaptic', 'gdebi', 'compizconfig-settings-manager',
                'dconf-tools', 'gconf-editor', 'pidgin', 'vlc', 'mplayer',
                'indicator-multiload'))

    if remote_configuration.lsb.RELEASE.startswith('13') \
            or remote_configuration.lsb.RELEASE == '12.10':
        pkg.apt.ppa_pkg('ppa:freyja-dev/unity-tweak-tool-daily',
                        'unity-tweak-tool', '/usr/bin/unity-tweak-tool')

        pkg.apt.ppa_pkg('ppa:gwendal-lebihan-dev/cinnamon-stable',
                        ('nemo', 'nemo-fileroller'), '/usr/bin/nemo')

    elif remote_configuration.lsb.RELEASE == '12.04':
        pkg.apt.ppa_pkg('ppa:myunity/ppa', 'myunity', '/usr/bin/myunity')

    if remote_configuration.lsb.RELEASE == '13.10':

        if not exists('/usr/share/icons/Faenza'):
            run(u'wget https://launchpad.net/~tiheum/+archive/equinox/+files/'
                u'faenza-icon-theme_1.3.1_all.deb -O /tmp/faenza.deb && '
                u'sudo dpkg -i /tmp/faenza.deb', quiet=QUIET)
    else:
        pkg.apt.ppa_pkg('ppa:tiheum/equinox', ('faience-icon-theme',
                        'faenza-icon-theme'), '/usr/share/icons/Faenza')

    if int(remote_configuration.lsb.RELEASE.split('.', 1)[0]) < 14:
        pkg.apt.ppa_pkg('ppa:caffeine-developers/ppa',
                        'caffeine', '/usr/bin/caffeine')

    #pkg.apt.ppa_pkg('ppa:conscioususer/polly-unstable',
    #                 'polly', '/usr/bin/polly')
    #
    # pkg.apt.ppa_pkg('ppa:kilian/f.lux', 'fluxgui', '/usr/bin/fluxgui')
    # pkg.apt.ppa_pkg('ppa:jonls/redshift-ppa',
    #                 'redshift', '/usr/bin/redshift')
    if remote_configuration.lsb.RELEASE == '13.10':
        pkg.pkg_add(('gtk-redshift', ))

    elif remote_configuration.lsb.RELEASE.startswith('14'):
        pkg.pkg_add(('redshift-gtk', ))


@task(aliases=('graphkbd', 'kbd', ))
@with_remote_configuration
def graphshortcuts(remote_configuration=None):
    """ Gconf / Dconf keyboard shortcuts for back-from-resume loose. """
    if remote_configuration.is_osx:
        return

    for key, value in (('activate-window-menu', "['<Shift><Alt>space']"),
                       ('toggle-maximized', "['<Alt>space']"), ):

        # Probably less direct than dconf
        #local('gsettings set org.gnome.desktop.wm.keybindings %s "%s"'
        #    % (key, value))

        # doesn't work with 'run()', because X connection is not here.
        local('dconf write /org/gnome/desktop/wm/keybindings/%s "%s"'
              % (key, value), capture=QUIET)


@task(aliases=('coc', ))
@with_remote_configuration
def clear_osx_cache(remote_configuration=None):
    """ Clears some OSX cache, to avoid opendirectoryd to hog CPU. """

    if not remote_configuration.is_osx:
        return

    # cf. http://support.apple.com/kb/HT3540
    # from http://apple.stackexchange.com/q/33312
    # because opendirectoryd takes 100% CPU on my MBPr.
    run('dscl . -list Computers | grep -v "^localhost$" '
        '| while read computer_name ; do sudo dscl . -delete '
        'Computers/"$computer_name" ; done', quiet=QUIET)


@task
@with_remote_configuration
def upload_osx_apps(remote_configuration=None):
    """ Upload local OSX Apps to my central location for easy redistribution
        without harvesting the internet on every new machine.

        .. note:: there is currently no “ clean outdated files ” procedure…
    """

    run('mkdir -p %s' % central_osx_apps.split(':')[1], quiet=QUIET)
    run('rsync -av %s %s' % (local_osx_apps, central_osx_apps), quiet=QUIET)

# =========================================== My personnal environments


@task
@with_remote_configuration
def myapps(remote_configuration=None):
    """ Skype + Chrome + Sublime + 1Password """

    install_skype()
    install_chrome()
    install_sublime()

    if not remote_configuration.is_vm:
        # No need to pollute the VM with wine,
        # I already have 1Password installed under OSX.
        install_spotify()
        install_1password()


@task
@with_remote_configuration
def mydevenv(remote_configuration=None):
    """ Clone my professional / personnal projects with GIT in ~/sources """

    install_powerline()

    dev()
    dev_web_nodejs()
    dev_web_ruby()
    #dev_web_pyside()

    deployment()

    # NO clone, it's already in my dropbox!
    #git_clone_or_update('sparks', 'git@github.com:Karmak23/sparks.git')
    #
    # Just symlink it to my sources for centralization/normalization
    # purposes. Or is it just bad-habits? ;-)
    with cd(tilde('sources')):
        symlink('../Dropbox/sparks', 'sparks')

    git_clone_or_update('pelican-themes',
                        'git@github.com:Karmak23/pelican-themes.git')

    # Not yet ready
    #git_clone_or_update('1flow', 'dev.1flow.net:/home/groups/oneflow.git')

    LOGGER.warning(u'Licorn® repositories disabled.')
    #git_clone_or_update('licorn', 'dev.licorn.org:/home/groups/licorn.git')
    #git_clone_or_update('mylicorn', 'my.licorn.org:/home/groups/mylicorn.git')


@task
@with_remote_configuration
def mydotfiles(overwrite=False, locally=False, remote_configuration=None):
    """ Symlink a bunch of things to Dropbox/… """

    with cd(tilde()):

        symlink('Dropbox/bin', 'bin', overwrite=overwrite, locally=locally)
        symlink('Dropbox/configuration/virtualenvs', '.virtualenvs',
                overwrite=overwrite, locally=locally)

        for filename in ('dsh', 'ssh', 'ackrc', 'bashrc', 'fabricrc',
                         'gitconfig', 'gitignore', 'dupload.conf',
                         'multitailrc'):
            symlink(dotfiles('dot.%s' % filename),
                    os.path.join(tilde(), '.%s' % filename),
                    overwrite=overwrite, locally=locally)

        if not remote_configuration.is_osx:
            if not exists('.config'):
                local('mkdir .config', capture=QUIET) \
                    if locally else run('mkdir .config', quiet=QUIET)

            with cd('.config'):
                # These don't handle the Dropboxed configuration / data
                # correctly. We won't symlink their data automatically.
                symlink_blacklist = ('caffeine', )

                base_path   = tilde(dotfiles('dot.config'))
                ln_src_path = os.path.join('..', base_path)

                # NOTE: this lists files on the local
                # host, not the remote target.
                for entry in os.listdir(base_path):
                    if entry.startswith('.'):
                        continue

                    if entry in symlink_blacklist:
                        if not exists(entry):
                            print("Please copy %s to ~/.config/ yourself."
                                  % os.path.join(ln_src_path, entry))
                        continue

                    # But this will do the symlink remotely.
                    symlink(os.path.join(ln_src_path, entry), entry,
                            overwrite=overwrite, locally=locally)


@task(aliases=('myenv', ))
@with_remote_configuration
def myfullenv(remote_configuration=None):
    """ sudo + full + fullgraph + mydev + mypkg + mydot """

    base()

    graphdev()
    graphdb()
    graph()

    mydotfiles()
    myapps()
    mydevenv()

    # ask questions last, when everything else has been installed / setup.
    if not remote_configuration.is_osx and confirm(
        'Reinstall bcmwl-kernel-source (MacbookAir(3,2) late 2010)?',
            default=False):
        # Reinstall / rebuild the BCM wlan driver.
        # NM should detect and re-connect automatically at the end.
        sudo('apt-get install --reinstall bcmwl-kernel-source', quiet=QUIET)


@task(aliases=('mysetup', ))
@with_remote_configuration
def mybootstrap(remote_configuration=None):
    """ Bootstrap my personal environment on the local machine. """

    pkg.pkg_add(('ssh', ), locally=True)

    mydotfiles(remote_configuration=None, locally=True)

# ============================================= LXC guests environments


@task
@with_remote_configuration
def lxc_base(remote_configuration=None):
    """ Base packages for an LXC container (LANG, mailx, nullmailer). """

    if remote_configuration.is_osx:
        info('Skipped lxc_base (not on LSB).')
        return

    sys_easy_sudo()

    print('XXX on Arch/BSD…')

    # install the locale before everything, else DPKG borks.
    pkg.pkg_add(('language-pack-fr', 'language-pack-en', ))

    # Remove firefox's locale, it's completely useless in a LXC.
    pkg.pkg_del(('firefox-locale-fr', 'firefox-locale-en', ))

    pkg.pkg_add(('bsd-mailx', ))

    # When using lxc_server on a lxc_host which already has postfix
    # installed, don't replace it by nullmailer, this is harmful.
    if not pkg.pkg_is_installed('postfix'):
        pkg.pkg_add(('nullmailer', ))


@task
@with_remote_configuration
def lxc_base_and_dev(remote_configuration=None):
    """ lxc_base + base + dev (for LXC guests containers) """

    if remote_configuration.is_osx:
        info('Skipped lxc_base (not on LSB).')
        return

    base()
    lxc_base()
    dev()


@task
@with_remote_configuration
def lxc_purge(remote_configuration=None):
    """ Remove useless packages on LXC guest. """

    if remote_configuration.is_osx:
        info('Skipped lxc_purge (not on LSB).')
        return

    if remote_configuration.is_ubuntu:
        # Some other useless packages on LXCs…
        # NOTE: don't purge dbus, it's used by the upstart bash completer. Too bad.
        pkg.pkg_del(('man-db', 'ureadahead', ))  # 'dbus', ))

        sudo('apt-get autoremove --purge --yes --force-yes', quiet=QUIET)

    print('XXX on Arch/BSD…')


@task
@with_remote_configuration
def lxc_server(remote_configuration=None):
    """ LXC base + server packages (Pg/Mongo/Redis/Memcache). """

    # If someone finds a better way to detect if we are on a physical
    # host or not, I will be happy to use it. For now I just assume
    # nobody installs a bootloader inside a container. I found trying
    # to detect the cgroup, /proc, etc always misleading at some point
    # because of bind mounts, LXC inside LXCs, and the like.
    if exists('/boot/grub'):
        lxc_base()
        lxc_host()

    #db_redis()
    #db_mongodb()
    #db_memcached()
    #db_postgresql()

    if not exists('/etc/nginx'):
        LOGGER.warning('Install NGINX now :-)')
