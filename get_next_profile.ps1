param (
    [string]$profilesJsonPath,
    [string]$sessionJsonPath
)

# Read the JSON files
$profilesData = Get-Content -Raw -Path $profilesJsonPath | ConvertFrom-Json
$sessionData = if (Test-Path -Path $sessionJsonPath) { Get-Content -Raw -Path $sessionJsonPath | ConvertFrom-Json } else { $null }

$allProfiles = $profilesData.profiles
$lastProfileId = if ($sessionData) { $sessionData.last_used_profile_id } else { $null }

# Filter for enabled profiles
$enabledProfiles = @($allProfiles | Where-Object { $_.enabled -eq $true })

if ($enabledProfiles.Count -eq 0) {
    Write-Error "No enabled profiles found in '$profilesJsonPath'. Please enable at least one profile."
    exit 1
}

# Filter out the last used profile to avoid back-to-back repeats if multiple profiles exist
$candidates = @($enabledProfiles | Where-Object { $_.id -ne $lastProfileId })
if ($candidates.Count -eq 0) {
    $candidates = $enabledProfiles
}

# Select a random profile from candidates
$randomIndex = Get-Random -Minimum 0 -Maximum $candidates.Count
$nextProfile = $candidates[$randomIndex]

# Output the next profile's data in a format the batch script can easily parse
Write-Output "$($nextProfile.id);$($nextProfile.script);$($nextProfile.port);$($nextProfile.connect_url)"