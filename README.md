# Load Impact Python SDK [![Build Status](https://travis-ci.org/loadimpact/loadimpact-sdk-python.png?branch=master,develop)](https://travis-ci.org/loadimpact/loadimpact-sdk-python) [![Coverage Status](https://coveralls.io/repos/loadimpact/loadimpact-sdk-python/badge.svg?branch=develop&service=github)](https://coveralls.io/github/loadimpact/loadimpact-sdk-python?branch=develop)

This Python SDK provides Python APIs to the Load Impact platform for running 
and managing performance tests in the cloud.

** Please note that this version of the SDK is in BETA and we are still working on being completely compatible with the version 3 Load Impact API. **

## Requirements

The Load Impact Python SDK works with Python versions 2.6, 2.7, 3.2 and 3.3.
It has one dependency, the [requests](http://www.python-requests.org/) library. 

## Installation

Install using `pip`:

```sh
pip install loadimpact-v3
```
[![PyPI](https://img.shields.io/pypi/v/loadimpact.svg)]() [![PyPI](https://img.shields.io/pypi/dm/loadimpact.svg)]()

## Creating an API client

To create an API client instance you need your API token. You can find it on
your [loadimpact.com account page](https://loadimpact.com/account/).

You either enter your API token as an argument when creating the client:

```python
import loadimpact3
client = loadimpact3.ApiTokenClient(api_token='YOUR_API_TOKEN_GOES_HERE')
```

or using environment variables:

```sh
export LOADIMPACT_API_TOKEN=YOUR_API_TOKEN_GOES_HERE
```
```python
import loadimpact3
client = loadimpact3.ApiTokenClient()
```

## Using an API client


### Create a new user scenario
```python
load_script = """
local response = http.get("http://example.com')
log.info("Load time: "..response.total_load_time.."s")
client.sleep(5)
"""
user_scenario = client.create_user_scenario({
    'name': "My user scenario",
    'load_script': load_script,
    'project_id': 1
})
```

### Validating a user scenario
```python
from loadimpact3 import UserScenarioValidation
from time import sleep

scenario_id = 1
user_scenario = client.get_user_scenario(scenario_id)
validation = user_scenario.validate()
poll_rate = 10

while not validation.is_done():
    validation = client.get_user_scenario_validation(validation.id)
    sleep(poll_rate)

validation_results = client.get_user_scenario_validation_result(validation.id)

for result in validation_results:
    print("[{0}] {1}".format(result.timestamp, result.message))

print("Validation completed with status: {0}".format(validation.status_text))
```

### Uploading a data store (CSV file with parameterization data)
For more information regarding parameterized data have a look at [this
knowledgebase article](http://support.loadimpact.com/knowledgebase/articles/174258-how-do-i-use-parameterized-data-).

```python
from loadimpact3 import DataStore
from time import sleep

file_obj = open('data.csv', 'r')
data_store = client.create_data_store({
    'name': "My data store",
    'separator': 'comma',
    'delimiter': 'double'
}, file_obj)
while not data_store.has_conversion_finished():
    sleep(3)
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
