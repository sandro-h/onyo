Push-Location -Path backend
try {
    Start-Process -FilePath "venv\scripts\python" -ArgumentList "-m cli $args" -nonewwindow -wait
}
finally {
    Pop-Location
}
