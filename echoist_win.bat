@echo off
:loop
echo %1
timeout 2 > NUL
goto loop
