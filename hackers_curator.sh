#!/usr/bin/env bash
set -e
set -u

if [ ! -e ./dist/hackers_curator.pex ]; then
  ./build.sh
fi
export PEX_PYTHON_PATH=python3.6:python3
./dist/hackers_curator.pex "$@"
