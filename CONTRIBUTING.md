# Contributing

Run `python -m pip install -e '.[dev]'` and `python -m pytest -q` before a pull
request. Replay fixtures are synthetic; never add customer data, credentials,
or terminal labels to deployable traces. Schema changes require a versioned
contract test and documentation update.
