#!/usr/bin/env python
# coding=utf-8

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


def inspect_resource(api_token, resource_name, resource_id=None, debug=False):
    client = ApiTokenClient(api_token)
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


if __name__ == "__main__":
    p = optparse.OptionParser(version=('%%prog %s' % li_sdk_version))
    p.add_option('--api-token', action='store',
                 dest='api_token', default=None,
                 help=("Your Load Impact API token."))
    p.add_option('--debug', action='store_true', dest='debug', default=False,
                 help=("."))
    opts, args = p.parse_args()

    if 1 > len(args):
        print(u"You need to specify at least 1 argument (to list): "
              u"resource_name")
        print(u"Specify 2 arguments (to get specific resource): resource_name, "
              u"resource_id")
        sys.exit(2)

    resource_name = args[0]
    resource_id = None
    if 1 < len(args):
        resource_id = int(args[1])

    try:
        inspect_resource(opts.api_token, resource_name, resource_id=resource_id,
                         debug=opts.debug)
    except ApiError:
        print(u"Error encountered: %s" % traceback.format_exc())
