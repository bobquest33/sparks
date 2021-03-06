# -*- coding: utf-8 -*-
""" A global and environment/host-dependant settings system for Django. """

import os
import logging

from os.path import dirname, abspath, join, exists
from ..fabric import local_configuration as platform

LOGGER = logging.getLogger(__name__)


if 'execfile' not in __builtins__:
    from sparks.utils import execfile


def find_settings(settings__file__name):
    """ Returns the first existing settings file, out of:

        - the one specified in the environment
          variable :env:`SPARKS_DJANGO_SETTINGS`,
        - one constructed from either the full hostname,
          then the host shortname (without TLD), then only
          the domain name. If the current hostname is short
          from the start (eg. :file:`/etc/hostname` contains
          a short name only), obviously only one will be tried.
        - a :file:`default` configuration eg.
          a :file:`settings/default.py` file.

        If none of these files are to be found, a :class:`RuntimeError`
        will be raised.

        These files will be looked up in the same directy as the caller.
        To acheive this, use them like this:

            project/
                settings/
                    __init__.py
                    myhostname_domain_ext.py
                    otherhost_domain_ext.py
                    special-config.py

        In the file :file:`__init__.py`: just write:

            # for Python 3.x, add this line:
            from sparks.utils import execfile

            from sparks.django.settings import find_settings
            execfile(find_settings(__file__))


        The :file:`myhostname_domain_ext.py` and others are completely
        standard settings file. You are free to use them as you like, eg.
        plain Django settings files, or combined in any way that pleases
        you. You could for example create a :file:`common.py`, import it
        in all other, and override only a part of its attributes in them.

        .. note:: hostname related operations are done lower-case, and dots
            are replaced with underscores. If your hostname is
            ``Chani.Licorn.local``, `sparks` will search
            ``chani_licorn_local``, ``chani`` and ``licorn_local``.

        .. note:: if you hostname starts with a digit, there is no problem
            regarding the current function: the setting filename can start
            with a digit, because it will not be imported
            but :func:`execfile`ed and in this particular case, Python
            will not complain, like it would have done for a module name.

    """

    here = dirname(abspath(settings__file__name))

    def settings_path(settings_name):

        return join(here, settings_name + '.py')

    candidates = []

    environ_settings = os.environ.get('SPARKS_DJANGO_SETTINGS', None)

    if environ_settings:
        candidates.append(settings_path(environ_settings))
        LOGGER.info(u'Picked up environment variable '
                    u'SPARKS_DJANGO_SETTINGS="{0}".'.format(
                    environ_settings))

    fullnodename = platform.hostname.lower().replace('.', '_')
    candidates.append(settings_path(fullnodename))

    try:
        shortname, domainname = platform.hostname.lower().split('.', 1)

    except ValueError:
        # The hostname is a short one, without the domain.
        pass

    else:
        candidates.extend(settings_path(x.replace('.', '_'))
                          for x in (shortname, domainname))

    candidates.append(settings_path('default'))

    for candidate in candidates:
        if exists(candidate):
            LOGGER.debug(u'Using first found settings file "{0}"'.format(
                         candidate))
            return candidate

    raise RuntimeError(u'No settings found! Tried {0}'.format(', '.join(
                       candidates)))


def include_snippets(snippets_list, project__file__, project_globals):
    """ Given a project root and an iterable of modules names, this function
        will use :func:`execfile` and import their content into the ``global``
        namespace. This way, included files content can be made dependant of
        previous inclusions.

        :param settings_root: a path (as string) representing the Django
            settings directory.

        :param snippets_list: an iterable of strings which will be included.

        Typical usage::

            myproject/
                settings/
                    snippets/
                        debug.py
                        common.py
                        production.py
                    __init__.py
                    myhostname.py

        Obviously, ``myhostname`` should be replaced by the hostname of your
        development machine, or the production machine, etc.

        For :file:`settings/__init__.py` contents, see :func:`find_settings`.

        Then, in :file:`myhostname.py`, write::

            from sparks.django.settings import include_snippets

            include_snippets((
                    '00_dev',
                    'common',
                    'email',
                    # whatever more…
                ),
                __file__, globals()
            )

        .. note:: the final ``__file__`` and ``globals()`` argument are fixed
            and important to merge all settings in the current settings module.

        .. versionchanged:: in 2.0, arguments were re-ordered to include the
            snippets list first, and to require only ``__file__`` from the
            caller, avoiding the need to ``import os`` there.
    """

    snippets_path = join(os.path.dirname(project__file__), 'snippets')

    for snippet in snippets_list:
        try:
            execfile(join(snippets_path, snippet + '.py'), project_globals)

        except Exception:
            # We need to print the full stack here, because Django will
            # only print unicode(exception), and this is a pain to debug
            # when settings fail to import.
            LOGGER.exception(u'Could not include snippet “%s”', snippet)

            # We still raise, to be sure to halt the settings import
            # process at the Django level.
            raise


def clone_settings(machine_name, project__file__, project_globals):
    """ Clone another settings file, to avoid re-writting
        it completely for only a small subset changes. Usage:

            from sparks.django.settings import clone_settings
            clone_settings('machine.domain.tld', __file__, globals())
            # and then you particular settings here…

        You can also specify directly the settings file name, without
        the ``.py`` extension.

        .. note:: the final ``__file__`` and ``globals()`` argument are fixed
            and important to merge all settings in the current settings module.

        .. versionadded:: in 2.0.
    """

    execfile(os.path.join(os.path.dirname(project__file__),
             '{0}.py'.format(machine_name.replace('.', '_'))),
             project_globals)
