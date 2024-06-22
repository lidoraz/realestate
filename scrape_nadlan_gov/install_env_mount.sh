#!/bin/bash

# Check if the virtual environment exists
if [ ! -d "venv_nadlan_gov" ]; then
    # Create the virtual environment
    python3 -m venv venv_nadlan_gov
fi

# Activate the virtual environment
source venv_nadlan_gov/bin/activate

