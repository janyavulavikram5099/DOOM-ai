param(
    [string]$Target = "Bluetooth",
    [string]$Action = "status" # "on", "off", "status"
)

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { 
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' 
})[0]

[Windows.Devices.Radios.Radio, Windows.System.Devices, ContentType = WindowsRuntime] | Out-Null
$op = [Windows.Devices.Radios.Radio]::GetRadiosAsync()
$task = $asTask.MakeGenericMethod([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]]).Invoke($null, @($op))
$task.Wait()
$radios = $task.Result

foreach ($r in $radios) {
    if ($r.Name -like "*$Target*" -or $r.Kind.ToString() -like "*$Target*") {
        if ($Action -eq "status") {
            Write-Host "$($r.Kind): $($r.State)"
            exit 0
        }
        $targetState = if ($Action -eq "on") { [Windows.Devices.Radios.RadioState]::On } else { [Windows.Devices.Radios.RadioState]::Off }
        $setOp = $r.SetStateAsync($targetState)
        $setTask = $asTask.MakeGenericMethod([Windows.Devices.Radios.RadioAccessStatus]).Invoke($null, @($setOp))
        $setTask.Wait()
        Write-Host "Result: $($setTask.Result), NewState: $($r.State)"
        exit 0
    }
}
Write-Host "Not found"
exit 1
