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

__all__ = ['DataStore', 'LoadZone',
           'UserScenario', 'UserScenarioValidation']

import json

from .exceptions import CoercionError, ResponseParseError
from .fields import (
    DataStoreListField, DateTimeField, Field, IntegerField,
    UnicodeField, BooleanField)
from pprint import pformat


class Resource(object):
    """All API resources derive from this base class."""

    fields = {}

    def __init__(self, client, **kwargs):
        super(Resource, self).__setattr__('_fields', {})
        self.client = client
        self._set_fields(kwargs)

    def __getattr__(self, name):
        fields = self.__class__.fields
        if name in fields:
            return self._fields[name].value
        raise AttributeError("'%s' object has no field '%s'"
                             % (self.__class__.__name__, name))

    def __setattr__(self, name, value):
        fields = self.__class__.fields
        if name in fields:
            self._fields[name].value = value
        super(Resource, self).__setattr__(name, value)

    def __repr__(self):
        return "<%s>\n%s" % (self.__class__.__name__, pformat(self._fields))

    @classmethod
    def _path(cls, resource_id=None, action=None):
        if resource_id is not None:
            if action:
                return '%s/%s/%s' % (cls.resource_name, str(resource_id),
                                     action)
            return '%s/%s' % (cls.resource_name, str(resource_id))
        return cls.resource_name

    def _set_fields(self, data):
        fields = self.__class__.fields
        for k, f in fields.items():
            if isinstance(f, tuple):
                fun, opts = f
                self._fields[k] = fun(data.get(k, fun.default()), options=opts)
            else:
                self._fields[k] = f(data.get(k, f.default()))


class GetMixin(object):
    @classmethod
    def get(cls, client, resource_id):
        response = client.get(cls._path(resource_id))
        try:
            instance = cls(client)
            name = cls.resource_response_object_name
            r = response.json()
            r_obj = r.get(name)
            instance._set_fields(r_obj)
            return instance
        except CoercionError as e:
            raise ResponseParseError(e)

    def sync(self):
        response = self.client.get(self.__class__._path(self.id))
        try:
            name = self.resource_response_object_name
            r = response.json()
            r_obj = r.get(name)
            self._set_fields(r_obj)
        except CoercionError as e:
            raise ResponseParseError(e)


class CreateMixin(object):
    create_content_type = 'application/json'

    @classmethod
    def create(cls, client, data, file_object=None):
        headers = None if file_object else {'Content-Type':
                                            cls.create_content_type}
        if not file_object and isinstance(data, dict):
            data = json.dumps(data)
        response = client.post(cls._path(), headers=headers, data=data,
                               file_object=file_object)
        try:
            instance = cls(client)
            name = cls.resource_response_object_name
            r = response.json()
            r_obj = r.get(name)
            instance._set_fields(r_obj)
            return instance
        except CoercionError as e:
            raise ResponseParseError(e)


class DeleteMixin(object):
    def delete(self):
        self.client.delete(self.__class__._path(resource_id=self.id))

    @classmethod
    def delete_with_id(cls, client, resource_id):
        client.delete(cls._path(resource_id=resource_id))


class UpdateMixin(object):

    @classmethod
    def update(cls, client, resource_id, data=None, file_object=None):
        if data:
            if not file_object and isinstance(data, str):
                data = json.loads(data)
        response = client.put(cls._path(resource_id=resource_id),
                              headers='', data=data, file_object=file_object)
        try:
            instance = cls(client)
            name = cls.resource_response_object_name
            r = response.json()
            r_obj = r.get(name)
            instance._set_fields(r_obj)
            return instance
        except CoercionError as e:
            raise ResponseParseError(e)


class ListMixin(object):

    @classmethod
    def list(cls, client, resource_id=None, project_id=None):
        if project_id:
            cls.project_id = project_id
        path = cls._path(resource_id=resource_id)
        response = client.get(path)
        objects = []
        try:
            name = cls.resource_response_objects_name
            r = response.json()
            r_obj = r.get(name)
            for obj in r_obj:
                instance = cls(client)
                instance._set_fields(obj)
                objects.append(instance)
            return objects
        except CoercionError as e:
            raise ResponseParseError(e)


class DataStore(Resource, ListMixin, GetMixin, CreateMixin, UpdateMixin, DeleteMixin):
    resource_name = 'data-stores'
    resource_response_object_name = 'data_store'
    resource_response_objects_name = 'data_stores'
    project_id = None

    fields = {
        'id': IntegerField,
        'name': UnicodeField,
        'status': IntegerField,
        'rows': IntegerField,
        'created': DateTimeField,
        'belongs_to_user': BooleanField,
        'project_id': IntegerField,
        'public_url': UnicodeField,
        'converted': BooleanField,
    }

    # Data store conversion status codes
    STATUS_QUEUED = 0
    STATUS_CONVERTING = 1
    STATUS_FINISHED = 2
    STATUS_FAILED = 3

    def has_conversion_finished(self):
        """Check whether data store conversion has finished or not.

        Args:
            client: API client instance.

        Returns:
            True if data store conversion has completed, otherwise False.

        """

        self.sync()

        if self.status in [DataStore.STATUS_FINISHED, DataStore.STATUS_FAILED]:
            return True
        return False

    @classmethod
    def _path(cls, resource_id=None):
        if cls.project_id:
            return '{0}?project_id={1}'.format(cls.resource_name, cls.project_id)
        return super(DataStore, cls)._path(resource_id)

    @classmethod
    def status_code_to_text(cls, status_code):
        if DataStore.STATUS_QUEUED == status_code:
            return 'queued'
        elif DataStore.STATUS_CONVERTING == status_code:
            return 'converting'
        elif DataStore.STATUS_FINISHED == status_code:
            return 'finished'
        elif DataStore.STATUS_FAILED == status_code:
            return 'failed'
        return 'unknown'


class LoadZone(Resource, ListMixin):
    resource_name = 'load-zones'
    fields = {
        'id': UnicodeField,
        'name': UnicodeField,
        'city': UnicodeField,
        'country': UnicodeField,
        'vendor': UnicodeField
    }

    # Aggregate load zones
    AGGREGATE_WORLD = 'world'

    # Amazon load zones
    AMAZON_US_ASHBURN = 'amazon:us:ashburn'
    AMAZON_US_PALOALTO = 'amazon:us:palo alto'
    AMAZON_IE_DUBLIN = 'amazon:ie:dublin'
    AMAZON_SG_SINGAPORE = 'amazon:sg:singapore'
    AMAZON_JP_TOKYO = 'amazon:jp:tokyo'
    AMAZON_US_PORTLAND = 'amazon:us:portland'
    AMAZON_BR_SAOPAULO = 'amazon:br:são paulo'
    AMAZON_AU_SYDNEY = 'amazon:au:sydney'

    # Rackspace load zones
    RACKSPACE_US_CHICAGO = 'rackspace:us:chicago'
    RACKSPACE_US_DALLAS = 'rackspace:us:dallas'
    RACKSPACE_UK_LONDON = 'rackspace:uk:chicago'
    RACKSPACE_AU_SYDNEY = 'rackspace:au:sydney'

    # Mapping of load zone names to IDs.
    NAME_TO_ID_MAP = {
        AGGREGATE_WORLD: 1,
        AMAZON_US_ASHBURN: 11,
        AMAZON_US_PALOALTO: 12,
        AMAZON_IE_DUBLIN: 13,
        AMAZON_SG_SINGAPORE: 14,
        AMAZON_JP_TOKYO: 15,
        AMAZON_US_PORTLAND: 22,
        AMAZON_BR_SAOPAULO: 23,
        AMAZON_AU_SYDNEY: 25,
        RACKSPACE_US_CHICAGO: 26,
        RACKSPACE_US_DALLAS: 27,
        RACKSPACE_UK_LONDON: 28,
        RACKSPACE_AU_SYDNEY: 29
    }

    @classmethod
    def name_to_id(cls, name):
        try:
            return cls.NAME_TO_ID_MAP[name]
        except KeyError:
            raise ValueError("There's no load zone with name '%s'" % name)


class UserScenario(Resource, ListMixin, GetMixin, CreateMixin, DeleteMixin,
                   UpdateMixin):
    resource_name = 'user-scenarios'
    resource_response_object_name = 'user_scenario'
    resource_response_objects_name = 'user_scenarios'
    project_id = None
    fields = {
        'name': (UnicodeField, Field.SERIALIZE),
        'script': (UnicodeField, Field.SERIALIZE),
        'data_store_ids': (DataStoreListField, Field.SERIALIZE),
        'created': DateTimeField,
        'updated': DateTimeField,
        'last_validation_id': IntegerField,
        'last_validated': DateTimeField,
        'lines': IntegerField,
        'data_store_counter': IntegerField,
        'last_validation_error': (UnicodeField, Field.SERIALIZE),
        'belongs_to_user': BooleanField,
        'project_id': IntegerField,
        'id': IntegerField
    }

    @classmethod
    def _path(cls, resource_id=None):
        if cls.project_id:
            return '{0}?project_id={1}'.format(cls.resource_name, cls.project_id)
        return super(UserScenario, cls)._path(resource_id)

    def validate(self):
        return self.client.create_user_scenario_validation(
            {'user_scenario_id': self.id})

    def update_scenario(self, data):
        fields = self.fields
        for k, f in fields.items():
            if not data.get(k):
                data[k] = getattr(self, k)
        return super(UserScenario, self).update(self.client, self.id, data)


class UserScenarioValidationResult(Resource, ListMixin):
    resource_name = 'validations'
    resource_response_object_name = 'user_scenario_validation_results'
    resource_response_objects_name = 'user_scenario_validation_results'

    fields = {
        'user_scenario_validation_id': IntegerField,
        'type': IntegerField,
        'offset': IntegerField,
        'level': (UnicodeField, Field.SERIALIZE),
        'message': (UnicodeField, Field.SERIALIZE),
        'timestamp': DateTimeField
    }

    @classmethod
    def _path(cls, resource_id):
        return '{0}/{1}/results'.format(cls.resource_name, resource_id)


class UserScenarioValidation(Resource, GetMixin, CreateMixin):
    resource_name = 'validations'
    resource_response_object_name = 'user_scenario_validation'
    fields = {
        'id': IntegerField,
        'user_scenario_id': IntegerField,
        'status': IntegerField,
        'status_text': UnicodeField,
        'queued': DateTimeField,
        'started': DateTimeField,
        'ended': DateTimeField
    }

    # Validation status codes
    STATUS_QUEUED = 0
    STATUS_INITIALIZING = 1
    STATUS_RUNNING = 2
    STATUS_FINISHED = 3
    STATUS_FAILED = 4

    def is_done(self):
        """Check whether validation is done or not.

        Returns:
            True if validation has completed, otherwise False.
        """
        if self.status in [UserScenarioValidation.STATUS_FINISHED,
                           UserScenarioValidation.STATUS_FAILED]:
            return True
        return False

    @classmethod
    def status_code_to_text(cls, status_code):
        if UserScenarioValidation.STATUS_QUEUED == status_code:
            return 'queued'
        elif UserScenarioValidation.STATUS_INITIALIZING == status_code:
            return 'initializing'
        elif UserScenarioValidation.STATUS_RUNNING == status_code:
            return 'running'
        elif UserScenarioValidation.STATUS_FINISHED == status_code:
            return 'finished'
        elif UserScenarioValidation.STATUS_FAILED == status_code:
            return 'failed'
        return 'unknown'


class Organization(Resource, ListMixin):
    resource_name = 'organizations'
    resource_response_object_name = 'organization'
    resource_response_objects_name = 'organizations'
    fields = {
        'name': (UnicodeField, Field.SERIALIZE),
        'id': IntegerField
    }


class OrganizationProject(Resource, ListMixin):
    resource_name = 'organizations'
    resource_response_object_name = 'project'
    resource_response_objects_name = 'projects'
    fields = {
        'name': (UnicodeField, Field.SERIALIZE),
        'id': IntegerField
    }

    @classmethod
    def _path(cls, resource_id):
        return '{0}/{1}/projects'.format(cls.resource_name, resource_id)
