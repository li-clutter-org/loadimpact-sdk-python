# coding=utf-8

__all__ = ['DateTimeField', 'DictField', 'FloatField', 'IntegerField',
           'ListField', 'ObjectField', 'StringField', 'UnicodeField']

from datetime import datetime
from exceptions import CoercionError
from utils import UTC


class Field(object):
    """All field classes derive from this base class."""

    def __init__(self, value=None):
        if value is None:
            self._value = self.__class__.default()
        else:
            self._value = self.__class__.coerce(value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        try:
            self._value = self.__class__.coerce(value)
        except CoercionError, e:
            raise ValueError(e)

    def __repr__(self):
        return repr(self._value)

    @classmethod
    def coerce(cls, value):
        raise NotImplementedError

    @classmethod
    def default(cls):
        return cls.field_type()


class DateTimeField(Field):
    field_type = datetime
    format = '%Y-%m-%dT%H:%M:%S'

    @classmethod
    def coerce(cls, value):
        try:
            return datetime.strptime(value[:-6], cls.format).replace(tzinfo=UTC())
        except ValueError, e:
            raise CoercionError(e)

    @classmethod
    def default(cls):
        return datetime.utcnow().replace(tzinfo=UTC())


class DictField(Field):
    field_type = dict

    @classmethod
    def coerce(cls, value):
        if not isinstance(value, cls.field_type):
            raise CoercionError(u"'%s' is not a dict" % repr(value))
        return value


class FloatField(Field):
    field_type = float

    @classmethod
    def coerce(cls, value):
        try:
            return float(value)
        except ValueError, e:
            raise CoercionError(e)


class IntegerField(Field):
    field_type = int

    @classmethod
    def coerce(cls, value):
        try:
            return int(value)
        except ValueError, e:
            raise CoercionError(e)


class ListField(Field):
    field_type = list

    @classmethod
    def coerce(cls, value):
        if not isinstance(value, cls.field_type):
            raise CoercionError(u"'%s' is not a list" % repr(value))
        return value


class StringField(Field):
    field_type = str

    @classmethod
    def coerce(cls, value):
        try:
            return str(value)
        except ValueError, e:
            raise CoercionError(e)


class UnicodeField(Field):
    field_type = unicode

    @classmethod
    def coerce(cls, value):
        try:
            if isinstance(value, str):
                return unicode(value, 'utf-8')
            else:
                return unicode(value)
        except (ValueError, UnicodeDecodeError), e:
            raise CoercionError(e)


class ObjectField(Field):
    field_type = object

    @classmethod
    def coerce(cls, value):
        try:
            return cls.field_type(value)
        except ValueError, e:
            raise CoercionError(e)
