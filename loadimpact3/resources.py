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

import hashlib
from time import sleep

import sys

__all__ = ['DataStore', 'LoadZone', 'Test',
           'UserScenario', 'UserScenarioValidation']

import json

from .exceptions import ApiError, CoercionError, ResponseParseError
from .fields import (
    DataStoreListField, DateTimeField, DictField, Field, IntegerField,
    UnicodeField, BooleanField, ListField, TimeStampField, FloatField)
from .utils import is_dict_different
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


class ListWithParamsMixin(object):
    list_content_type = 'application/json'

    fields = {
        'type': IntegerField,
        'offset': IntegerField,
        'ids': DictField,
    }

    @classmethod
    def _path(cls, resource_id):
        return '{0}/{1}/result_ids'.format(cls.resource_name, resource_id)

    @classmethod
    def list(cls, client, resource_id=None, data=None):
        path = cls._path(resource_id=resource_id)
        response = client.post(path,
                               headers={'Content-Type': cls.list_content_type},
                               data=json.dumps(data))
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


class Test(Resource, ListMixin, GetMixin, CreateMixin, DeleteMixin):
    resource_name = 'tests'
    resource_response_object_name = 'test'
    resource_response_objects_name = 'tests'
    project_id = None

    fields = {
        'id': IntegerField,
        'name': (UnicodeField, Field.SERIALIZE),
        'config': (DictField, Field.SERIALIZE),
        'last_test_run_id': IntegerField,
    }

    @classmethod
    def _path(cls, resource_id=None):
        if cls.project_id:
            return '{0}?project_id={1}'.format(cls.resource_name, cls.project_id)
        return super(Test, cls)._path(resource_id)

    def start_test_run(self):
        """Start test run based on this test config.

        Returns:
            TestRun with 'Created' status.
        Raises:
            ClientError from the client.
        """
        return self.client.create_test_run({'test_id': self.id})


class _TestRunResultStream(object):
    def __init__(self, test_run, result_ids, raise_api_errors=False):
        self.test_run = test_run
        self.result_ids = result_ids
        self.raise_api_errors = raise_api_errors
        self._last = dict([(rid, {'offset': -1, 'data': {}}) for rid in result_ids])
        self._last_two = []
        self._series = {}

    @property
    def series(self):
        return self._series

    def __call__(self, poll_rate=3, post_polls=5):
        """
        Poll the API for results of a TestRun and yield the differences
        as `TestRunMetricPoint`s until there are no new results.

        :param poll_rate: seconds between API polls.
        :param post_polls: number of polls with the same results to make
        before marking the polling as completed.
        """
        def is_done(self):
            if not self.test_run.is_done(raise_api_errors=self.raise_api_errors) or not self.is_done():
                return False
            return True

        done = False
        while not done or 0 < post_polls:
            done = is_done(self)
            if done:
                post_polls -= 1
            # Build the query, requesting results only from each offset onward.
            q = ['%s|%d' % (rid, self._last.get(rid, {}).get('offset', -1))
                 for rid in self.result_ids]

            try:
                results = TestRunResults.list(self.test_run.client, self.test_run.id, {'ids': ','.join(q)})
            except ApiError as e:
                if self.raise_api_errors:
                    raise e
                results = []
            change = {}
            for result in results:
                try:
                    if result.offset > self._last[result.sid]['offset']:
                        # Store the changes for the metric and the offset.
                        change[result.sid] = result.data[-1]
                        self._last[result.sid]['data'] = result.data[-1]
                        self._last[result.sid]['offset'] = result.offset
                except (IndexError, KeyError):
                    continue
                self._series.setdefault(result.id, []).extend(result.data)

            if 2 == len(self._last_two):
                self._last_two.pop(0)
            self._last_two.append(self._last)
            if change:
                # Coerce the changes to TestRunMetricPoint before returning.
                yield {k: TestRunMetricPoint(None, **v) for k, v in change.items()}
            sleep(poll_rate)

    def __iter__(self):
        return self.__call__()

    def is_done(self):
        if 2 != len(self._last_two):
            return False
        if is_dict_different(self._last_two[0], self._last_two[1]):
            return False
        return True

    def _get(self, path, params):
        return self.test_run.client.get(path, params=params)


class TestRun(Resource, ListMixin, GetMixin, CreateMixin, DeleteMixin):
    resource_name = 'test-runs'
    resource_response_object_name = 'test_run'
    resource_response_objects_name = 'test_runs'

    stream_class = _TestRunResultStream

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
    STATUS_ABORTED_SCRIPT_ERROR = 9
    STATUS_ABORTING_THRESHOLD = 10
    STATUS_ABORTED_THRESHOLD = 11
    STATUS_FAILED_THRESHOLD = 12

    fields = {
        'id': IntegerField,
        'queued': DateTimeField,
        'started': DateTimeField,
        'ended': DateTimeField,
        'status': IntegerField,
        'status_text': UnicodeField,
    }

    def abort(self):
        self.client.post(self.__class__._path(resource_id=self.id, action='abort'))

    def list_test_run_result_ids(self, data):
        return self.client.list_test_run_result_ids(self.id, data)

    def result_stream(self, result_ids=None, raise_api_errors=False):
        """Get access to result stream.
        Args:
            result_ids: List of result IDs to include in this stream.
        Returns:
            Test result stream object.
        """
        if not result_ids:
            load_zone_id = LoadZone.name_to_id(LoadZone.AGGREGATE_WORLD)
            result_ids = [
                TestRunMetric.result_id_from_name(TestRunMetric.ACTIVE_USERS, load_zone_id),
                TestRunMetric.result_id_from_name(TestRunMetric.REQUESTS_PER_SECOND, load_zone_id),
                TestRunMetric.result_id_from_name(TestRunMetric.BANDWIDTH, load_zone_id),
                TestRunMetric.result_id_from_name(TestRunMetric.USER_LOAD_TIME, load_zone_id),
                TestRunMetric.result_id_from_name(TestRunMetric.FAILURE_RATE, load_zone_id)
            ]
        return self.__class__.stream_class(self, result_ids, raise_api_errors=raise_api_errors)

    def is_done(self, raise_api_errors=False):
        """Check whether test is done or not.
        Returns:
            True if test has completed, otherwise False.
        Raises:
            ResponseParseError: Unable to parse response (sync call) from API.
        """
        try:
            self.sync()
            if self.status in [self.STATUS_FINISHED, self.STATUS_TIMED_OUT, self.STATUS_ABORTED_USER,
                               self.STATUS_ABORTED_SYSTEM, self.STATUS_ABORTED_SCRIPT_ERROR,
                               self.STATUS_ABORTED_THRESHOLD, self.STATUS_FAILED_THRESHOLD]:
                return True
        except ApiError as e:
            if raise_api_errors:
                raise e
        return False


class TestRunResultsIds(Resource, ListWithParamsMixin):
    resource_name = 'test-runs'
    resource_response_object_name = 'test_run_result_ids'
    resource_response_objects_name = 'test_run_result_ids'

    fields = {
        'type': IntegerField,
        'offset': IntegerField,
        'ids': DictField,
    }

    # TestRunResults type codes.
    TYPE_COMMON = 1
    TYPE_URL = 2
    TYPE_LIVE_FEEDBACK = 3
    TYPE_LOG = 4
    TYPE_CUSTOM_METRIC = 5
    TYPE_PAGE = 6
    TYPE_DTP = 7
    TYPE_SYSTEM = 8
    TYPE_SERVER_METRIC = 9
    TYPE_INTEGRATION = 10

    TYPE_CODE_TO_TEXT_MAP = {
        TYPE_COMMON: 'common',
        TYPE_URL: 'url',
        TYPE_LIVE_FEEDBACK: 'live_feedback',
        TYPE_LOG: 'log',
        TYPE_CUSTOM_METRIC: 'custom_metric',
        TYPE_PAGE: 'page',
        TYPE_DTP: 'dtp',
        TYPE_SYSTEM: 'system',
        TYPE_SERVER_METRIC: 'server_metric',
        TYPE_INTEGRATION: 'integration'
    }

    @classmethod
    def _path(cls, resource_id):
        return '{0}/{1}/result_ids'.format(cls.resource_name, resource_id)

    @classmethod
    def results_type_code_to_text(cls, results_type_code):
        return cls.TYPE_CODE_TO_TEXT_MAP.get(results_type_code, 'unknown')


class TestRunResults(Resource, ListWithParamsMixin):
    resource_name = 'test-runs'
    resource_response_object_name = 'test_run_results'
    resource_response_objects_name = 'test_run_results'

    fields = {
        'id': UnicodeField,
        'sid': UnicodeField,
        'type': IntegerField,
        'offset': IntegerField,
        'data': ListField,
    }

    @classmethod
    def _path(cls, resource_id):
        return '{0}/{1}/results'.format(cls.resource_name, resource_id)


class TestRunMetric(object):
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
        return '__li_page_%s:%s:%s' % (hashlib.md5(page_name).hexdigest(),
                                       str(load_zone_id), str(user_scenario_id))

    @classmethod
    def result_id_for_url(cls, url, load_zone_id, user_scenario_id,
                          method='GET', status_code=200):
        if sys.version_info >= (3, 0):
            url = url.encode('utf-8')
        else:
            if isinstance(url, unicode):
                url = url.encode('utf-8')
        return '__li_url_%s:%s:%s:%s:%s' % (hashlib.md5(url).hexdigest(),
                                            str(load_zone_id),
                                            str(user_scenario_id),
                                            str(status_code), method)


class TestRunMetricPoint(Resource):
    """
    Individual point of a Test Run Metric. This class is provided by
    convenience, as the API does not expose get/list methods but rather
    is included as `data` on the output of TestRunResults.
    """
    fields = {
        'timestamp': TimeStampField,
        'data': DictField
    }

    @classmethod
    def _path(cls, resource_id=None, action=None):
        raise NotImplementedError

    @property
    def aggregate_function(self):
        return next(iter(self.data.keys()))

    @property
    def value(self):
        return next(iter(self.data.values()))


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
