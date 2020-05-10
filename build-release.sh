#!/usr/bin/env bash

set -ex

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
TEMP_DIR=`mktemp -d`
CWD=`pwd`

cd $TEMP_DIR
cp -r "$ROOT_DIR/custom_components/goldair_climate" .
cd goldair_climate
rm -rf __pycache__ */__pycache__
zip -r homeassistant-goldair-climate * .translations
cp homeassistant-goldair-climate.zip "$CWD"
cd "$CWD"
rm -rf $TEMP_DIR