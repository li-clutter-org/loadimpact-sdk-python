# Load Impact Python SDK #

TODO

# Usage #
import loadimpactsdk
import time

print(loadimpactsdk.__version__)

# Create API client
api_token = 'YOUR_API_TOKEN_GOES_HERE'
client = loadimpactsdk.ApiTokenClient(api_token)

# Get config
config = loadimpactsdk.TestConfig.get(client, 1)
print(config.name)
print(config.config)
print(config.user_scenarios)

# Create config
config = loadimpactsdk.TestConfig(name="My config")
config.add_ramp_step(50, 10)
user_scenario = loadimpactsdk.UserScenario.get(1)
config.add_user_scenario(user_scenario, load_zone_id=LoadZone.name_to_id(LoadZone.AMAZON_US_ASHBURN), traffic_percent=100)
config.create(client)

# Update config
config = loadimpactsdk.TestConfig.get(client, 1)
config.name = 'My test configuration 2'
config.add_ramp_step(1000, 5, index=None) # index=None is the default and means last
config.update(client)

# Delete config
config = loadimpactsdk.TestConfig.get(client, 1)
config.delete(client)

# Start test based on config
test = loadimpactsdk.TestConfig.start_test(client)
stream = test.result_stream([
    TestResult.result_id_from_name(TestResult.USER_LOAD_TIME,
                                   load_zone_id=world_id),
    TestResult.result_id_from_name(TestResult.ACTIVE_USERS,
                                   load_zone_id=world_id)])
while not test.is_done():
  stream.poll(client)
  print(stream.last())
  time.sleep(3)

# Get results from old test
test = loadimpactsdk.Test.get(1)
stream = test.result_stream([
    TestResult.result_id_from_name(TestResult.USER_LOAD_TIME,
                                   load_zone_id=world_id),
    TestResult.result_id_from_name(TestResult.ACTIVE_USERS,
                                   load_zone_id=world_id)])
while not stream.is_done():
  stream.poll(client)
  print(stream.last())
  time.sleep(3)
