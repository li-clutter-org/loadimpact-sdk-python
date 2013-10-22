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

import optparse
import sys
import traceback

from loadimpact import (
    ApiTokenClient, ApiError, LoadZone, Test, TestConfig, TestResult,
    __version__ as li_sdk_version)


def start_test(client, test_config_id):
    assert test_config_id is not None, \
        "'test_config_id' is mandatory for 'start'"

    test_id = TestConfig.start_test_from_id(
        client, test_config_id)
    test = Test.get(client, test_id)
    world_id = LoadZone.name_to_id(LoadZone.AGGREGATE_WORLD)
    stream = test.result_stream([
        TestResult.result_id_from_name(TestResult.LIVE_FEEDBACK),
        TestResult.result_id_from_name(TestResult.USER_LOAD_TIME,
                                       load_zone_id=world_id),
        TestResult.result_id_from_name(TestResult.ACTIVE_USERS,
                                       load_zone_id=world_id)])

    try:
        print("Starting test #%d (view test: %s)..." % (test.id, test.public_url))
        try:
            for data in stream:
                print(data)  
        except KeyboardInterrupt:
            print("Aborting test.")
            test.abort()
            for data in stream:
                print(data)
        print("Test completed with status '%s'"
              % (Test.status_code_to_text(test.status)))
    except ApiError as e:
        print("Aborting test, unhandled error: %s" % str(e))
        test.abort()


def usage():
    print("Usage: specify a test configuration ID")


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

    test_config_id = None

    if 1 <= len(args):
        test_config_id = args[0]

    try:
        client = ApiTokenClient(opts.api_token, debug=opts.debug)
        start_test(client, test_config_id)
    except ApiError:
        print("Error encountered: %s" % traceback.format_exc())
