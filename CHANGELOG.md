# Changelog

## v1.1.5 (2015-12-04)

- Fix PEP8 violations.
- Fix contruction of page and URL result metric IDs.
- Add test coverage reporting through Coveralls.io.

## v1.1.4 (2015-09-29)

- Fix data store create doc bug in README.
- Set content type header on PUT requests.
- Default to show full API response message on error response.

## v1.1.3 (2015-08-28)

- Clarify unit of duration property when creating test config.
- Better handling of error messages from API.
- Add comment about need for user scenario in test config to README.
- Fix failing tests.

## v1.1.2 (2015-07-10)

- Add setup.cfg.

## v1.1.1 (2015-07-10)

- Fix inconsistency in representation of data stores attached to a user scenario.
- Fix PyPI badges.
- Added missing "user_type" parameter in the create_test_config() example in README.
- Fix doc error how to specify load zone in test config.

## v1.1.0 (2013-11-05)

- Added missing client.get_test(test_id) and client.list_tests() methods.
- Fixed URL result ID string construction bug, swapped method and status code.

## v1.0.0 (2013-10-22)

- Improved APIs for create/get/list to avoid having to pass a client object
  around.
- Added support for user scenario validation.
- Added clone support for test configuration and user scenarios.
- Fixed update to work for resources supporting that operation.
- Cleaned up code and added greater test coverage.
- Python 3.2 and 3.3 support.

## v0.1.1 (2013-10-03)

- Added auto installation of setuptools if not already present or if old version
  is present.
- Fixed selection of last data point in test result data stream poll() method.

## v0.1.0 (2013-09-18)

- First beta release.
