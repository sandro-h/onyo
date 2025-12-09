Push-Location -Path backend
try {
    $env:NO_COLOR="true"
    $p = Start-Process -FilePath "venv\scripts\python" -ArgumentList "-u -m onyo_backend" -passthru -nonewwindow -RedirectStandardOutput ..\backend.log -RedirectStandardError ..\backend_err.log
    echo $p.id > ..\backend.pid
}
finally {
    Pop-Location
}
