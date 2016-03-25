# Intro

WAC is a simple command line tool for managing groups of openwrt based rotuers.

# Features

* show system status (ip, load, mem, uptime) of all devices
* show wireless interface status (ssid, txpower, channel) all devices
* ban client by mac address
* change wireless settings (ssid, encryption, channel
* management devices by user-defined groups

# Installation

Install from pypi,

```
pip install openwrt-wac
```

Install from source,
```
git clone https://github.com/jianingy/openwrt-wac.git
cd openwrt-wac
python ./setup.py install
```

# Basic Usage


Users can define their own groups by putting files into `groups`
directory. Names of the files will be used as groupnames. Each file should
contain ip address or domains of openwrt devices. Here is an example,

```
192.168.100.202
192.168.100.203
192.168.100.204
192.168.100.207

```

After defined groups, you can use its name for various operations.

List all access points,

```
$ wac ap-list @soho2

name, host, #clients, loadavg, mem, uptime
CORP-SOHO-AP-1, 192.168.100.207, 35, 0.00 / 0.00 / 0.00, 104.3 MB / 128.9 MB, a month ago
CORP-SOHO-AP-13, 192.168.100.203, 54, 0.00 / 0.00 / 0.00, 103.9 MB / 128.9 MB, a month ago
CORP-SOHO-AP-14, 192.168.100.202, 68, 0.00 / 0.00 / 0.00, 100.2 MB / 128.9 MB, 29 days ago
CORP-SOHO-AP-18, 192.168.100.204, 47, 0.00 / 0.00 / 0.00, 103.4 MB / 128.9 MB, a month ago
```

List all wlan interfaces,

```
$ wac wlan-list @soho2
name, host, radio, wlan, ssid, enc, status, hwmode, htmode, txpower, channel
CORP-SOHO-AP-1, 192.168.100.207, radio0, wlan0, daling, psk2, up, 11g, HT40, 24, 11
CORP-SOHO-AP-1, 192.168.100.207, radio1, wlan1, daling-5g, psk2, up, 11a, HT20, 24, 36
CORP-SOHO-AP-13, 192.168.100.203, radio0, wlan0, daling, psk2, up, 11g, HT40, 24, 9
CORP-SOHO-AP-13, 192.168.100.203, radio1, wlan1, daling-5g, psk2, up, 11a, HT20, 24, 153
CORP-SOHO-AP-14, 192.168.100.202, radio0, wlan0, daling, psk2, up, 11g, HT40, 24, 11
CORP-SOHO-AP-14, 192.168.100.202, radio1, wlan1, daling-5g, psk2, up, 11a, HT20, 24, 149
CORP-SOHO-AP-18, 192.168.100.204, radio0, wlan0, daling, psk2, up, 11g, HT40, 24, 7
CORP-SOHO-AP-18, 192.168.100.204, radio1, wlan1, daling-5g, psk2, up, 11a, HT20, 24, 149
```

Change a wlan setting by its address,

```
wac wlan-edit --wlan-id 0 --channel 1 192.168.100.203
wac wlan-edit --wlan-id 0 --ssid 'public-wifi' 192.168.100.203
wac wlan-edit --wlan-id 0 --encryption 'psk2:password' 192.168.100.203
```

Ban a client by its mac address,

```
wac client-ban 192.168.100.203 --wlan-id 1 --mac bc:4c:c4:ff:ff:ff
```

Remove a client from ban list,
```
wac client-permit 192.168.100.203 --wlan-id 1 --mac bc:4c:c4:ff:ff:ff
```


# License
```
   Copyright 2016, Jianing Yang

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
```
