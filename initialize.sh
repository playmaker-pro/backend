#!/bin/bash

# This script contains the commands that have to be run after database initialization
# VENV MUST BE ACTIVATED !

execute_command() {
    echo "Currently running: $*"
    "$@"
    local status=$?
    if [ $status -ne 0 ]; then
        echo "Error with $*" >&2
        exit $status
    else
        echo "Successfully executed $*"
    fi
}

# import cities
execute_command ./manage.py cities_light

# create short name for clubs and teams
execute_command ./manage.py create_short_name_for_club_and_team

# change league seniority to "Centralna Liga Juniorow"
execute_command ./manage.py change_league_seniorty

# hide predefined leagues
execute_command ./manage.py hide_predefined_leagues

# create default leagues
execute_command ./manage.py create_default_leagues

# add season 2023/2024
#TODO: This should not be hardcoded here, script should get by default current season from clubs.models.Season.define_current_season()
execute_command ./manage.py add_seasons 2023 2024