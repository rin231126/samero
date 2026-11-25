"""Split non-interactive HTTPS staging from the existing attended restart test.
Production code, URL, SHA-256, zone metadata, and OS launch policy are unchanged.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1]).resolve()/'tests/windows-update-smoke.ps1'
s=p.read_text(encoding='utf-8')
def edit(old,new):
    global s
    assert s.count(old)==1,(old,s.count(old))
    s=s.replace(old,new)
edit('param([Parameter(Mandatory=$true)][string]$Exe)',
     'param([Parameter(Mandatory=$true)][string]$Exe,[switch]$StageOnly)')
edit("  $r=Api 'public-update-restart' @{update=[string]$meta.sequence;confirmed=$true}",'''  if($StageOnly) {
    $state=Api 'state'
    if(@($state.projects | Where-Object {$_.id -eq $project.id -and $_.goal -eq 'Keep this project unchanged'}).Count -ne 1){throw 'Project state not preserved'}
    if((Get-FileHash -LiteralPath $Exe -Algorithm SHA256).Hash -ne $original){throw 'Old executable changed'}
    $null=Api 'exit'
    if(!$child.WaitForExit(15000) -or $child.ExitCode -ne 0){throw 'Old Manager did not exit normally after staging'}
    Write-Output 'PASS: HTTPS download, SHA-256, Internet-zone metadata, rejection without approval, preserved state and normal exit.'
    Write-Output 'NOT VERIFIED: interactive Internet-zone launch; use the full Windows test on an attended desktop.'
    return
  }
  $r=Api 'public-update-restart' @{update=[string]$meta.sequence;confirmed=$true}''')
p.write_text(s,encoding='utf-8')
print('PASS: staging-only mode added; original interactive test retained')
