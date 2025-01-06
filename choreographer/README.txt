These READMEs (in directories) are development notes, think of them as additions
to the package-level docstrings (the one at the top of each __init__.py).


The browsers are the main entrypoint for the user. They:

1. Manage the actual browser process (start/stop/kill).
2. Integrate the different resources: (see _channels/, _brokers/, _browsers/).
3. Is a list of `Tab`s, `Session`s, and `Target`s.
4. Provides a basic API.
