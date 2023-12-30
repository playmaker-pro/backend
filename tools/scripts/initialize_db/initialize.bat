@echo off

REM This script contains the commands that have to be run after database initialization
REM VENV MUST BE ACTIVATED !

SETLOCAL EnableDelayedExpansion

:execute_command
echo Currently running: %*
%*
set status=%errorlevel%
if !status! neq 0 (
    echo Error with %* >&2
    exit /b !status!
) else (
    echo Successfully executed %*
)

REM import cities
call :execute_command python manage.py cities_light

REM create short name for clubs and teams
call :execute_command python manage.py create_short_name_for_club_and_team

REM change league seniority to "Centralna Liga Juniorow"
call :execute_command python manage.py change_league_seniorty

REM hide predefined leagues
call :execute_command python manage.py hide_predefined_leagues

REM add season 2023/2024
REM TODO: This should not be hardcoded here, script should get by default current season from clubs.models.Season.define_current_season()
call :execute_command python manage.py add_seasons 2023 2024

EXIT /B 0
