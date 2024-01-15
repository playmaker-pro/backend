@echo off

REM Creates empty .env file as template

(
    echo SCRAPPER__AUTH__USERNAME=
    echo SCRAPPER__AUTH__PASSWORD=
    echo SCRAPPER__BASE_URL=http://localhost:8080/
) > ..\..\..\.env
