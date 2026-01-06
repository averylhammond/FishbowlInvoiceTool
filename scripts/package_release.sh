#!/usr/bin/env bash
#####################################################################################
# This script is intended to take the FishbowlInvoiceTool and package it as a       #
# release executable using PyInstaller. It assumes that the FishbowlInvoiceTool     #
# repository has been cloned into a directory alongside the automated-invoice-      #
# testing repository, which contains resource files that are packaged into the      #
# release. This helper script automates the packaging process for speed and also    #
# automated testing purposes. It can be ran in or out of the python virtual         #
# environment, as it will create it's own if needed.                                #
#                                                                                   #
# The required project structure is as follows:                                     #
# project_root/                                                                     #
# ├── automated-invoice-testing/                                                    #
# │   └── resources/                                                                #
# └── FishbowlInvoiceTool/                                                          #
#   └── scripts/package_release.sh                                                  #
#####################################################################################

# Fail safely on errors and undefined variables, and ensure pipelines fully succeed
set -euo pipefail

# Run a git clean to clean up the project tree before packaging
git clean -fdxf

# Exit if no argument provided
if [[ $# -lt 1 ]]; then
    echo "Usage: ./package_release.sh <populate_invoices>, where <populate_invoices> is 'true' or 'false'"
    echo "Example: ./package_release.sh true will copy the Invoices/ folder from the testing framework into the release"
    echo "Use this if you want the release to include sample invoices for testing purposes."
    exit 1
fi

# Get the location of this script, and use it to derive the project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Use the derived parent directory to set the resources and project paths
RESOURCES_DIR="$ROOT_DIR/automated-invoice-testing/resources"
PROJECT_DIR="$ROOT_DIR/FishbowlInvoiceTool"

# Ensure that the source and destination directories exist
if [[ ! -d "$RESOURCES_DIR" ]]; then
  echo "Resources directory does not exist in testing framework: $RESOURCES_DIR"
  echo "Make sure to clone the latest version of the automated-invoice-testing"
  echo "repo into the same parent directory as FishbowlInvoiceTool."
  exit 1
fi
if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "Application directory does not exist: $PROJECT_DIR"
  exit 1
fi

# Check virtual environment
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    echo "Already inside of a virtual environment: $VIRTUAL_ENV"
else
    # If not in a virtual environment, create one
    echo "Creating a fresh virtual environment for packaging..."
    python -m venv "$PROJECT_DIR/venv"
    
    # Determine the OS type, only linux and Windows are supported
    # Activating the venv requires different paths on Windows/Linux
    # Exit on unknown OS
    OS_TYPE="$(uname -s 2>/dev/null || echo unknown)"
    if [[ "$OS_TYPE" == "Linux" ]]; then
        source "$PROJECT_DIR/venv/bin/activate"
    elif [[ "$OS_TYPE" == "MINGW"* || "$OS_TYPE" == "CYGWIN"* || "$OS_TYPE" == "MSYS"* ]]; then
        source "$PROJECT_DIR/venv/Scripts/activate"
    else
        echo "Unknown OS: ${OS_TYPE:-}... Exiting"
        exit 1
    fi

    echo "Activated virtual environment: $VIRTUAL_ENV"
fi

# Make sure that all project dependencies are installed in the virtual environment
pip install -r "$PROJECT_DIR/requirements/release.txt"

# Install PyInstaller
pip install PyInstaller

# Use PyInstaller to package the application into an executable
echo "Packaging the application into a release executable..."
python -OO -m PyInstaller --onefile --noconsole --name AutoInvoiceProc main.py

# Set up the desired release project structure
RELEASE_DIR="$PROJECT_DIR/release/FishbowlInvoiceTool"
CONFIGS_DIR="$RELEASE_DIR/Configs"
INVOICES_DIR="$RELEASE_DIR/Invoices"

mkdir -p "$RELEASE_DIR"
mkdir -p "$CONFIGS_DIR"
mkdir -p "$INVOICES_DIR"

# Move the necessary existing files over to the release directory, including
# the executable created by PyInstaller, and the ReadMe
mv "$PROJECT_DIR/dist/AutoInvoiceProc.exe" "$RELEASE_DIR/"
cp "$PROJECT_DIR/ReadMe.txt" "$RELEASE_DIR/"  # Note that this is the customer ReadMe.txt, not the GitHub README.md

# Exit virtual environment on script exit
echo "Deactivating virtual environment: $VIRTUAL_ENV"
deactivate