@echo off
python "%~dp0verify_release.py" %*
exit /b %errorlevel%
