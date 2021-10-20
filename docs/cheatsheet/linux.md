# Misc linux tools cheatsheet

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

## Enable Magic Key
```shell
# Temporary
sudo sysctl -w kernel.sysrq=1

# Permanent
sudo vim /etc/sysctl.conf
# Add:
kernel.sysrq=1
```

## Write file without text editor: cat + EOF
```shell
cat << 'EOF' > task.xml
EOF
```
