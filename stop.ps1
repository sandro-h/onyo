taskkill /f /pid $(get-content -path backend.pid)
remove-item -path backend.pid