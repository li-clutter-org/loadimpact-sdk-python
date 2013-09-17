# coding=utf-8

__all__ = ['DataStore', 'LoadZone', 'Test', 'TestConfig', 'TestResult',
           'UserScenario']

import json
import hashlib

from exceptions import CoercionError, ResponseParseError
from fields import (
    DateTimeField, DictField, IntegerField, ListField, StringField,
    UnicodeField)
from pprint import pformat
from utils import is_dict_different


class Resource(object):
    """All API resources derive from this base class."""

    fields = {}

    def __init__(self, **kwargs):
        super(Resource, self).__setattr__('_fields', {})
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
            if not name in self._fields:
                self._fields[name] = fields[name](value)
            else:
                self._fields[name].value = value
        super(Resource, self).__setattr__(name, value)

    def __repr__(self):
        return "<Resource:%s>\n%s" % (self.__class__.__name__,
                                      pformat(self._fields))

    @classmethod
    def _path(cls, resource_id=None, action=None):
        if resource_id:
            if action:
                return '%s/%s/%s' % (cls.resource_name, str(resource_id),
                                     action)
            else:
                return '%s/%s' % (cls.resource_name, str(resource_id))
        else:
            return cls.resource_name

    def _set_fields(self, data):
        fields = self.__class__.fields
        for k, f in fields.iteritems():
            self._fields[k] = f(data.get(k, None))


class GetMixin(object):
    @classmethod
    def get(cls, client, resource_id):
        response = client.get(cls._path(resource_id))
        try:
            instance = cls()
            instance._set_fields(response.json())
            return instance
        except CoercionError, e:
            raise ResponseParseError(e)

    def sync(self, client):
        response = client.get(self.__class__._path(self.id))
        try:
            self._set_fields(response.json())
        except CoercionError, e:
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
            instance = cls()
            instance._set_fields(response.json())
            return instance
        except CoercionError, e:
            raise ResponseParseError(e)


class DeleteMixin(object):
    def delete(self, client):
        client.delete(self.__class__._path(resource_id=self.id))

    @classmethod
    def delete_with_id(cls, client, resource_id):
        client.delete(cls._path(resource_id=resource_id))


class UpdateMixin(object):
    def update(self, client, data):
        if isinstance(data, dict):
            data = json.dumps(data)
        response = client.put(cls._path(), data=data)
        try:
            instance = cls()
            instance._set_fields(response.json())
            return instance
        except CoercionError, e:
            raise ResponseParseError(e)


class ListMixin(object):
    @classmethod
    def list(cls, client):
        response = client.get(cls._path())
        try:
            resources = []
            l = response.json()
            for r in l:
                instance = cls()
                instance._set_fields(r)
                resources.append(instance)
            return resources
        except CoercionError, e:
            raise ResponseParseError(e)


class DataStore(Resource, ListMixin, GetMixin, CreateMixin, DeleteMixin):
    resource_name = 'data-stores'
    create_content_type = 'multipart/form-data'
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

    def has_conversion_finished(self, client):
        """Check whether data store conversion has finished or not.

        Args:
            client: API client instance.

        Returns:
            True if data store conversion has completed, otherwise False.

        Raises:
            ResponseParseError: Unable to parse response (sync call) from API.
        """
        self.sync(client)
        if self.status in [DataStore.STATUS_FINISHED, DataStore.STATUS_FAILED]:
            return True
        return False


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
            raise ValueError(u"There's no load zone with name '%s'" % name)


class TestResult(object):
    ACCUMULATED_LOAD_TIME = '__li_accumulated_load_time'
    ACTIVE_USERS = '__li_clients_active'
    ACTIVE_CONNECTIONS = '__li_connections_active'
    BANDWIDTH = '__li_bandwidth'
    CONTENT_TYPES = '__li_content_type'
    CONTENT_TYPES_LOAD_TIME = '__li_content_type_load_time'
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
        return '__custom_%s:%s:%s' % (hashlib.md5(custom_name).hexdigest(),
                                     str(load_zone_id), str(user_scenario_id))

    @classmethod
    def result_id_for_page(cls, page_name, load_zone_id, user_scenario_id):
        return '__li_page%s:%s:%s' % (hashlib.md5(page_name).hexdigest(),
                                      str(load_zone_id), str(user_scenario_id))

    @classmethod
    def result_id_for_url(cls, url, load_zone_id, user_scenario_id,
                          method='GET', status_code=200):
        return '__li_url%s:%s:%s:%s:%s' % (hashlib.md5(url).hexdigest(),
                                           str(load_zone_id),
                                           str(user_scenario_id),
                                           method, str(status_code))


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

    def is_done(self, client):
        """Check whether test is done or not.

        Args:
            client: API client instance.

        Returns:
            True if test has completed, otherwise False.

        Raises:
            ResponseParseError: Unable to parse response (sync call) from API.
        """
        self.sync(client)
        if self.status in [Test.STATUS_FINISHED, Test.STATUS_TIMED_OUT,
                           Test.STATUS_ABORTED_USER,
                           Test.STATUS_ABORTED_SYSTEM]:
            return True
        return False

    def result_stream(self, result_ids=[TestResult.USER_LOAD_TIME,
                                        TestResult.ACTIVE_USERS]):
        """Get access to result stream.

        Args:
            result_ids: List of result IDs to include in this stream.

        Returns:
            Test result stream object.
        """
        return _TestResultStream(self.id, result_ids)

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
        'name': UnicodeField,
        'url': UnicodeField,
        'config': DictField,
        'public_url': UnicodeField,
        'created': DateTimeField,
        'updated': DateTimeField
    }

    # User types
    SBU = 'sbu'
    VU = 'vu'

    def __init__(self, **kwargs):
        super(TestConfig, self).__init__(**kwargs)
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
            raise ValueError(u"'user_type' must be either 'sbu' or 'vu'")
        self.config['user_type'] = value

    def start_test(self, client):
        """Start test based on this test config.

        Args:
            client: API client instance.

        Returns:
            Test ID of created and started test.

        Raises:
            ResponseParseError: Unable to parse response from API.
        """
        return self.__class__.start_test_from_id(client, self.id)

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
        except KeyError, e:
            raise ResponseParseError(e)

    def _set_default_config(self):
        if 'load_schedule' not in self.config:
            self.config['load_schedule'] = []

        if 'tracks' not in self.config:
            self.config['tracks'] = []

        if 'user_type' not in self.config:
            self.config['user_type'] = TestConfig.SBU


class _TestResultStream(Resource):
    resource_name = 'tests'

    def __init__(self, test_id, result_ids):
        self.test_id = test_id
        self.result_ids = result_ids
        self._last = {rid.split(':')[0]: {'offset': -1} for rid in result_ids}
        self._last_two = []
        self._series = {}

    def is_done(self):
        if 2 != len(self._last_two):
            return False
        return False if is_dict_different(self._last_two[0], self._last_two[1]) else True

    def last(self, result_id=None):
        if not result_id:
            return self._last
        return self._last[result_id]

    @property
    def series(self):
        return self._series

    def poll(self, client):
        q = ['%s|%d' % (rid.split(':')[0], self._last.get(rid.split(':')[0], {}).get('offset', -1))
             for rid in self.result_ids]
        response = client.get(self.__class__._path(resource_id=self.test_id,
                                                   action='results'),
                              params={'ids': ','.join(q)})
        results = response.json()
        for rid, data in results.iteritems():
            try:
                self._last[rid] = data[0]
            except IndexError:
                continue
            if rid not in self._series:
                self._series[rid] = []
            self._series[rid].extend(data)

        if 2 == len(self._last_two):
            self._last_two.pop(0)
        self._last_two.append(self._last)


class UserScenario(Resource, ListMixin, GetMixin, CreateMixin, DeleteMixin,
                   UpdateMixin):
    resource_name = 'user-scenarios'
    fields = {
        'id': IntegerField,
        'name': UnicodeField,
        'script_type': StringField,
        'load_script': UnicodeField,
        'data_stores': ListField,
        'created': DateTimeField,
        'updated': DateTimeField
    }

    def clone(client, name=None):
        self.post(client, data={''})


class UserScenarioValidation(Resource, ListMixin, GetMixin, CreateMixin):
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
