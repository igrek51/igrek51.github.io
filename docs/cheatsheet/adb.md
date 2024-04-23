# ADB cheatsheet
## Logcat dump
Select device 43d075de, filter selected tags with DEBUG level, SILENT other tags, colorful, show with timestamp & PID
```
adb -s 43d075de logcat dupa0:D dupa1:D dupa2:D dupa3:D dupa4:D *:S -v time -v color
```
Short messages only:
```
adb -s 43d075de logcat dupa0:D dupa1:D dupa2:D dupa3:D dupa4:D *:S -v raw -v color
adb -s F5AZB702J659 logcat dupa0:D dupa1:D dupa2:D dupa3:D dupa4:D *:S -v raw -v color
./adb logcat songbook0:D songbook1:D songbook2:D songbook3:D songbook4:D '*:S' -v raw -v color
```

Print last 10000 lines (`-T 10000`) with errors (`*:E`) only (`-s`) and exit (`-d`). Show time, tag & message (`-v time`):
```
adb logcat -d -T 10000 -s *:E -v color -v time -b main
```

Print logs of a package (by tag):
```
adb logcat -d -T 10000 -s songbook0:D songbook1:D songbook2:d songbook3:D songbook4:D -v color -v time -b main
adb logcat -d -s dupa0:D dupa1:D dupa2:D dupa3:D -v color -v time -b main
```

Print debug logs of one process (by PID):
```
adb logcat -d '*:D' -v color -v time -b main --pid=30280
```

## Backup application data (/data/data)
```bash
# Backup app data only
adb backup -noapk igrek.songbook
# Extract
( printf "\x1f\x8b\x08\x00\x00\x00\x00\x00" ; tail -c +25 backup.ab ) |  tar xfvz -

# Backup app data and apk
adb backup -apk com.azure.authenticator -f appdata.bak
# Restore
adb restore appdata.bak

# Backup app data only
adb backup com.azure.authenticator -f appdata.bak
```

## Simulate key input
```
adb shell input text ---text---
adb shell input keyevent 66 # enter
adb shell input text text3
adb shell input keyevent 66 # enter
adb shell input text ---text---
```

Click the home button
```
adb shell input keyevent 3
```

## Wireless debugging over WiFi connection
Enable Wireless debugging:
```
cd /mnt/data/ext/opt/android-sdk/platform-tools
adb devices
adb shell setprop service.adb.tcp.port 4448
adb tcpip 4448
adb shell ip addr show dev wlan0
adb connect 192.168.0.250:4448
```
Disable:
```
adb shell setprop service.adb.tcp.port -1
adb disconnect 192.168.0.250:4448
adb kill-server
```

## List installed packages
```
pm list packages
```

## Uninstall bloatware packages (Xiaomi)
```
pm uninstall -k --user 0 com.miui.msa.global
pm uninstall -k --user 0 com.xiaomi.mipicks
pm uninstall -k --user 0 com.facebook.appmanager
pm uninstall -k --user 0 com.facebook.services
pm uninstall -k --user 0 com.facebook.system
pm uninstall -k --user 0 com.xiaomi.simactivate.service
pm uninstall -k --user 0 com.miui.videoplayer
pm uninstall -k --user 0 com.miui.micloudsync
pm uninstall -k --user 0 com.miui.cloudservice
pm uninstall -k --user 0 com.miui.cloudbackup
pm uninstall -k --user 0 com.miui.yellowpage
pm uninstall -k --user 0 com.xiaomi.joyose
pm uninstall -k --user 0 com.miui.analytics
pm uninstall -k --user 0 com.xiaomi.payment
pm uninstall -k --user 0 com.xiaomi.mi_connect_service
```

Install preinstalled package back:
```
cmd package install-existing com.miui.miwallpaper
```

## Uninstall bloatware packages (Motorola)
```
adb shell pm uninstall -k --user 0 com.facebook.appmanager
adb shell pm uninstall -k --user 0 com.facebook.services
adb shell pm uninstall -k --user 0 com.facebook.system
adb shell pm uninstall -k --user 0 com.facebook.katana
```

## Disable annoying NFC icon
Enable "USB Debuging" in first place.
```
adb shell settings put secure icon_blacklist nfc
```

## List Settings
```
adb shell settings list system
adb shell settings list global
adb shell settings list secure
```

## Look up Android version
Android version:
```
getprop ro.build.version.release
```
API level:
```
getprop ro.build.version.sdk
```

## Access data dir through shell
```sh
adb shell
> run-as igrek.songbook
> cd /data/data/igrek.songbook
```
