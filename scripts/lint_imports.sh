#!/bin/bash
set -eu
errors=0
# make sure not importing from anna_agent directly
git --no-pager grep '^from anna_agent\.' . && errors=$((errors+1))
if [ "$errors" -gt 0 ]; then
    exit 1
else
    exit 0
fi
