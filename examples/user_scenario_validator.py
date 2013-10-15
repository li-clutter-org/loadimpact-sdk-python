#!/usr/bin/env python
# coding=utf-8

import optparse
import sys
import traceback

from loadimpact import (
    ApiTokenClient, ApiError, UserScenarioValidation,
    __version__ as li_sdk_version)


def start_validation(client, user_scenario_id):
    assert user_scenario_id is not None, \
        "'user_scenario_id' is mandatory for 'start'"

    user_scenario = client.get_user_scenario(user_scenario_id)
    validation = user_scenario.validate()
    stream = validation.result_stream()

    print("Starting validation #%d..." % (validation.id,))
    for result in stream:
        if 'stack_trace' in result:
            print('[%s]: %s @ line %s'
                  % (result['timestamp'], result['message'],
                     result['line_number']))
            print('Stack trace:')
            for frame in result['stack_trace']:
                print('\t%s:%s in %s' % (frame[2], frame[1], frame[0]))
        else:
            print('[%s]: %s' % (result['timestamp'], result['message']))
    print("Validation completed with status '%s'"
          % (UserScenarioValidation.status_code_to_text(validation.status)))


def usage():
    print(u"Usage: specify a user scenario ID")


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

    user_scenario_id = None

    if 1 <= len(args):
        user_scenario_id = args[0]

    try:
        client = ApiTokenClient(opts.api_token, debug=opts.debug)
        start_validation(client, user_scenario_id)
    except ApiError:
        print(u"Error encountered: %s" % traceback.format_exc())
