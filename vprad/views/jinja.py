import datetime

import bleach
from django.db import models
from django.template.defaultfilters import safe

from vprad.site.jinja import register_filter

EMPTY_VALUE_DISPLAY = '--'
TRUE_VALUE_DISPLAY = '<i class="check icon"></i>'
FALSE_VALUE_DISPLAY = '<i class="times icon"></i>'


@register_filter(name='attribute_name')
def filter_attribute_name(obj, attname):
    """ Return a human friendly name for an object attribute.

    This normaly means the verbose_name of a field, if the attname is
    a field. If there are no better options, the attname is returned.
    """
    if '__' in attname:
        related_model, field_name = attname.split('__', 1)
        obj = getattr(obj, related_model)
    if isinstance(obj, models.Model):
        field = obj._meta.get_field(attname)
        return field.verbose_name
    return attname


@register_filter(name='format_attribute')
def filter_format_attribute(obj, attname):
    """ Format the value of an object attribute, nicely for humans.
    """
    field: models.Field = obj._meta.get_field(attname) if isinstance(obj, models.Model) else None
    if '__' in attname:
        related_model, field_name = attname.split('__', 1)
        obj = getattr(obj, related_model)

    display_func = getattr(obj, 'get_%s_display' % attname, None)
    if display_func:
        value = display_func()
    else:
        value = getattr(obj, attname)
    retval = filter_format_value(value)
    if isinstance(value, models.Model) and hasattr(obj, 'get_absolute_url'):
        retval = '<a href="%s">%s</a>' % (obj.get_absolute_url(), retval)
    elif isinstance(field, models.URLField) and value != EMPTY_VALUE_DISPLAY:
        retval = '<a href="%s">%s</a>' % (value, value)
    return safe(retval)


@register_filter(name='format_value')
def filter_format_value(value):
    """ Format a value nicely for humans.
    """
    if value is None:
        return EMPTY_VALUE_DISPLAY
    elif isinstance(value, datetime.datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(value, datetime.date):
        return value.strftime('%Y-%m-%d')
    elif isinstance(value, datetime.timedelta):
        return filter_format_timedelta(value)
    elif isinstance(value, str):
        return bleach.clean(value)
    elif isinstance(value, bool):
        return TRUE_VALUE_DISPLAY if value else FALSE_VALUE_DISPLAY
    return str(value)


@register_filter(name='timesince')
def filter_timesince(value: datetime.datetime,
                     until: datetime.datetime = None) -> str:
    """Show a human friendly string for a date to current time.

    Example:
        > from datetime import date, datetime
        > filter_timesince(date(2019, 12, 30), date(2019, 12, 31))
        '1 days'
        > filter_timesince(datetime(2019, 12, 30, 10, 0, 0), datetime(2019, 12, 31, 11, 0, 0))
        '1 days, 1 hours'

    Args:
        value: The datetime to which show the time since,
        until: The datetime to which the difference is calculated,
            defaults to `datetime.datetime.now()`.

    Returns:
        str: A string represeting the human readable timedelta.
    """
    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        value = datetime.datetime.combine(value, datetime.datetime.min.time())
    if until and isinstance(until, datetime.date) and not isinstance(until, datetime.datetime):
        until = datetime.datetime.combine(until, datetime.datetime.min.time())

    if not until:
        until = datetime.datetime.now(tz=value.tzinfo if value.tzinfo else None)
    since = until - value
    return filter_format_timedelta(since)


@register_filter(name='format_timedelta')
def filter_format_timedelta(value: datetime.timedelta):
    """Show a human friendly string for a date to current time.

    Example:
        > from datetime import timedelta
        > format_timedelta(timedelta(days=1))
        '1 days'
        > format_timedelta(timedelta(days=1, hours=1)
        '1 days, 1 hours'

    Args:
        value: The timedelta to format nicely

    Returns:
        str: A string represeting the human readable timedelta.
    """
    # https://codereview.stackexchange.com/q/37285
    days, rem = divmod(value.total_seconds(), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    if seconds < 1: seconds = 0
    locals_ = locals()
    magnitudes_str = ("{n} {magnitude}".format(n=int(locals_[magnitude]), magnitude=magnitude)
                      for magnitude in ("days", "hours", "minutes", "seconds") if locals_[magnitude])
    eta_str = ", ".join(magnitudes_str)
    return eta_str