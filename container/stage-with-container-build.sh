#!/bin/bash

set -xue

cd /buildroot/pf9-mors/container && make --max-load=$(nproc) stage-with-py-build-container
