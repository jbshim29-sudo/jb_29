@echo off
REM KOSPI 200 저평가 스크리너 일일 실행 배치
REM 작업 스케줄러가 이 파일을 호출합니다.
setlocal
set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"
set "PYTHONIOENCODING=utf-8"

if not exist "%PY%" (
  echo [ERROR] venv Python not found: %PY%
  exit /b 1
)

"%PY%" "%ROOT%src\main.py"
exit /b %errorlevel%
