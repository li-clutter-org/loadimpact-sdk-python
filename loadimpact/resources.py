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

__all__ = ['DataStore', 'LoadZone', 'Test', 'TestConfig', 'TestResult',
           'UserScenario', 'UserScenarioValidation']

import json
import hashlib
import sys

from .exceptions import CoercionError, ConflictError, ResponseParseError
from .fields import (
    DataStoreListField, DateTimeField, DictField, Field, IntegerField,
    StringField, UnicodeField)
from pprint import pformat
from time import sleep
from .utils import is_dict_different


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
            instance._set_fields(response.json())
            return instance
        except CoercionError as e:
            raise ResponseParseError(e)

    def sync(self):
        response = self.client.get(self.__class__._path(self.id))
        try:
            self._set_fields(response.json())
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
            instance._set_fields(response.json())
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
    update_content_type = 'application/json'

    def update(self, data=None):
        if data:
            if isinstance(data, str):
                data = json.loads(data)
            self._set_fields(data)

        headers = {'Content-Type': self.__class__.update_content_type}
        data = {}
        fields = self.__class__.fields
        for k, f in fields.items():
            if self._fields[k].has_option(Field.SERIALIZE):
                data[k] = getattr(self, k)

        response = self.client.put(self.__class__._path(resource_id=self.id),
                                   headers=headers, data=json.dumps(data))
        try:
            self._set_fields(response.json())
        except CoercionError as e:
            raise ResponseParseError(e)


class ListMixin(object):
    @classmethod
    def list(cls, client):
        response = client.get(cls._path())
        try:
            resources = []
            l = response.json()
            if isinstance(l, list):
                for r in l:
                    instance = cls(client)
                    instance._set_fields(r)
                    resources.append(instance)
            return resources
        except CoercionError as e:
            raise ResponseParseError(e)


class DataStore(Resource, ListMixin, GetMixin, CreateMixin, DeleteMixin):
    resource_name = 'data-stores'
    fields = {
        'id': IntegerField,
        'name': UnicodeField,
        'status': IntegerField,
        'rows': IntegerField,
        'created': DateTimeField,
        'updated': DateTimeField
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

        Raises:
            ResponseParseError: Unable to parse response (sync call) from API.
        """
        self.sync()
        if self.status in [DataStore.STATUS_FINISHED, DataStore.STATUS_FAILED]:
            return True
        return False

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


class TestResult(object):
    ACCUMULATED_LOAD_TIME = '__li_accumulated_load_time'
    ACTIVE_USERS = '__li_clients_active'
    ACTIVE_CONNECTIONS = '__li_connections_active'
    BANDWIDTH = '__li_bandwidth'
    CONTENT_TYPES = '__li_content_type'
    CONTENT_TYPES_LOAD_TIME = '__li_content_type_load_time'
    FAILURE_RATE = '__li_failure_rate'
    LIVE_FEEDBACK = '__li_live_feedback'
    LOAD_GENERATOR_CPU_UTILIZATION = '__li_loadgen_cpu_utilization'
    LOAD_GENERATOR_MEMORY_UTILIZATION = '__li_loadgen_memory_utilization'
    LOG = '__li_log'
    PROGRESS_PERCENT = '__li_progress_percent_total'
    REQUESTS_PER_SECOND = '__li_requests_per_second'
    TOTAL_BYTES_RECEIVED = '__li_total_rx_bytes'
    TOTAL_REQUESTS = '__li_total_requests'
    USER_LOAD_TIME = '__li_user_load_time'
    USER_SCENARIO_REPETITION_SUCCESS_RATE = '__li_reps_succeeded_percent'
    USER_SCENARIO_REPETITION_FAILURE_RATE = '__li_reps_failed_percent'

    @classmethod
    def result_id_from_name(cls, name, load_zone_id=None, user_scenario_id=None):
        if not load_zone_id:
            return name
        if not user_scenario_id:
            return '%s:%s' % (name, str(load_zone_id))
        return '%s:%s:%s' % (name, str(load_zone_id), str(user_scenario_id))

    @classmethod
    def result_id_from_custom_metric_name(cls, custom_name, load_zone_id,
                                          user_scenario_id):
        if sys.version_info >= (3, 0):
            custom_name = custom_name.encode('utf-8')
        else:
            if isinstance(custom_name, unicode):
                custom_name = custom_name.encode('utf-8')
        return '__custom_%s:%s:%s' % (hashlib.md5(custom_name).hexdigest(),
                                      str(load_zone_id), str(user_scenario_id))

    @classmethod
    def result_id_for_page(cls, page_name, load_zone_id, user_scenario_id):
        if sys.version_info >= (3, 0):
            page_name = page_name.encode('utf-8')
        else:
            if isinstance(page_name, unicode):
                page_name = page_name.encode('utf-8')
        return '__li_page%s:%s:%s' % (hashlib.md5(page_name).hexdigest(),
                                      str(load_zone_id), str(user_scenario_id))

    @classmethod
    def result_id_for_url(cls, url, load_zone_id, user_scenario_id,
                          method='GET', status_code=200):
        if sys.version_info >= (3, 0):
            url = url.encode('utf-8')
        else:
            if isinstance(url, unicode):
                url = url.encode('utf-8')
        return '__li_url%s:%s:%s:%s:%s' % (hashlib.md5(url).hexdigest(),
                                           str(load_zone_id),
                                           str(user_scenario_id),
                                           str(status_code), method)


class _TestResultStream(Resource):
    resource_name = 'tests'

    def __init__(self, test, result_ids):
        self.test = test
        self.result_ids = result_ids
        self._last = dict([(rid, {'offset': -1}) for rid in result_ids])
        self._last_two = []
        self._series = {}

    @property
    def series(self):
        return self._series

    def __call__(self, poll_rate=3, post_polls=5):
        def is_done(self):
            if not self.test.is_done() or not self.is_done():
                return False
            return True

        done = False
        while not done or 0 < post_polls:
            done = is_done(self)
            if done:
                post_polls = post_polls - 1
            q = ['%s|%d' % (rid, self._last.get(rid, {}).get('offset', -1))
                 for rid in self.result_ids]
            path = self.__class__._path(
                resource_id=self.test.id, action='results')
            response = self._get(path, {'ids': ','.join(q)})
            results = response.json()
            change = {}
            for rid, data in results.items():
                try:
                    if data[0]['offset'] > self._last[rid]['offset']:
                        change[rid] = data[-1]
                        self._last[rid] = data[-1]
                except (IndexError, KeyError):
                    continue
                if rid not in self._series:
                    self._series[rid] = []
                self._series[rid].extend(data)

            if 2 == len(self._last_two):
                self._last_two.pop(0)
            self._last_two.append(self._last)
            if change:
                yield change
            sleep(poll_rate)

    def __iter__(self):
        return self.__call__()

    def is_done(self):
        if 2 != len(self._last_two):
            return False
        if is_dict_different(self._last_two[0], self._last_two[1]):
            return False
        return True

    def last(self, result_id=None):
        if not result_id:
            return self._last
        return self._last[result_id]

    def _get(self, path, params):
        return self.test.client.get(path, params=params)


class Test(Resource, ListMixin, GetMixin, CreateMixin, DeleteMixin):
    resource_name = 'tests'
    fields = {
        'id': IntegerField,
        'title': UnicodeField,
        'url': UnicodeField,
        'status': IntegerField,
        'status_text': UnicodeField,
        'public_url': UnicodeField,
        'started': DateTimeField,
        'ended': DateTimeField
    }
    stream_class = _TestResultStream

    # Test status codes
    STATUS_CREATED = -1
    STATUS_QUEUED = 0
    STATUS_INITIALIZING = 1
    STATUS_RUNNING = 2
    STATUS_FINISHED = 3
    STATUS_TIMED_OUT = 4
    STATUS_ABORTING_USER = 5
    STATUS_ABORTED_USER = 6
    STATUS_ABORTING_SYSTEM = 7
    STATUS_ABORTED_SYSTEM = 8

    def abort(self):
        """Abort test.

        Returns:
            True if abort has been acknowledged and test is in a test where
            it's possible to abort, False otherwise.
        """
        try:
            self.client.post(self.__class__._path(resource_id=self.id,
                                                  action='abort'))
        except ConflictError:
            return False
        return True

    def is_done(self):
        """Check whether test is done or not.

        Returns:
            True if test has completed, otherwise False.

        Raises:
            ResponseParseError: Unable to parse response (sync call) from API.
        """
        self.sync()
        if self.status in [Test.STATUS_FINISHED, Test.STATUS_TIMED_OUT,
                           Test.STATUS_ABORTED_USER,
                           Test.STATUS_ABORTED_SYSTEM]:
            return True
        return False

    def result_stream(self, result_ids=None):
        """Get access to result stream.

        Args:
            result_ids: List of result IDs to include in this stream.

        Returns:
            Test result stream object.
        """
        if not result_ids:
            result_ids = [
                TestResult.result_id_from_name(
                    TestResult.USER_LOAD_TIME,
                    load_zone_id=LoadZone.name_to_id(LoadZone.AGGREGATE_WORLD)),
                TestResult.result_id_from_name(
                    TestResult.ACTIVE_USERS,
                    load_zone_id=LoadZone.name_to_id(LoadZone.AGGREGATE_WORLD))
            ]
        return self.__class__.stream_class(self, result_ids)

    @classmethod
    def status_code_to_text(cls, status_code):
        if Test.STATUS_CREATED == status_code:
            return 'created'
        elif Test.STATUS_QUEUED == status_code:
            return 'queued'
        elif Test.STATUS_INITIALIZING == status_code:
            return 'initializing'
        elif Test.STATUS_RUNNING == status_code:
            return 'running'
        elif Test.STATUS_FINISHED == status_code:
            return 'finished'
        elif Test.STATUS_TIMED_OUT == status_code:
            return 'timed out'
        elif Test.STATUS_ABORTING_USER == status_code:
            return 'aborting (by user)'
        elif Test.STATUS_ABORTED_USER == status_code:
            return 'aborted (by user)'
        elif Test.STATUS_ABORTING_SYSTEM == status_code:
            return 'aborting (by system)'
        elif Test.STATUS_ABORTED_SYSTEM == status_code:
            return 'aborted (by system)'
        return 'unknown'


class TestConfig(Resource, ListMixin, GetMixin, CreateMixin, DeleteMixin,
                 UpdateMixin):
    resource_name = 'test-configs'
    fields = {
        'id': IntegerField,
        'name': (UnicodeField, Field.SERIALIZE),
        'url': (UnicodeField, Field.SERIALIZE),
        'config': (DictField, Field.SERIALIZE),
        'public_url': UnicodeField,
        'created': DateTimeField,
        'updated': DateTimeField
    }

    # User types
    SBU = 'sbu'
    VU = 'vu'

    def __init__(self, client, **kwargs):
        super(TestConfig, self).__init__(client, **kwargs)
        self._set_default_config()

    def add_user_scenario(self, user_scenario,
                          load_zone_id=LoadZone.AMAZON_US_ASHBURN,
                          traffic_percent=100):
        self.add_user_scenario_with_id(user_scenario.id,
                                       load_zone_id=load_zone_id,
                                       traffic_percent=traffic_percent)

    def add_user_scenario_with_id(self, user_scenario_id,
                                  load_zone_id=LoadZone.AMAZON_US_ASHBURN,
                                  traffic_percent=100):
        if 'tracks' not in self.config:
            self.config['tracks'] = []

        self.config['tracks'].append({
            'clips': [{
                'user_scenario_id': user_scenario_id,
                'percent': traffic_percent
            }],
            'loadzone': load_zone_id
        })

    def add_ramp_step(self, users, duration, index=None):
        if 'load_schedule' not in self.config:
            self.config['load_schedule'] = []

        if (index is None or index < 0 or
                index >= len(self.config['load_schedule'])):
            self.config['load_schedule'].append({
                'users': users,
                'duration': duration
            })
        else:
            self.config['load_schedule'].insert(index, {
                'users': users,
                'duration': duration
            })

    @property
    def user_type(self):
        return self.config.get('user_type', TestConfig.SBU)

    @user_type.setter
    def user_type(self, value):
        if value not in [TestConfig.SBU, TestConfig.VU]:
            raise ValueError("'user_type' must be either 'sbu' or 'vu'")
        self.config['user_type'] = value

    def clone(self, name):
        headers = {'Content-Type': self.__class__.create_content_type}
        response = self.client.post(
            self.__class__._path(resource_id=self.id, action='clone'),
            headers=headers, data={'name': name})
        try:
            instance = self.__class__(self.client)
            instance._set_fields(response.json())
            return instance
        except CoercionError as e:
            raise ResponseParseError(e)

    def start_test(self):
        """Start test based on this test config.

        Args:
            client: API client instance.

        Returns:
            Test ID of created and started test.

        Raises:
            ResponseParseError: Unable to parse response from API.
        """
        return self.__class__.start_test_from_id(self.client, self.id)

    @classmethod
    def start_test_from_id(cls, client, test_config_id):
        """Start test based on this test config.

        Args:
            client: API client instance.
            test_config_id: Test configuration ID to create/start test from.

        Returns:
            Test ID of created and started test.

        Raises:
            ResponseParseError: Unable to parse response from API.
        """
        response = client.post(cls._path(resource_id=test_config_id,
                               action='start'))
        try:
            test = response.json()
            return test['id']
        except KeyError as e:
            raise ResponseParseError(e)

    def _set_default_config(self):
        if 'load_schedule' not in self.config:
            self.config['load_schedule'] = []

        if 'tracks' not in self.config:
            self.config['tracks'] = []

        if 'user_type' not in self.config:
            self.config['user_type'] = TestConfig.SBU


class UserScenario(Resource, ListMixin, GetMixin, CreateMixin, DeleteMixin,
                   UpdateMixin):
    resource_name = 'user-scenarios'
    fields = {
        'id': IntegerField,
        'name': (UnicodeField, Field.SERIALIZE),
        'script_type': StringField,
        'load_script': (UnicodeField, Field.SERIALIZE),
        'data_stores': (DataStoreListField, Field.SERIALIZE),
        'created': DateTimeField,
        'updated': DateTimeField
    }

    def clone(self, name):
        headers = {'Content-Type': self.__class__.create_content_type}
        response = self.client.post(
            self.__class__._path(resource_id=self.id, action='clone'),
            headers=headers, data={'name': name})
        try:
            instance = self.__class__(self.client)
            instance._set_fields(response.json())
            return instance
        except CoercionError as e:
            raise ResponseParseError(e)

    def validate(self):
        return self.client.create_user_scenario_validation(
            {'user_scenario_id': self.id})


class _UserScenarioValidationResultStream(Resource):
    resource_name = 'user-scenario-validations'

    def __init__(self, validation):
        self.validation = validation
        self.last_offset = -1
        self.results = []
        self.status = UserScenarioValidation.STATUS_QUEUED
        self.status_text = UserScenarioValidation.status_code_to_text(
            self.status)

    def __call__(self, poll_rate=3):
        while not self.is_done():
            path = self.__class__._path(
                resource_id=self.validation.id, action='results')
            response = self.validation.client.get(
                path, params={'offset': self.last_offset})
            results = response.json()
            self.status = results.get('status', self.status)
            self.status_text = UserScenarioValidation.status_code_to_text(
                self.status)
            if 'results' in results:
                for data in results['results']:
                    self.last_offset = data['offset']
                    yield data
                self.results.extend(results['results'])
                sleep(poll_rate)

        # Sync user scenario validation model to update status.
        self.validation.sync()

    def __iter__(self):
        return self.__call__()

    def is_done(self):
        """Check whether validation is done or not.

        Returns:
            True if validation has completed, otherwise False.
        """
        if self.status in [UserScenarioValidation.STATUS_FINISHED,
                           UserScenarioValidation.STATUS_FAILED]:
            return True
        return False


class UserScenarioValidation(Resource, GetMixin, CreateMixin):
    resource_name = 'user-scenario-validations'
    fields = {
        'id': IntegerField,
        'user_scenario_id': IntegerField,
        'status': IntegerField,
        'status_text': UnicodeField,
        'created': DateTimeField,
        'started': DateTimeField,
        'ended': DateTimeField
    }
    stream_class = _UserScenarioValidationResultStream

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

        Raises:
            ResponseParseError: Unable to parse response (sync call) from API.
        """
        self.sync()
        if self.status in [UserScenarioValidation.STATUS_FINISHED,
                           UserScenarioValidation.STATUS_FAILED]:
            return True
        return False

    def result_stream(self):
        """Get access to result stream.

        Returns:
            User scenario validation result stream object.
        """
        return self.__class__.stream_class(self)

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
