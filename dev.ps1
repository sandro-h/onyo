Push-Location -Path backend
try {
    Start-Process -FilePath "venv\scripts\jurigged" -ArgumentList "-m onyo_backend" -passthru -nonewwindow -wait
}
finally {
    Pop-Location
}
