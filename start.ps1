Push-Location -Path backend
try {
    .\venv\Scripts\Activate.ps1
    python -u -m onyo_backend *> ..\backend.log
}
finally {
    Pop-Location
}
