# coding=utf-8

"""
Copyright 2015 Load Impact

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import absolute_import

__all__ = ['DateTimeField', 'DictField', 'FloatField', 'IntegerField',
           'ListField', 'ObjectField', 'StringField', 'UnicodeField']

import sys

from datetime import datetime
from .exceptions import CoercionError
from .utils import UTC


class Field(object):
    """All field classes derive from this base class."""

    # Option enumeration.
    SERIALIZE = 1

    def __init__(self, value=None, options=None):
        if value is None:
            self._value = self.__class__.default()
        else:
            self._value = self.__class__.coerce(value)
        self.options = []
        if options:
            if isinstance(options, int):
                self.options = [options]
            else:
                self.options = list(options)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        try:
            self._value = self.__class__.coerce(value)
        except CoercionError as e:
            raise ValueError(e)

    def __repr__(self):
        return repr(self._value)

    def has_option(self, option):
        return option in self.options

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
        if not isinstance(value, cls.field_type):
            try:
                return datetime.strptime(value[:-6], cls.format).replace(
                    tzinfo=UTC())
            except ValueError as e:
                raise CoercionError(e)
        return value

    @classmethod
    def default(cls):
        return datetime.utcnow().replace(tzinfo=UTC())


class DictField(Field):
    field_type = dict

    @classmethod
    def coerce(cls, value):
        if not isinstance(value, cls.field_type):
            raise CoercionError("'%s' is not a dict" % repr(value))
        return value


class FloatField(Field):
    field_type = float

    @classmethod
    def coerce(cls, value):
        try:
            return float(value)
        except ValueError as e:
            raise CoercionError(e)


class IntegerField(Field):
    field_type = int

    @classmethod
    def coerce(cls, value):
        try:
            return int(value)
        except ValueError as e:
            raise CoercionError(e)


class ListField(Field):
    field_type = list

    @classmethod
    def coerce(cls, value):
        if not isinstance(value, cls.field_type):
            raise CoercionError("'%s' is not a list" % repr(value))
        return value


class StringField(Field):
    field_type = str

    @classmethod
    def coerce(cls, value):
        try:
            return str(value)
        except ValueError as e:
            raise CoercionError(e)


class UnicodeField(Field):
    field_type = str if sys.version_info >= (3, 0) else unicode

    @classmethod
    def coerce(cls, value):
        try:
            if sys.version_info >= (3, 0):
                return str(value)
            else:
                if isinstance(value, str):
                    return unicode(value, 'utf-8')
                else:
                    return unicode(value)
        except (ValueError, UnicodeDecodeError) as e:
            raise CoercionError(e)


class ObjectField(Field):
    field_type = object

    @classmethod
    def coerce(cls, value):
        try:
            return cls.field_type(value)
        except ValueError as e:
            raise CoercionError(e)


class DataStoreListField(Field):
    field_type = list

    @classmethod
    def coerce(cls, value):
        if not isinstance(value, cls.field_type):
            raise CoercionError("'%s' is not a list" % repr(value))
        r = []
        for ds in value:
            if isinstance(ds, dict) and 'id' in ds:
                r.append(ds['id'])
            elif isinstance(ds, int):
                r.append(ds)
        return r
