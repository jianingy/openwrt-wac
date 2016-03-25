#
# This piece of code is written by
#    Jianing Yang <jianingy.yang@gmail.com>
# with love and passion!
#
#        H A P P Y    H A C K I N G !
#              _____               ______
#     ____====  ]OO|_n_n__][.      |    |
#    [________]_|__|________)<     |YANG|
#     oo    oo  'oo OOOO-| oo\\_   ~o~~o~
# +--+--+--+--+--+--+--+--+--+--+--+--+--+
#                             18 Mar, 2016
#
from __future__ import absolute_import
from .exception import GenericError
from .utils import fatal
from .ubus import UBusClient, UBUS_STATUS_OK
from os.path import join as path_join
from tornado.gen import coroutine, Return
from tornado.options import options
import logging
import six

LOG = logging.getLogger('tornado.application')

FREQS_24 = {
    1: 2412, 2: 2417, 3: 2422, 4: 2427, 5: 2432, 6: 2437,
    7: 2442, 8: 2447, 9: 2452, 10: 2457, 11: 2462, 12: 2467,
    13: 2472
}
FREQS_50 = {
    36: 5180, 40: 5200, 44: 5220, 48: 5240, 52: 5260,
    56: 5280, 60: 5300, 64: 5320,
    149: 5745, 153: 5765, 157: 5785, 161: 5805, 165: 5825
}


class InvalidChannelError(GenericError):
    error_format = 'invalid wlan frequency: %(channel)s'


def expand_host(dest):
    if dest.startswith('@'):
        group_name = dest[1:]
        try:
            rows = file(path_join(options.group_dir, group_name)).readlines()
            dests = map(lambda x: x.strip(), rows)
        except IOError:
            fatal('cannot find group %s' % group_name)
            return []
        except Exception:
            raise
        else:
            return dests
    else:
        return [dest]


def raise_on_ubus_error(code, reason='unknown error'):
    if code == UBUS_STATUS_OK:
        return
    raise Return(('False', '[ERROR:%d] %s' % (code, reason)))


@coroutine
def create_multiple_ap(dest):
    aps = dict()
    for dest in dest:
        try:
            ap = UBusClient(dest)
            yield ap.login()
        except Exception as e:
            LOG.warn('unable to log into %s: %s' % (dest, str(e)))
        else:
            aps[dest] = ap
    raise Return(aps)


@coroutine
def client_list(aps):
    client_all = []
    for host, ap in six.iteritems(aps):
        hostapd_clients = yield ap.list_clients()
        for hostapd, retval in six.iteritems(hostapd_clients):
            freq = retval['freq']
            clients = retval['clients']
            ifname = hostapd.replace('hostapd.', '')
            client_all.extend([{'name': ap.hostname,
                                'host': host,
                                'ifname': ifname,
                                'freq': freq,
                                'mac': mac}
                               for mac in clients.keys()])
    raise Return(client_all)


@coroutine
def client_ban(ap, wlan_id, mac):
    result = yield ap.set_mac_filter_policy('deny', wlan_id)
    raise_on_ubus_error(result, 'cannot set policy')
    mac_list = yield ap.get_mac_list(wlan_id)
    mac_list.append(mac)
    result = yield ap.set_mac_list(list(set(mac_list)), wlan_id)
    raise_on_ubus_error(result, 'cannot set maclist')
    result = yield ap.commit('wireless')
    raise_on_ubus_error(result, 'cannot commit configuration')
    result = yield ap.del_client(wlan_id, mac, ban_time=1000)
    raise_on_ubus_error(result, 'cannot deauth client')
    raise Return((True, '%s banned' % mac))


@coroutine
def client_permit(ap, wlan_id, mac):
    result = yield ap.set_mac_filter_policy('deny', wlan_id)
    raise_on_ubus_error(result, 'cannot set policy')
    mac_list = yield ap.get_mac_list(wlan_id)
    if mac not in mac_list:
        raise Return((False, "mac doesn't exists"))
    mac_list.remove(mac)
    result = yield ap.set_mac_list(list(set(mac_list)), wlan_id)
    raise_on_ubus_error(result, 'cannot set maclist')
    result = yield ap.commit('wireless')
    raise_on_ubus_error(result, 'cannot commit configuration')
    raise Return((True, '%s permitted' % mac))


@coroutine
def ap_list(ap_list):
    ap_all = []
    for host, ap in six.iteritems(ap_list):
        status = dict(host=host)
        system_status = yield ap.get_system_status()
        status['system'] = system_status
        board_status = yield ap.get_board_status()
        status['board'] = board_status
        hostapd_clients = yield ap.list_clients()
        num_clients = sum([len(c[1]['clients'])
                           for c in six.iteritems(hostapd_clients)])
        status['num_clients'] = num_clients
        ap_all.append(status)

    raise Return(ap_all)


@coroutine
def wlan_list(ap_list):
    ap_all = []
    for host, ap in six.iteritems(ap_list):
        status = dict(host=host)
        board_status = yield ap.get_board_status()
        status['board'] = board_status
        wireless_status = yield ap.get_wireless_status()
        status['wireless'] = wireless_status
        ap_all.append(status)

    raise Return(ap_all)


@coroutine
def wlan_set_channel(ap, channel, wlan_id):
    result = yield ap.set_channel(channel, wlan_id)
    raise_on_ubus_error(result)
    result = yield ap.commit('wireless')
    raise_on_ubus_error(result, 'cannot commit configuration')
    raise Return((True, 'channel changed to %d' % channel))


@coroutine
def wlan_set_ssid(ap, ssid, wlan_id):
    result = yield ap.set_ssid(ssid, wlan_id)
    raise_on_ubus_error(result)
    result = yield ap.commit('wireless')
    raise_on_ubus_error(result, 'cannot commit configuration')
    raise Return((True, 'ssid changed to %s' % ssid))


@coroutine
def wlan_set_encryption(ap, method, key, wlan_id):
    result = yield ap.set_encryption(method, key, wlan_id)
    raise_on_ubus_error(result)
    result = yield ap.commit('wireless')
    raise_on_ubus_error(result, 'cannot commit configuration')
    raise Return((True, 'encryption changed to %s(%s)' % (key, method)))


@coroutine
def wlan_enable(ap, enable, wlan_id):
    result = yield ap.enable_wlan(enable, wlan_id)
    raise_on_ubus_error(result)
    result = yield ap.commit('wireless')
    raise_on_ubus_error(result, 'cannot commit configuration')
    raise Return((True, '%s' % ('enabled' if enable else 'disabled')))
