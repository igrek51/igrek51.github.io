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
### Check if TCP port is open
```shell
sudo nmap -sS -p22 192.168.0.50 # SYN scan
sudo nmap -sY -p22 192.168.0.50 # open/filtered/closed
```
### Discover hosts with ping scan
```shell
sudo nmap -sP 192.168.0.1/24
```

## Enable Magic Key
```shell
# Temporary
sudo sysctl -w kernel.sysrq=1

# Permanent
sudo vim /etc/sysctl.conf
# Add:
kernel.sysrq=1
```

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
