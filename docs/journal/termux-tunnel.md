# Cloudflared tunnel for Termux
This guide explains how to start a *Cloudflared* tunnel on an Android device with *Termux* terminal
and how to connect to it remotely from the public Internet,
even if the device is **behind the NAT** and has a **volatile public IP**.

This will allow to connect to it through SSH as well as ADB.

This setup doesn't require root access.

## Setup confguration
These variables are needed during the setup.
Some of them will be known and have to updated once some steps are finished.
Keep them in a `setup.env` file on both server (Android device) and the client (Linux desktop).:
```sh
# ID of a Cloudflared tunnel
TUNNEL_ID=
# DNS name for SSH tunnel
TUNNEL_DNS_SSH=
# DNS name for ADB tunnel
TUNNEL_DNS_ADB=
# Slack incoming webhook for notifications
SLACK_WEBHOOK=
# client's SSH public key
SSH_CLIENT_PUB_KEY=
# ID of a Termux user, auto-assigned by Android during installation
TERMUX_USER_ID=
# IP address of Android device in a local network
SERVER_LAN_IP=
```

## Cloudflare Setup
Open your [Cloudflare Dashboard](https://dash.cloudflare.com/)
and create a tunnel in:
Zero Trust / Networks / Tunnels / Create a `cloudflared` tunnel with the following public hostnames:
- `termux-ssh.example.com` pointing to a service `tcp://localhost:8022`
- `termux-adb.example.com` pointing to a service `tcp://localhost:5555`

Read newly created tunnel ID and update the `setup.env` file:
```sh
TUNNEL_ID=d6ab1533
TUNNEL_DNS_SSH=termux-ssh.example.com
TUNNEL_DNS_ADB=termux-adb.example.com
```

## Optional: Slack webhook
Configure Slack incoming webhook to receive notifications as soon as the tunnel is online.
Update `setup.env`:
```sh
SLACK_WEBHOOK=https://hooks.slack.com/services/DUP4
```

## Bind your SSH key
Read your public SSH key of the client device with `cat ~/.ssh/id_rsa.pub`.
Update `setup.env`:
```sh
SSH_CLIENT_PUB_KEY="ssh-rsa SSHRSAKEY me@box"
```

## Termux Setup
Install [Termux](https://github.com/termux/termux-app/releases/download/v0.118.1/termux-app_v0.118.1+github-debug_arm64-v8a.apk)
on Android device.

We're going to need these packages:
```sh
pkg --check-mirror update
pkg install vim git openssh curl curlie dnsutils make python uv zsh termux-api
uv pip install --system supervisor
```

Read the user ID and LAN IP address
```sh
id -u
ifconfig
```
and update it in `setup.env`:
```sh
TERMUX_USER_ID=10000
SERVER_LAN_IP=192.168.0.2
```

Create `setup.env` and activate it:
```sh
vim setup.env  # paste the content
. setup.env
```

Add client's SSH key to `~/.ssh/authorized_keys`.
```sh
mkdir -p ~/.ssh
echo "$SSH_CLIENT_PUB_KEY" >> ~/.ssh/authorized_keys
```

Optionally, for faster typing, run SSH server on Android device,
connect to it (being in the same LAN network) and run the rest of the commands remotely.
```sh
# on Android server side:
sshd -D -d -p 8023
# on Client side:
. setup.env
ssh $TERMUX_USER_ID@$SERVER_LAN_IP -p 8023
```

Setup Termux for convenient use:
```sh
cat << 'EOF' > ~/.termux/termux.properties
extra-keys = [ \
 ['(', ')', '[', ']', '<', '>', '`', '*'], \
 [':', '~', '-', '_', '/', '|', 'BACKSLASH', '='], \
 ['ESC','QUOTE', 'APOSTROPHE', 'PGUP', 'HOME','UP','END','+'], \
 ['TAB','CTRL','ALT','PGDN','LEFT','DOWN','RIGHT','DEL'] \
]
allow-external-apps = true
EOF
```

Install [Termux:API](https://github.com/termux/termux-api) & [Termux:Widget](https://github.com/termux/termux-widget)
```sh
mkdir -p tmp
wget https://github.com/termux/termux-api/releases/download/v0.50.1/termux-api_v0.50.1+github-debug.apk -O tmp/termux-api_v0.50.1+github-debug.apk
termux-open tmp/termux-api_v0.50.1+github-debug.apk

wget https://github.com/termux/termux-widget/releases/download/v0.14.0/termux-widget-app_v0.14.0+github.debug.apk -O tmp/termux-widget-app_v0.14.0+github.debug.apk
termux-open tmp/termux-widget-app_v0.14.0+github.debug.apk

mkdir -p /data/data/com.termux/files/home/.shortcuts/tasks
chmod 700 -R /data/data/com.termux/files/home/.shortcuts
```

Install correct cloudflared version (don't do `pkg install cloudflared`)
```sh
mkdir -p tmp
wget https://github.com/igrek51/cloudflared-termux/releases/download/2025.2.0/cloudflared -O tmp/cloudflared
chmod +x tmp/cloudflared
install cloudflared /data/data/com.termux/files/usr/bin
```
or build it [manually](https://github.com/rajbhx/cloudflared-termux/blob/main/Cloudflared-termux_%40rajbhx.sh).

Install Local ADB client. Enable Developer Options and USB debugging. Authorize the device.
```sh
curl -s https://raw.githubusercontent.com/rendiix/termux-adb-fastboot/master/install.sh | bash
adb devices
adb shell
```

Authenticate and configure `cloudflared`
```sh
mkdir -p ~/cloudflare
cloudflared tunnel login
cloudflared tunnel token --cred-file ~/.cloudflared/$TUNNEL_ID.json $TUNNEL_ID

cat << EOF > ~/.cloudflared/config.yml
# protocol: http2
url: tcp://localhost:8022
tunnel: $TUNNEL_ID
credentials-file: /data/data/com.termux/files/home/.cloudflared/$TUNNEL_ID.json
EOF
```

Configure Slack notifier script.
```sh
cat << EOF > ~/cloudflare/slack-notifier.sh
#!/data/data/com.termux/files/usr/bin/bash -ex
MESSAGE=\$(cat <<EOF2
Opening cloudflared tunnel...
User ID: \$(id -u)
Device: \$(getprop ro.product.brand) \$(getprop ro.product.model), \$(getprop ro.product.device), \$(uname -m)
Android: version \$(getprop ro.build.version.release), API level \$(getprop ro.build.version.sdk)
EOF2
)
curl -v -X POST -H 'Content-type: application/json' --data "{\"text\":\"\$MESSAGE\"}" \
    $SLACK_WEBHOOK
EOF
chmod +x ~/cloudflare/slack-notifier.sh
```

Configure supervisord to run services in background:
- SSH server,
- cloudflared tunnel
- Slack notifier.
```sh
cat << EOF > ~/cloudflare/supervisord.conf
[supervisord]
logfile=$HOME/cloudflare/supervisord.log

[program:sshd]
command=sshd -D -d -p 8022
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$HOME/cloudflare/sshd.log

[program:cloudflared]
command=cloudflared tunnel --loglevel debug run $TUNNEL_ID
autostart=true
autorestart=false
redirect_stderr=true
stdout_logfile=$HOME/cloudflare/cloudflared.log

[program:slack-notifier]
command=$HOME/cloudflare/slack-notifier.sh 2>&1
autostart=true
autorestart=false
redirect_stderr=true
stdout_logfile=$HOME/cloudflare/slack-notifier.log
startsecs=0
exitcodes=0

[supervisorctl]

[inet_http_server]
port = 127.0.0.1:9001

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface
EOF
```

Prepare useful scripts
```sh
cat << EOF > ~/cloudflare/Makefile
supervisor-start:
	supervisord -c $HOME/cloudflare/supervisord.conf --pidfile $HOME/cloudflare/supervisord.pid

tunnel-start:
	cloudflared tunnel --loglevel debug run $TUNNEL_ID

supervisor-status:
	supervisorctl -c $HOME/cloudflare/supervisord.conf status

supervisor-stop:
	supervisorctl -c $HOME/cloudflare/supervisord.conf shutdown
EOF

# Open Tunnel Script
cat << EOF > ~/.shortcuts/tasks/open-tunnel.sh
termux-wake-lock
supervisord -c $HOME/cloudflare/supervisord.conf --pidfile $HOME/cloudflare/supervisord.pid
termux-notification --group termux --title "Termux Tunnel" --content "Remote tunnel opened"
EOF

# Close Tunnel Script
cat << EOF > ~/.shortcuts/tasks/close-tunnel.sh
supervisorctl -c $HOME/cloudflare/supervisord.conf shutdown
termux-wake-unlock
termux-notification --group termux --title "Termux Tunnel" --content "Remote tunnel closed"
EOF
```

On your Android device, add widgets from Termux:Widget:
- `~/.shortcuts/tasks/open-tunnel.sh`
- `~/.shortcuts/tasks/close-tunnel.sh`

## Opening the tunnel
Click the `open-tunnel.sh` widget.
You should get the slack notification as the tunnel is opened.

## Client prerequisites
- SSH client with generated public key
- Cloudflared client
- ADB client
- `scrcpy` client

## Connecting from the client
Access the cloudflared tunnel from the client device.
This opens local port 8023 that will forward the SSH traffic through Cloudflare to the remote server.
```sh
. setup.env
cloudflared access tcp --loglevel debug --hostname $TUNNEL_DNS_SSH --url localhost:8023
```
Now, you can connect to the SSH tunnel:
```sh
ssh $TERMUX_USER_ID@localhost -p 8023
```

Once you're in, open ADB port on the server for the remote debugging:
```sh
adb tcpip 5555
adb devices  # This should list local emulator-5554
```

Open another tunnel to forward ADB port.
```sh
cloudflared access tcp --loglevel debug --hostname $TUNNEL_DNS_ADB --url localhost:5556
```

Finally, connect to the remote device through ADB tunnel:
```sh
adb connect localhost:5556
scrcpy -s localhost:5556
```
