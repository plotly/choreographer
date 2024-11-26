#!/usr/bin/env bash
set -e
wget $(curl -s https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json |
jq -r ".versions | .[-1] | .downloads.chrome | .[] | select(.platform == \"${1}\").url")
unzip chrome*
export BROWSER_PATH="$(realpath "chrome-${1}")/chrome"
