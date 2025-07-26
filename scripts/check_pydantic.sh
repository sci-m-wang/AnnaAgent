#!/bin/bash
# This script searches for pydantic imports in tracked files
# Usage: ./scripts/check_pydantic.sh /path/to/repository
if [ $# -ne 1 ]; then
  echo "Usage: $0 /path/to/repository"
  exit 1
fi
repo="$1"
result=$(git -C "$repo" grep -E '^import pydantic|^from pydantic')
if [ -n "$result" ]; then
  echo "ERROR: The following lines need to be updated:"
  echo "$result"
  echo "Please replace the code with an import from langchain_core.pydantic_v1."
  echo "For example, replace 'from pydantic import BaseModel'"
  echo "with 'from langchain_core.pydantic_v1 import BaseModel'"
  exit 1
fi
