# Adjust Report API Function

| Branch    | Status |
| -------- | ------- |
| Main  | [![Fake Adjust Serverless CI CD on Main](https://github.com/Gasta88/fake_adjust_serverless_service/actions/workflows/cicd.yaml/badge.svg?branch=main)](https://github.com/Gasta88/fake_adjust_serverless_service/actions/workflows/cicd.yaml)    |
| Developement | [![Fake Adjust Serverless CI CD on Development](https://github.com/Gasta88/fake_adjust_serverless_service/actions/workflows/cicd.yaml/badge.svg?branch=development)](https://github.com/Gasta88/fake_adjust_serverless_service/actions/workflows/cicd.yaml)     |




## Purpose/Goals

The *Fake Adjust Serverless Service* is a service used to query the Fake Adjust REST API and retrieve the attribution reporting data.

The project will collect Fake Adjust Report API data at different intervals:

- every 2h
- every week
- every month

This is done because Fake Adust simulates a data aggregator itself and the velocity of different sources is quite different between each other. Without any warning, some records could be updated and it is necessary to have the most recent view of the data at hand.


The retrieved data is later recorded on BigQuery and sanitized via ELT process.

## Infrastructure design

![infra design](docs/adjust_serverless_service.png "Infrastructure design")

## Data workflow

- At a fixed interval, a scheduler send a HTTP call to the *orchestrator* Cloud Function.
- According to the schedule, it builds the right type and the right amount of URLs (1, 7 or 30).
- In a "fire-and-forget" fashion, it will send each URL to the *executor* Cloud Function.
- Each URL will create an isolated instance of the *executor* Cloud Function.
- Destination BigQuery dataset and tables are fetched and two consecutive HTTP POST are made to Adjust Report API:
    - one for *ios* platform
    - one for *android* platform
- The returned data is manipulated in Pandas according to the BigQuery table specifics.
- The operation day and timestamp are recorded inside the dedicated lookup table to build the materialized view via Dataform at a later stage (out of this repository scope).

## Data observability

To be defined with Cloud Logging...


## Testing the pipeline

At the current state, the project is tested via CI/CD pipeline in GitHub. Tests are allocated in _test/_ folder.

Two types of tests are run:

- Unit tests
- End-to-end tests

### Unit testing:

The unit testing of the project occurs at two levels:

- Terraform plan output.
- Python scripts.

These steps are run in parallel at every **push** event on the remote.
