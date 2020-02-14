from django.utils.translation import gettext, ngettext
from jinja2 import Environment

from vprad.site.jinja import globals
from .decorators import jinja_filters, jinja_globals, register_global, register_filter


def environment(**options):
    options.setdefault('extensions', [])
    options['extensions'].append('jinja2.ext.i18n')
    options['extensions'].append('jinja2.ext.debug')
    env = Environment(**options)
    env.globals.update(jinja_globals)
    env.filters.update(jinja_filters)
    # noinspection PyUnresolvedReferences
    env.install_gettext_callables(gettext=gettext,
                                  ngettext=ngettext,
                                  newstyle=True)
    return env
