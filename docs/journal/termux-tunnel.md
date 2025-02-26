# Cloudflared Tunnel on Termux
This guide explains how to start a *Cloudflared* tunnel on an Android device using the *Termux* terminal.
With this setup, you can connect to your device remotely from the public Internet,
even if it's **behind NAT** or has a **changing public IP**.

You'll be able to use SSH and ADB to connect, and you won't need root access.

## Configuration
You'll need to configure some variables during the setup process.
Some of them will be known and have to updated once some steps are finished.
Some will be known upfront, while others will need updating as you go.
Save these in a `setup.env` file on both your Android device (server) and Linux desktop (client):
```sh
# Cloudflared tunnel ID
TUNNEL_ID=
# DNS name for SSH tunnel
TUNNEL_DNS_SSH=
# DNS name for ADB tunnel
TUNNEL_DNS_ADB=
# Slack webhook URL for notifications
SLACK_WEBHOOK=
# SSH public key of the client
SSH_CLIENT_PUB_KEY=
# Termux user ID, assigned by Android during installation
TERMUX_USER_ID=
# Local network IP address of the Android device
SERVER_LAN_IP=
```

## Cloudflare Setup
Open your [Cloudflare Dashboard](https://dash.cloudflare.com/)
and create a tunnel under
Zero Trust / Networks / Tunnels.
Create a `cloudflared` tunnel with the following public hostnames:

- `termux-ssh.example.com` pointing to a service `tcp://localhost:8022`
- `termux-adb.example.com` pointing to a service `tcp://localhost:5555`

After creating the tunnel, update your `setup.env` file with the new tunnel ID:
```sh
TUNNEL_ID=d6ab1533
TUNNEL_DNS_SSH=termux-ssh.example.com
TUNNEL_DNS_ADB=termux-adb.example.com
```

## Optional: Slack Notifications
Configure Slack incoming webhook to receive notifications as soon as the tunnel is online.
Update `setup.env`:
```sh
SLACK_WEBHOOK=https://hooks.slack.com/services/DUP4
```

## Add your SSH key
Get your client's public SSH key using `cat ~/.ssh/id_rsa.pub`
and update `setup.env`:
```sh
SSH_CLIENT_PUB_KEY="ssh-rsa SSHRSAKEY me@box"
```

## Termux Setup
Install [Termux](https://github.com/termux/termux-app/releases/download/v0.118.1/termux-app_v0.118.1+github-debug_arm64-v8a.apk)
on your Android device.

Install the necessary packages:
```sh
pkg --check-mirror update
pkg install vim git openssh curl curlie dnsutils make python uv zsh termux-api
uv pip install --system supervisor
```

Find your user ID and LAN IP address with:
```sh
id -u
ifconfig
```
Update your `setup.env` with this information:
```sh
TERMUX_USER_ID=10000
SERVER_LAN_IP=192.168.0.2
```

Create and activate `setup.env`:
```sh
vim setup.env  # paste the content
. setup.env
```

Add client's SSH key to `~/.ssh/authorized_keys`.
```sh
mkdir -p ~/.ssh
echo "$SSH_CLIENT_PUB_KEY" >> ~/.ssh/authorized_keys
```

For easier typing, you can run the SSH server on your Android device
and connect to it from the same LAN.
```sh
# On the Android device:
sshd -D -d -p 8023
# On the client device:
. setup.env
ssh $TERMUX_USER_ID@$SERVER_LAN_IP -p 8023
# Now you can run the rest of the commands remotely
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

Install [Termux:API](https://github.com/termux/termux-api)
and [Termux:Widget](https://github.com/termux/termux-widget)
```sh
mkdir -p tmp
wget https://github.com/termux/termux-api/releases/download/v0.50.1/termux-api_v0.50.1+github-debug.apk -O tmp/termux-api_v0.50.1+github-debug.apk
termux-open tmp/termux-api_v0.50.1+github-debug.apk

wget https://github.com/termux/termux-widget/releases/download/v0.14.0/termux-widget-app_v0.14.0+github.debug.apk -O tmp/termux-widget-app_v0.14.0+github.debug.apk
termux-open tmp/termux-widget-app_v0.14.0+github.debug.apk

mkdir -p /data/data/com.termux/files/home/.shortcuts/tasks
chmod 700 -R /data/data/com.termux/files/home/.shortcuts
```

Install the correct version of `cloudflared` (don't use `pkg install cloudflared`):
```sh
mkdir -p tmp
wget https://github.com/igrek51/cloudflared-termux/releases/download/2025.2.0/cloudflared -O tmp/cloudflared
chmod +x tmp/cloudflared
install cloudflared /data/data/com.termux/files/usr/bin
```
Or build it [manually](https://github.com/rajbhx/cloudflared-termux/blob/main/Cloudflared-termux_%40rajbhx.sh).

Install the local ADB client. Enable Developer Options and USB debugging, and authorize the device:
```sh
curl -s https://raw.githubusercontent.com/rendiix/termux-adb-fastboot/master/install.sh | bash
adb devices  # This client should have access to a local device
adb shell
```

Authenticate and configure `cloudflared`:
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

Configure a Slack notifier script.
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

Set up `supervisord` to run services in background:

- SSH server,
- cloudflared tunnel
- Slack notifier

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

Prepare useful scripts:
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

On your Android device, add widgets from Termux:Widget for:

- `~/.shortcuts/tasks/open-tunnel.sh`
- `~/.shortcuts/tasks/close-tunnel.sh`

## Opening the tunnel
Tap the `open-tunnel.sh` widget.
You should get the slack notification when the tunnel is open.

## Client prerequisites
You'll need:

- SSH client with generated public key
- Cloudflared client
- ADB client
- `scrcpy` client

## Connecting from the client
Access the Cloudflared tunnel from the client device.
This opens local port 8023 to forward SSH traffic through Cloudflare to the remote server.
```sh
. setup.env
cloudflared access tcp --loglevel debug --hostname $TUNNEL_DNS_SSH --url localhost:8023
```
Now, connect to the SSH tunnel:
```sh
ssh $TERMUX_USER_ID@localhost -p 8023
```

Once you're in, open ADB port on the server for remote debugging:
```sh
adb tcpip 5555
adb devices  # This should list local emulator-5554
```

Open another tunnel to forward the ADB port.
```sh
cloudflared access tcp --loglevel debug --hostname $TUNNEL_DNS_ADB --url localhost:5556
```

Finally, connect to the remote device through the ADB tunnel:
```sh
adb connect localhost:5556
scrcpy -s localhost:5556
```
