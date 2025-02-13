# ADB cheatsheet
## Logcat dump
Select device 43d075de, filter selected tags with DEBUG level, SILENT other tags, colorful, show with timestamp & PID
```sh
adb -s 43d075de logcat dupa0:D dupa1:D dupa2:D dupa3:D dupa4:D *:S -v time -v color
```
Short messages only:
```sh
adb -s 43d075de logcat dupa0:D dupa1:D dupa2:D dupa3:D dupa4:D *:S -v raw -v color
adb -s F5AZB702J659 logcat dupa0:D dupa1:D dupa2:D dupa3:D dupa4:D *:S -v raw -v color
./adb logcat songbook0:D songbook1:D songbook2:D songbook3:D songbook4:D '*:S' -v raw -v color
```

Print last 10000 lines (`-T 10000`) with errors (`*:E`) only (`-s`) and exit (`-d`). Show time, tag & message (`-v time`):
```sh
adb logcat -d -T 10000 -s *:E -v color -v time -b main
```

Print logs of a package (by tag):
```sh
adb logcat -d -T 10000 -s songbook0:D songbook1:D songbook2:d songbook3:D songbook4:D -v color -v time -b main
adb logcat -d -s dupa0:D dupa1:D dupa2:D dupa3:D -v color -v time -b main
```

Print debug logs of one process (by PID):
```sh
adb logcat -d '*:D' -v color -v time -b main --pid=30280
```

## Backup application data (/data/data)
```sh
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
PACKAGE=com.azure.authenticator && adb backup $PACKAGE -f $PACKAGE.bak
```

## Make backup of installed APK
Locate APK by running:
```sh
pm path com.google.android.videos
```

Pull APKs
```sh
adb pull /data/app/com.google.android.videos-E83Rbdyp43iEgzifOQfMRw==/base.apk com.google.android.videos.bak.apk
adb pull /data/app/com.google.android.videos-E83Rbdyp43iEgzifOQfMRw==/split_config.armeabi_v7a.apk split_config.armeabi_v7a.apk
adb pull /data/app/com.google.android.videos-E83Rbdyp43iEgzifOQfMRw==/split_config.xhdpi.apk split_config.xhdpi.apk
```

## Simulate key input
```sh
adb shell input text ---text---
adb shell input keyevent 66 # enter
adb shell input text text3
adb shell input keyevent 66 # enter
adb shell input text ---text---
```

Click the home button
```sh
adb shell input keyevent 3
```

Display and control your Android device with [scrcpy](https://github.com/Genymobile/scrcpy)

## Wireless debugging over WiFi connection
Enable Wireless debugging:
```sh
cd /mnt/data/ext/opt/android-sdk/platform-tools
adb devices
adb shell setprop service.adb.tcp.port 4448
adb tcpip 4448
adb shell ip addr show dev wlan0
adb connect 192.168.0.250:4448
```
Disable:
```sh
adb shell setprop service.adb.tcp.port -1
adb disconnect 192.168.0.250:4448
adb kill-server
```

Alternatively:
1. Connect the Android Device to via USB (Initial Setup)
2. Restart ADB in TCP/IP: `adb tcpip 5555`
3. Disconnect the USB Cable
4. Connect remotely: `adb connect PUBLIC_IP:5555`

## List installed packages
```sh
pm list packages
```

List disabled packages
```sh
pm list packages -d
```

## Disable package
```sh
pm disable-user --user 0 com.google.android.videos
```

Re-enable:
```sh
pm enable --user 0 com.google.android.videos
```

## Uninstall bloatware packages (Xiaomi)
```sh
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
```sh
cmd package install-existing com.miui.miwallpaper
```

## Uninstall bloatware packages (Motorola)
```sh
adb shell pm uninstall -k --user 0 com.facebook.appmanager
adb shell pm uninstall -k --user 0 com.facebook.services
adb shell pm uninstall -k --user 0 com.facebook.system
adb shell pm uninstall -k --user 0 com.facebook.katana
adb shell pm uninstall -k --user 0 com.taboola.mip
```

## Clear cache
```sh
pm trim-caches 9999999999
```

## Hide annoying NFC icon
Enable "USB Debuging" in first place.
```sh
adb shell settings put secure icon_blacklist nfc
```

## Hide VoLTE icon
```sh
adb shell settings put secure icon_blacklist rotate,ims
```

## List Settings
```sh
adb shell settings list system
adb shell settings list global
adb shell settings list secure
```

## Look up Android version
Android version:
```sh
getprop ro.build.version.release
```
API level:
```sh
getprop ro.build.version.sdk
```

## Access data dir through shell
```sh
adb shell
> run-as igrek.songbook
> cd /data/data/igrek.songbook
```

## Synchronize files over ADB
```shell
# On Android device:
# 1. Open Termux
# 2. Install:
pkg install openssh
# 3. Authorize host in ~/.ssh/authorized_keys
# 4. Open SSH server:
sshd

# On Host:
# 1. Add SSH config to ~/.ssh/config: name: termux, Port 8022, User taken from `id`
# 2. Dry Run
rsync -rvhn --delete --size-only /mnt/data/Igrek/mp3/ termux:/data/data/com.termux/files/home/sd/mp3
# 3. Synchronize files
rsync -rvh --delete --size-only --info=progress2 /mnt/data/Igrek/mp3/ termux:/data/data/com.termux/files/home/sd/mp3

# On Android:
# 5. Close SSH server:
pkill sshd
```
