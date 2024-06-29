#!/bin/bash

# Check if the virtual environment exists
if [ ! -d ".venv_nadlan_gov_requests2.24" ]; then
    # Create the virtual environment
    python3 -m venv .venv_nadlan_gov_requests2.24
fi
# ALREADY HAVE AN ENVIRONMENT just need to pip install it.
# Activate the virtual environment
source .venv_nadlan_gov_requests2.24/bin/activate

