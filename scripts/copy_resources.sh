#!/usr/bin/env bash

#####################################################################################
# This script is intended to copy resource files from the automated-invoice-testing #
# repo into the FishbowlInvoiceTool repo for use during testing. The application    #
# does not contain resource files that contain private company data since it is a   #
# public repository. This helper script assumes that the FishbowlInvoiceTool        #
# application and the automated-invoice-testing repository have both been cloned    #
# into the same parent directory, and automates the file copy process.              #
#                                                                                   #
# The required project structure is as follows:                                     #
# project_root/                                                                     #
# ├── automated-invoice-testing/                                                    #
# │   └── resources/                                                                #
# └── FishbowlInvoiceTool/                                                          #
#   └── scripts/copy_resources.sh                                                   #
#                                                                                   #
# Note: This script will not work unless the above structure is maintained, meaning #
# that both repositories must be cloned into the same parent directory.             #
#                                                                                   #
# Usage: ./copy_resources.sh                                                        #
#####################################################################################

# Fail safely on errors and undefined variables, and ensure pipelines fully succeed
set -euo pipefail

# Get the location of this script, and use it to derive the project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Use the derived project directory to set source and destination paths
SRC="$ROOT_DIR/automated-invoice-testing/resources"
DST="$ROOT_DIR/FishbowlInvoiceTool"

# Ensure that the source and destination directories exist
if [[ ! -d "$SRC" ]]; then
  echo "Source directory does not exist: $SRC"
  exit 1
fi
if [[ ! -d "$DST" ]]; then
  echo "Destination directory does not exist: $DST"
  exit 1
fi

# Copy the resources over to the application folder
cp -a "$SRC"/. "$DST"/