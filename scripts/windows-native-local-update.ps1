param([Parameter(Mandatory=$true)][string]$Exe,[Parameter(Mandatory=$true)][string]$Fixture)
$ErrorActionPreference='Stop'
$Exe=(Resolve-Path -LiteralPath $Exe).Path; $Fixture=(Resolve-Path -LiteralPath $Fixture).Path
$root=Join-Path ([IO.Path]::GetTempPath()) ('SAMERO Local QA '+[guid]::NewGuid())
$storage=Join-Path $root 'data'; $workspace=Join-Path $root 'workspace'
$null=New-Item -ItemType Directory -Path $storage,$workspace
$original=(Get-FileHash -LiteralPath $Exe -Algorithm SHA256).Hash
$candidate=Join-Path $storage 'SAMERO-update-0123456789abcdef0123456789abcdef.exe'
$child=$null; $origin=$null; $headers=$null
function Api([string]$Action,[hashtable]$Body=@{}) {
  Invoke-RestMethod -Uri "$origin/api/$Action" -Method Post -Headers $headers -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $Body -Depth 8 -Compress))) -TimeoutSec 20
}
function Connect([string]$Previous='') {
  $file=Join-Path $storage 'ui.url'
  for($i=0;$i -lt 200;$i++) {
    if(Test-Path -LiteralPath $file) {
      $url=[IO.File]::ReadAllText($file)
      if($url -ne $Previous -and $url -match '^http://127\.0\.0\.1:[0-9]+/#([0-9a-f]{32})$') {
        $script:origin,$token=$url -split '/#';$script:headers=@{Origin=$origin;'X-Samero-Key'=$token};return $url
      }
    }
    Start-Sleep -Milliseconds 100
  }
  throw 'No new Manager lease'
}
function MustReject([hashtable]$Body) {
  try { $null=Api 'public-update-restart' $Body; throw 'Unexpected success' } catch {
    if(!$_.Exception.Response -or [int]$_.Exception.Response.StatusCode -ne 409) {throw}
  }
}
try {
  # Locally built fixture only. Never remove zone metadata.
  if(Get-Item -LiteralPath $Fixture -Stream Zone.Identifier -ErrorAction SilentlyContinue){throw 'Fixture has Internet-zone metadata; local-only test refused'}
  Copy-Item -LiteralPath $Fixture -Destination $candidate
  if(Get-Item -LiteralPath $candidate -Stream Zone.Identifier -ErrorAction SilentlyContinue){throw 'Local candidate has Internet-zone metadata; test refused'}
  $digest=(Get-FileHash -LiteralPath $Fixture -Algorithm SHA256).Hash.ToLowerInvariant()
  if((Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant() -ne $digest){throw 'Fixture digest mismatch'}
  @{sha256=$digest;bytes=(Get-Item -LiteralPath $candidate).Length} | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $storage 'native-local-fixture.json') -Encoding utf8NoBOM
  $child=Start-Process -FilePath $Exe -ArgumentList @('--headless','--data-dir',('"'+$storage+'"')) -PassThru
  $oldUrl=Connect
  $oldProof=[IO.File]::ReadAllText((Join-Path $storage 'ui.version'))
  $project=Api 'project-save' @{name='Local update QA';path=$workspace;goal='Keep this project unchanged'}
  MustReject @{update='2147483647'};MustReject @{update='1';confirmed=$true}
  $r=Api 'public-update-restart' @{update='2147483647';confirmed=$true}
  if($r.status -ne 'restarting'){throw 'Restart not accepted'}
  if(!$child.WaitForExit(30000) -or $child.ExitCode -ne 0){
    $phase=Join-Path $storage 'update-launch-phase.txt';if(Test-Path -LiteralPath $phase){Write-Output ([IO.File]::ReadAllText($phase))}
    throw 'Old test process failed to exit'
  }
  $null=Connect $oldUrl
  $proof=[IO.File]::ReadAllText((Join-Path $storage 'ui.version'))
  if(($proof -split [char]10)[1] -eq ($oldProof -split [char]10)[1]){throw 'New source build identity not observed'}
  $state=Api 'state'
  if(@($state.projects | Where-Object {$_.id -eq $project.id -and $_.goal -eq 'Keep this project unchanged'}).Count -ne 1){throw 'Project state not preserved'}
  $running=@(Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -eq $candidate})
  if($running.Count -ne 1){throw 'Exact new executable process not observed'}
  if((Get-FileHash -LiteralPath $Exe -Algorithm SHA256).Hash -ne $original){throw 'Old executable changed'}
  if((Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant() -ne $digest){throw 'Candidate changed'}
  $null=Api 'exit'
  Write-Output 'PASS: native local-only verified candidate restart, approval rejection, exact process/build identity and preserved data. Internet-zone interactive launch is a separate test.'
} finally {
  if($origin -and $headers){try {$null=Api 'exit'} catch {}}
  if($child -and !$child.HasExited){Stop-Process -Id $child.Id -ErrorAction SilentlyContinue}
  Start-Sleep -Seconds 1
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
