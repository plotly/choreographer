# Exit on error

$ErrorActionPreference = "Stop"

# Get the platform (like 'win', 'mac', 'linux')
$platform = $args[0]

# Fetch the known good versions with download URLs
$response = Invoke-RestMethod -Uri "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"

# Filter for the appropriate download URL based on the platform
$downloadUrl = $response.versions[-1].downloads.chrome | Where-Object { $_.platform -eq $platform } | Select-Object -ExpandProperty url

# Download the zip file
Invoke-WebRequest -Uri $downloadUrl -OutFile "chrome.zip"

# Unzip the downloaded file
Expand-Archive -Path "chrome.zip" -DestinationPath "."

# Set the browser path
$browserPath = (Get-ChildItem -Directory | Where-Object { $_.Name -like "chrome-*" }).FullName + "\chrome"

# Export the browser path as an environment variable (for the current session)
$env:BROWSER_PATH = $browserPath
[Environment]::SetEnvironmentVariable("BROWSER_PATH", $browserPath, "Machine")

Write-Host "BROWSER_PATH set to $env:BROWSER_PATH"
