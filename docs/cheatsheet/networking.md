# Networking on Linux

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

## Netcat
Start Listening:
```sh
nc -lvp 1234
```
Connect:
```sh
nc -v 192.168.0.1 1234
```

## Nmcli
### Scan Wifi networks
```sh
nmcli -f IN-USE,SSID,BSSID,CHAN,FREQ,RATE,SIGNAL,BARS,SECURITY,DEVICE device wifi list --rescan yes
```

## Connect to particular access point (BSSID)
```sh
nmcli dev wifi connect <BSSID>
```
