$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\reset_chrome_debug_data.ps1')
$sandbox=Join-Path $PSScriptRoot ('..\.validation\debug-profile-'+[guid]::NewGuid().ToString('N'))
$sandbox=[IO.Path]::GetFullPath($sandbox)
New-Item -ItemType Directory -Path $sandbox -Force | Out-Null
$script:processes=@()
function Get-CimInstance { param($ClassName,$Filter,$ErrorAction) return $script:processes }
function Assert($Condition,[string]$Message) { if (-not $Condition) { throw $Message } }
function Put([string]$Path) { New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($Path)) -Force | Out-Null; [IO.File]::WriteAllText($Path,'fixture') }
function Reject([scriptblock]$Action,[string]$Pattern) { $caught=$false;try{& $Action | Out-Null}catch{$caught=$true;Assert ($_.Exception.Message -match $Pattern) $_.Exception.Message};Assert $caught 'Expected rejection' }
$profile=Get-DebugProfilePath $sandbox
$outside=Join-Path $sandbox 'Google\Chrome\User Data\Default\Network\Cookies'
Put $outside
try {
    Reject {Get-DebugProfilePath '..\wrong'} 'absoluter'
    Assert ($profile -eq (Join-Path $sandbox 'BaccaratCounterChrome')) 'Dedicated path'
    Reset-DebugSiteData $sandbox | Out-Null
    Assert (-not (Test-Path -LiteralPath $profile)) 'Absent profile is not created or redirected'
    Write-Output 'PASS fixed profile scope and first launch'

    $delete=@('Default\Network\Cookies','Default\Network\Cookies-wal','Default\Network\Cookies-shm','Default\Cookies-journal',
        'Default\Cache\Cache_Data\entry','Default\Code Cache\js\entry','Default\Service Worker\CacheStorage\entry',
        'Default\Local Storage\leveldb\entry','Default\Session Storage\entry','Default\IndexedDB\entry',
        'Default\Storage\entry','Default\WebStorage\entry','Default\File System\entry','Default\Shared Dictionary\entry',
        'Default\GPUCache\entry','ShaderCache\entry','Profile 1\Network\Cookies','Guest Profile\Cache\entry')
    $keep=@('Local State','Default\Bookmarks','Default\Login Data','Default\Preferences','Default\Secure Preferences')
    foreach($p in $delete+$keep){Put (Join-Path $profile $p)}
    Reset-DebugSiteData $sandbox | Out-Null
    foreach($p in $delete){Assert (-not(Test-Path -LiteralPath (Join-Path $profile $p))) ('Retained '+$p)}
    foreach($p in $keep){Assert ([IO.File]::ReadAllText((Join-Path $profile $p)) -eq 'fixture') ('Modified '+$p)}
    Assert ([IO.File]::ReadAllText($outside) -eq 'fixture') 'Normal Chrome profile touched'
    Write-Output 'PASS all cookie sidecars, caches and site storage removed; credentials/preferences/bookmarks/normal Chrome preserved'

    Put (Join-Path $profile 'Default\Network\Cookies')
    $script:processes=@([pscustomobject]@{CommandLine='chrome.exe --user-data-dir="'+$profile+'" --remote-debugging-port=9222'})
    Reject {Reset-DebugSiteData $sandbox} 'noch offen'
    Assert (Test-Path -LiteralPath (Join-Path $profile 'Default\Network\Cookies')) 'Active browser data deleted'
    Reset-DebugSiteData $sandbox 'simulator' | Out-Null
    Assert (Test-Path -LiteralPath (Join-Path $profile 'Default\Network\Cookies')) 'Existing simulator tab reset session'
    $script:processes=@([pscustomobject]@{CommandLine='chrome.exe --user-data-dir="'+$profile+'-other"'})
    Reset-DebugSiteData $sandbox 'simulator' | Out-Null
    Assert (-not(Test-Path -LiteralPath (Join-Path $profile 'Default\Network\Cookies'))) 'Cold simulator launch was not cleaned'
    Write-Output 'PASS active browser blocks reset; simulator reuse preserved; separate profile cannot spoof running match'

    $cookie=Join-Path $profile 'Default\Network\Cookies';Put $cookie
    $lock=[IO.File]::Open($cookie,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    try {Reject {Reset-DebugSiteData $sandbox} 'verwendet|used|Zugriff|access|process|Prozess'} finally {$lock.Dispose()}
    Assert (Test-Path -LiteralPath $cookie) 'Locked data silently ignored'
    Reset-DebugSiteData $sandbox | Out-Null
    Write-Output 'PASS locked cookies abort start instead of reporting clean'

    $cache=Join-Path $profile 'Default\Cache';$junction=Join-Path $cache 'outside'
    New-Item -ItemType Directory -Path $cache -Force | Out-Null
    New-Item -ItemType Junction -Path $junction -Value ([IO.Path]::GetDirectoryName($outside)) | Out-Null
    try {Reject {Reset-DebugSiteData $sandbox} 'Verknuepfung';Assert (Test-Path -LiteralPath $outside) 'Junction escaped scope'}
    finally {[IO.Directory]::Delete($junction)}
    Write-Output 'PASS nested junction rejected before any deletion'
    $bat=Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot '..\start_chrome_debug.bat')
    Assert ($bat.IndexOf('reset_chrome_debug_data.ps1') -lt $bat.IndexOf('start "" "%CHROME%"')) 'Cleanup follows launch'
    Assert ($bat -match '(?s)reset_chrome_debug_data.ps1.*if errorlevel 1.*exit /b 1.*start ""') 'Cleanup failure does not block start'
    Write-Output 'PASS BAT checks cleanup result before launching Chrome'
} finally {
    Assert ($sandbox.StartsWith([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\.validation'))+'\')) 'Invalid test cleanup scope'
    Remove-Item -LiteralPath $sandbox -Recurse -Force
}
