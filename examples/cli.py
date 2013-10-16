#!/usr/bin/env python
# coding=utf-8

"""
Copyright 2013 Load Impact

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

import json
import optparse
import sys
import traceback

from loadimpact import (
    ApiTokenClient, ApiError, DataStore, LoadZone, TestConfig, UserScenario,
    __version__ as li_sdk_version)


def get_or_list(client, cls, resource_id=None):
    if resource_id:
        return [cls.get(client, resource_id)]
    else:
        return cls.list(client)


def handle_get_or_list(client, resource_name, resource_id=None):
    resources = []

    if resource_name in ['ds', 'datastore', 'data-store', 'data_store']:
        resources = get_or_list(client, DataStore, resource_id)
    elif resource_name in ['lz', 'loadzone', 'load-zone', 'load_zone']:
        resources = get_or_list(client, LoadZone, None)
    elif resource_name in ['tc', 'testconfig', 'test-config', 'test_config']:
        resources = get_or_list(client, TestConfig, resource_id)
    elif resource_name in ['us', 'userscenario', 'user-scenario',
                           'user_scenario']:
        resources = get_or_list(client, UserScenario, resource_id)
    else:
        raise RuntimeError(u"Unknown resource: %s" % resource_name)

    for resource in resources:
        print(repr(resource))


def handle_get(client, resource_name, resource_id):
    assert resource_id is not None, "'resource_id' is mandatory for 'get'"
    handle_get_or_list(client, resource_name, resource_id)


def handle_create(client, resource_name, resource_fields, resource_file=None):
    assert resource_fields is not None, \
        "'resource_fields' is mandatory for 'create'"

    if resource_name in ['ds', 'datastore', 'data-store', 'data_store']:
        assert resource_file is not None, \
            "'resource_file' is mandatory for data store 'create'"
        with open(resource_file, 'r') as f:
            DataStore.create(client, resource_fields, file_object=f)
    elif resource_name in ['tc', 'testconfig', 'test-config', 'test_config']:
        TestConfig.create(client, resource_fields)
    elif resource_name in ['us', 'userscenario', 'user-scenario',
                           'user_scenario']:
        UserScenario.create(client, resource_fields)
    else:
        raise RuntimeError(u"Unknown resource or type not deletable: %s"
                           % resource_name)

    print(u"Resource created!")


def handle_update(client, resource_name, resource_id, resource_fields):
    assert resource_id is not None, "'resource_id' is mandatory for 'update'"
    assert resource_fields is not None, \
        "'resource_fields' is mandatory for 'update'"

    if resource_name in ['tc', 'testconfig', 'test-config', 'test_config']:
        TestConfig.update(client, resource_id)
    elif resource_name in ['us', 'userscenario', 'user-scenario',
                           'user_scenario']:
        UserScenario.update(client, resource_id)
    else:
        raise RuntimeError(u"Unknown resource or type not deletable: %s"
                           % resource_name)

    print(u"Resource updated!")


def handle_delete(client, resource_name, resource_id):
    assert resource_id is not None, "'resource_id' is mandatory for 'delete'"

    if resource_name in ['ds', 'datastore', 'data-store', 'data_store']:
        DataStore.delete_with_id(client, resource_id)
    elif resource_name in ['tc', 'testconfig', 'test-config', 'test_config']:
        TestConfig.delete_with_id(client, resource_id)
    elif resource_name in ['us', 'userscenario', 'user-scenario',
                           'user_scenario']:
        UserScenario.delete_with_id(client, resource_id)
    else:
        raise RuntimeError(u"Unknown resource or type not deletable: %s"
                           % resource_name)

    print(u"Resource deleted!")


def handle_start(client, resource_name, resource_id):
    assert resource_name not in ['tc', 'testconfig', 'test-config',
                                 'test_config'], \
        "'resource_id' is mandatory for 'start'"
    assert resource_id is not None, "'resource_id' is mandatory for 'start'"

    TestConfig.start_with_id(client, resource_id)

    print(u"Test started!")


def usage():
    print(u"Usage:")
    print(u"\tresource_name: name of resource, eg. 'userscenario', "
          u"'testconfig', 'datastore' etc. or shorthand form 'us', 'tc', 'ds' "
          u"etc.")
    print(u"\t(optional) resource_action: action to perform, one of 'list' "
          u"(default), 'get', 'create', 'update', 'delete' or 'start' (only "
          u"for test configs)")
    print(u"")
    print(u"'list' specific arguments:")
    print(u"\t-")
    print(u"")
    print(u"'get' specific arguments:")
    print(u"\tresource_id: ID of resource to get")
    print(u"")
    print(u"'create' specific arguments:")
    print(u"\tresource_fields: JSON string with resource fields")
    print(u"\t(optional) resource_file: Data store CSV file to upload for data "
          u"store resource")
    print(u"")
    print(u"'update' specific arguments:")
    print(u"\tresource_id: ID of resource to update")
    print(u"\tresource_fields: JSON string with resource fields to update")
    print(u"")
    print(u"'delete' specific arguments:")
    print(u"\tresource_id: ID of resource to delete")
    print(u"")
    print(u"'start' specific arguments:")
    print(u"\tresource_id: ID of test configuration to start a test from")


if __name__ == "__main__":
    p = optparse.OptionParser(version=('%%prog %s' % li_sdk_version))
    p.add_option('--api-token', action='store',
                 dest='api_token', default=None,
                 help=("Your Load Impact API token."))
    p.add_option('--debug', action='store_true', dest='debug', default=False,
                 help=("."))
    opts, args = p.parse_args()

    if 1 > len(args):
        usage()
        sys.exit(2)

    resource_name = args[0]
    resource_action = 'list'
    resource_id = None
    resource_fields = None
    resource_file = None

    if 1 < len(args):
        resource_action = args[1]
    if 2 < len(args):
        if resource_action in ['get', 'update', 'delete']:
            resource_id = int(args[2])
        elif resource_action in ['create']:
            resource_fields = json.loads(args[2])
    if 3 < len(args):
        if resource_action in ['update']:
            resource_fields = json.loads(args[3])
        elif resource_action in ['create']:
            resource_file = args[3]

    try:
        client = ApiTokenClient(opts.api_token, debug=opts.debug)

        if 'list' == resource_action:
            handle_get_or_list(client, resource_name, resource_id)
        elif 'get' == resource_action:
            handle_get(client, resource_name, resource_id)
        elif 'create' == resource_action:
            handle_create(client, resource_name, resource_fields, resource_file)
        elif 'update' == resource_action:
            handle_update(client, resource_name, resource_id, resource_fields)
        elif 'delete' == resource_action:
            handle_delete(client, resource_name, resource_id)
        elif 'start' == resource_action:
            handle_start(client, resource_name, resource_id)
    except ApiError:
        print(u"Error encountered: %s" % traceback.format_exc())
