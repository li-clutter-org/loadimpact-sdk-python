# Load Impact Python SDK [![Build Status](https://travis-ci.org/loadimpact/loadimpact-sdk-python.png?branch=master,develop)](https://travis-ci.org/loadimpact/loadimpact-sdk-python)

This Python SDK provides Python APIs to the Load Impact platform for running 
and managing performance tests in the cloud.

## Requirements

The Load Impact Python SDK works with Python versions 2.6, 2.7, 3.2 and 3.3.
It has one dependency, the [requests](http://www.python-requests.org/) library. 

## Installation

Install using `pip`:

```sh
pip install loadimpact
```
[![Latest PyPI Version](https://pypip.in/v/loadimpact/badge.png)](https://pypi.python.org/pypi/loadimpact) [![PyPI Downloads](https://pypip.in/d/loadimpact/badge.png)](https://pypi.python.org/pypi/loadimpact)

## Creating an API client

To create an API client instance you need your API token. You can find it on
your [loadimpact.com account page](https://loadimpact.com/account/).

You either enter your API token as an argument when creating the client:

```python
import loadimpact
client = loadimpact.ApiTokenClient(api_token='YOUR_API_TOKEN_GOES_HERE')
```

or using environment variables:

```sh
export LOADIMPACT_API_TOKEN=YOUR_API_TOKEN_GOES_HERE
```
```python
import loadimpact
client = loadimpact.ApiTokenClient()
```

## Using an API client

### List test configurations
```python
configs = client.list_test_configs()
```

### Get a specific test configuration
```python
test_config_id = 1
config = client.get_test_config(test_config_id)
```

### Create a new test configuration
```python
from loadimpact import LoadZone

config = client.create_test_config({
    'name': 'My test configuration',
    'url': 'http://example.com/',
    'config': {
        "load_schedule": [{"users": 10, "duration": 10}],
        "tracks": [{
            "clips": [{
                "user_scenario_id": 1, "percent": 100
            }],
            "loadzone": LoadZone.AMAZON_US_ASHBURN
        }]
    }
})
```

The available load zones are as follows:
```python
# Amazon load zones
LoadZone.AMAZON_US_ASHBURN
LoadZone.AMAZON_US_ASHBURN
LoadZone.AMAZON_US_PALOALTO
LoadZone.AMAZON_IE_DUBLIN
LoadZone.AMAZON_SG_SINGAPORE
LoadZone.AMAZON_JP_TOKYO
LoadZone.AMAZON_US_PORTLAND
LoadZone.AMAZON_BR_SAOPAULO
LoadZone.AMAZON_AU_SYDNEY

# Rackspace load zones
LoadZone.RACKSPACE_US_CHICAGO
LoadZone.RACKSPACE_US_DALLAS
LoadZone.RACKSPACE_UK_LONDON
LoadZone.RACKSPACE_AU_SYDNEY
```

### Update an existing test configuration
```python
config = client.get_test_config(1)
config.name = "Changed name"
config.update()
```

or

```python
config = client.get_test_config(1)
config.update({'name': "Changed name"})
```

### Delete config
```python
config = client.get_test_config(1)
config.delete()
```

Deleting data stores and user scenarios is done in the same way, calling a
delete method on the resource object.

### Run test and stream results to STDOUT
```python
from loadimpact import TestResult

test_config = client.get_test_config(1)
test = test_config.start_test()
stream = test.result_stream([
    TestResult.result_id_from_name(TestResult.LIVE_FEEDBACK),
    TestResult.result_id_from_name(TestResult.ACTIVE_USERS,
                                   load_zone_id=world_id),
    TestResult.result_id_from_name(TestResult.REQUESTS_PER_SECOND,
                                   load_zone_id=world_id),
    TestResult.result_id_from_name(TestResult.USER_LOAD_TIME,
                                   load_zone_id=world_id)])

for data in stream(poll_rate=3):
    print data[TestResult.result_id_from_name(TestResult.LIVE_FEEDBACK)]
    time.sleep(3)
```

### Create a new user scenario
```python
load_script = """
local response = http.get("http://example.com')
log.info("Load time: "..response.total_load_time.."s")
client.sleep(5)
"""
user_scenario = client.create_user_scenario({
    'name': "My user scenario",
    'load_script': load_script
})
```

### Validating a user scenario
```python
from loadimpact import UserScenarioValidation

user_scenario_id = 1
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
        for filename, line, function in result['stack_trace']:
            print('\t%s:%s in %s' % (function, line, filename))
    else:
        print('[%s]: %s' % (result['timestamp'], result['message']))
print("Validation completed with status '%s'"
      % (UserScenarioValidation.status_code_to_text(validation.status)))
```

### Uploading a data store (CSV file with parameterization data)
For more information regarding parameterized data have a look at [this
knowledgebase article](http://support.loadimpact.com/knowledgebase/articles/174258-how-do-i-use-parameterized-data-).

```python
from loadimpact import DataStore

fil_obj = open('data.csv', 'r')
data_store = client.create_data_store({
    'name': "My data store",
    'separator': 'comma',
    'delimeter': 'double'
}, file_obj)
while not data_store.has_conversion_finished():
    time.sleep(3)
print("Data store conversion completed with status '%s'"
      % (DataStore.status_code_to_text(data_store.status)))
```

### Adding a data store to a user scenario
```python
user_scenario = client.get_user_scenario(1)
data_store = client.get_data_store(1)
user_scenario.data_stores.append(data_store.id)
user_scenario.update()
```
