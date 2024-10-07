# Testing

## Running:

### Process Control Tests

- Verbose: `pytest -W error -n auto -vvv -rA --capture=tee-sys tests/test_process.py`
- Quiet:`pytest -W error -n auto -v -rFe --capture=fd tests/test_process.py`

### Browser Interaction Tests

- Verbose: `pytest --debug -n auto -W error -vvv -rA --capture=tee-sys --ignore=tests/test_process.py`
- Quiet :`pytest -W error -n auto -v -rFe --capture=fd --ignore=tests/test_process.py`

You can also add "--no-headless" to these if you want to see the browser pop up

## Writing Tests:

Put async and sync tests in different files. Add `_sync.py` to synchronous tests.

If doing process tests, maybe use the same decorators and fixtures in the `test_process.py` file.

If doing browser interaction tests, use `test_placeholder.py` as the minimum template.
