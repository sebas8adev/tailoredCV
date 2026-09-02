param (
    [string]$profilesJsonPath,
    [string]$sessionJsonPath
)

# Read the JSON files
$profilesData = Get-Content -Raw -Path $profilesJsonPath | ConvertFrom-Json
$sessionData = Get-Content -Raw -Path $sessionJsonPath | ConvertFrom-Json

$allProfiles = $profilesData.profiles
$lastProfileId = $sessionData.last_used_profile_id

# Filter for enabled profiles
$enabledProfiles = @($allProfiles | Where-Object { $_.enabled -eq $true })

if ($enabledProfiles.Count -eq 0) {
    Write-Error "No enabled profiles found in '$profilesJsonPath'. Please enable at least one profile."
    exit 1
}

# Find the index of the last used profile within the enabled list
$lastIndex = -1
for ($i = 0; $i -lt $enabledProfiles.Count; $i++) {
    if ($enabledProfiles[$i].id -eq $lastProfileId) {
        $lastIndex = $i
        break
    }
}

# Determine the next profile index from the enabled list
$nextIndex = ($lastIndex + 1) % $enabledProfiles.Count
$nextProfile = $enabledProfiles[$nextIndex]

# Output the next profile's data in a format the batch script can easily parse
Write-Output "$($nextProfile.id);$($nextProfile.script);$($nextProfile.port);$($nextProfile.connect_url)"