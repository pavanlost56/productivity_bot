# -----------------------------------------
# Reset Google Calendar OAuth credentials
# (Only deletes token.json, never client_secret.json)
# -----------------------------------------

Write-Host "➡️ Resetting Google Calendar credentials..."

# Path to your project root
$ProjectRoot = "D:\productivity_bot"

# Files
$ClientSecret = Join-Path $ProjectRoot "client_secret.json"
$TokenFile    = Join-Path $ProjectRoot "token.json"

# 1) Verify client_secret.json exists
if (Test-Path $ClientSecret) {
    Write-Host "✅ Found client_secret.json (kept safe)"
} else {
    Write-Host "❌ ERROR: client_secret.json is missing in $ProjectRoot"
    Write-Host "Download it from Google Cloud Console → OAuth Client ID → Desktop app."
    exit 1
}

# 2) Delete only token.json (forces new login)
if (Test-Path $TokenFile) {
    Remove-Item $TokenFile -Force
    Write-Host "🗑️ Deleted old token.json (will be regenerated after login)"
} else {
    Write-Host "ℹ️ No token.json found (first-time setup)"
}

# 3) Start the bot again
Write-Host "🚀 Starting bot... A browser window will open for Google login."
& "$ProjectRoot\.venv\Scripts\python.exe" -m productivity_bot.main
