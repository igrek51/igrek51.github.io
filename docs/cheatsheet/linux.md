# Misc Linux tools cheatsheet

## Less
### Less without line wrapping
```
less -S
```
### Colorful less
```
less -r
```
### Less: leave uncleared output on exit
```
export LESS="-X"
```

## Screen
```shell
screen -S new_screen_name # create named screen
# detach with Ctrl+a, d
screen -ls # list screens
screen -r 5050 # reattach
screen -d -r byname # reattach not-detached session
```

## Nmap
### Discover hosts, MACs, hostnames with ping scan
```shell
sudo nmap -sP 192.168.0.1/24
```

### Check if TCP port is open
```shell
sudo nmap -sS -p22 192.168.0.50 # SYN scan
sudo nmap -sY -p22 192.168.0.50 # open/filtered/closed
```

### Scan port range
```sh
nmap -p 1-65535 localhost
```

### Scan OS and detect services
```sh
nmap -A -T4 192.168.0.49
```

### Detect service versions
```sh
nmap -sV 192.168.0.49
```

### CVE detection
```sh
nmap -Pn --script vuln 192.168.0.49
```

## Enable Magic Key
```shell
# Temporary
sudo sysctl -w kernel.sysrq=1
# or
sudo echo 1 > /proc/sys/kernel/sysrq

# Permanent
sudo vim /etc/sysctl.conf
# Add:
kernel.sysrq=1
```

To use the magic SysRq key, press the key combo `ALT`-`SysRq`-`<command key>`:

- `r` - Turns off keyboard raw mode and sets it to XLATE
- `e` - Send a SIGTERM to all processes, except for init.
- `i` - Send a SIGKILL to all processes, except for init.
- `s` - Will attempt to sync all mounted filesystems.
- `u` - Will attempt to remount all mounted filesystems read-only.
- `b` - Will immediately reboot the system without syncing or unmounting your disks.
- `o` - Will shut your system off (if configured and supported).

!!! note
    Some keyboards may not have a key labeled ‘SysRq’. The ‘SysRq’ key is also known as the ‘Print Screen’ key.

## GPG
### Add GPG key to trusted keys (fix NO_PUBKEY)
```shell
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys <PUBKEY>
```

## Shell
### Write file without text editor: cat + EOF
```shell
cat << 'EOF' > task.xml
EOF
```
### Turn on strict mode in bash
```shell
set -euxo pipefail
```

## xargs
Run command on each line:
```sh
ls -1 *.sh | xargs -I %s echo "mv '%s' '%s.bak'"
```
