#!/bin/bash

# Creates empty .env file as template

echo "SCRAPPER__AUTH__USERNAME=
SCRAPPER__AUTH__PASSWORD=
SCRAPPER__BASE_URL=" > "$(dirname $0)"/../../../.env