# Ubuntu Security Workarounds

## Restrictions

Ubuntu has special rules around programs installed outside of its package
manager.

### Sandbox

#### Root

Because sandboxing depends on running subprocesses in underpriviledged modes
using OS-level APIs, and if you run as root, all your root process have
root-privileges, sandboxing wont work if run as root.

#### Ubuntu

Ubuntu doesn't let non-package-manager installed apps run w/ sandboxing tools.

### Temporary Files

Ubuntu doesn't let apps share temporary files.

## Impacts

Even though we recommend testing with our "known-later-version", we have to, in
order to test sandbox, use the package manager of ubuntu. So sometimes there are
failures.
