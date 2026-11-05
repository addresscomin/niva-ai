@echo off
title Push NIVA AI to GitHub
echo ========================================================
echo  Pushing NIVA AI to https://github.com/addresscomin/niva-ai.git
echo ========================================================
cd /d "%~dp0"
"C:\Users\STUDENT\.bin\git\cmd\git.exe" push -u origin main
echo ========================================================
echo  Done! Your repository is updated on GitHub.
echo ========================================================
pause
