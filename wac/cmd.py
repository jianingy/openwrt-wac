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
#                             17 Mar, 2016
#
from __future__ import absolute_import
from . import service
from .utils import fatal, out, header_out
from humanize import naturalsize, naturaltime
from tornado.gen import coroutine
from tornado.log import enable_pretty_logging
from tornado.ioloop import IOLoop
from tornado.options import options, define

import click
import functools
import six
import traceback


def pretty_exception(fn):

    @functools.wraps(fn)
    def wrap(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if options.debug:
                traceback.print_exc(e)
            fatal(e.message)

    return wrap


def cmp_host(x, y):
    if x > y:
        return 1
    return -1


def _val(d, path, transformer=lambda x: unicode(x)):
    current_value = d
    try:
        for node in path.split('.'):
            if node.isdigit():
                current_value = current_value[int(node)]
            else:
                current_value = current_value[node]
    except KeyError:
        return 'n/a'
    else:
        return transformer(current_value)


@click.group()
@click.option('--debug', flag_value=True, default=False,
              help='enable debug mode')
@click.option('--timeout', default=5, help='timeout')
@click.option('--group-dir', default='groups',
              help='directory of group definition files')
def wac(group_dir, debug, timeout):
    define('debug', default=debug)
    define('timeout', default=timeout)
    define('group-dir', default=group_dir)
    if debug:
        options.logging = 'debug'

    enable_pretty_logging()


@wac.command(name='client-list',
             help='list all connected devices')
@click.argument('host', type=str, nargs=-1)
def client_list(host):

    hosts = service.expand_host(host[0])

    @coroutine
    def _run():
        aps = yield service.create_multiple_ap(hosts)
        clients = yield service.client_list(aps)
        header_out('name, host, ifname, freq, mac_address')
        out('\n'.join(['{name} {host} {ifname} {freq} {mac}'.format(**c)
                       for c in clients]))

    IOLoop.instance().run_sync(_run)


@wac.command(name='client-ban', help='ban a client by mac address')
@click.option('--wlan-id', type=int, help='wlan id')
@click.option('--mac', type=str, help='mac address to ban')
@click.argument('host', type=str, nargs=-1)
@pretty_exception
def client_ban(wlan_id, mac, host):

    hosts = service.expand_host(host[0])

    @coroutine
    def _run():
        aps = yield service.create_multiple_ap(hosts)
        header_out('host, wlan_id, reason')
        for ap in aps.values():
            status = yield service.client_ban(ap, wlan_id, mac)
            out('%s, %s, %s' % (ap.addr, wlan_id, status[1]))

    IOLoop.instance().run_sync(_run)


@wac.command(name='client-permit', help="restore a client's access")
@click.option('--wlan-id', type=int, help='wlan id')
@click.option('--mac', type=str, help='mac address to permit')
@click.argument('host', type=str, nargs=-1)
@pretty_exception
def client_permit(wlan_id, mac, host):

    hosts = service.expand_host(host[0])

    @coroutine
    def _run():
        aps = yield service.create_multiple_ap(hosts)
        header_out('host, wlan_id, reason')
        for ap in aps.values():
            status = yield service.client_permit(ap, wlan_id, mac)
            out('%s, %s, %s' % (ap.addr, wlan_id, status[1]))

    IOLoop.instance().run_sync(_run)


@wac.command(name='ap-list', help='show all openwrt devices status')
@click.argument('host', type=str, nargs=-1)
def ap_list(host):

    hosts = service.expand_host(host[0])

    def _calc_load(x):
        return x / 65535

    @coroutine
    def _run():
        rows = []
        aps = yield service.create_multiple_ap(hosts)
        details = yield service.ap_list(aps)
        header_out('name, host, #clients, loadavg, mem, uptime')
        for ap in details:
            row = []
            row.append(_val(ap, 'board.hostname'))
            row.append(_val(ap, 'host'))
            row.append('%s' % (_val(ap, 'num_clients')))
            row.append('%.2f / %.2f / %.2f' % (
                _val(ap, 'system.load.0', _calc_load),
                _val(ap, 'system.load.1', _calc_load),
                _val(ap, 'system.load.2', _calc_load)))
            row.append('%s / %s' %
                       (_val(ap, 'system.memory.free', naturalsize),
                        _val(ap, 'system.memory.total', naturalsize)))
            row.append('%s' % (_val(ap, 'system.uptime', naturaltime)))
            rows.append(', '.join(row))

        out('\n'.join(sorted(rows, cmp_host)))
    IOLoop.instance().run_sync(_run)


@wac.command(name='wlan-edit', help='change wlan settings')
@click.option('--wlan-id', type=int, default=0,
              help='wlan id')
@click.option('--enable', 'state', flag_value='enable', help='disable wlan')
@click.option('--disable', 'state', flag_value='disable', help='disable wlan')
@click.option('--ssid', type=str, help='new ssid to change')
@click.option('--channel', type=int, help='new channel to change')
@click.option('--encryption', type=str,
              help='new password to change. format: "method:secret"')
@click.argument('host', type=str, nargs=-1)
@pretty_exception
def wlan_edit(wlan_id, state, channel, ssid, encryption, host):

    hosts = service.expand_host(host[0])

    @coroutine
    def _run():
        aps = yield service.create_multiple_ap(hosts)
        for ap in aps.values():
            if channel:
                status = yield service.wlan_set_channel(ap, channel, wlan_id)
                out('%s, wlan%d, %s' % (ap.addr, wlan_id, status[1]))
            if ssid:
                status = yield service.wlan_set_ssid(ap, ssid, wlan_id)
                out('%s, wlan%d, %s' % (ap.addr, wlan_id, status[1]))
            if encryption:
                method, _, key = encryption.partition(':')
                status = yield service.wlan_set_encryption(ap, method, key,
                                                           wlan_id)
                out('%s, wlan%d, %s' % (ap.addr, wlan_id, status[1]))
            if state == 'enable':
                status = yield service.wlan_enable(ap, True, wlan_id)
                out('%s, wlan%d, %s' % (ap.addr, wlan_id, status[1]))
            if state == 'disable':
                status = yield service.wlan_enable(ap, False, wlan_id)
                out('%s, wlan%d, %s' % (ap.addr, wlan_id, status[1]))

    IOLoop.instance().run_sync(_run)


@wac.command(name='wlan-list', help='show all wlan interfaces status')
@click.argument('host', type=str, nargs=-1)
def wlan_list(host):

    hosts = service.expand_host(host[0])

    @coroutine
    def _run():
        rows = []
        aps = yield service.create_multiple_ap(hosts)
        details = yield service.wlan_list(aps)
        header_out('name, host, radio, wlan, ssid, enc, '
                   'status, hwmode, htmode, '
                   'txpower, channel')
        for ap in details:
            for radio, status in six.iteritems(ap['wireless']):
                for wlan in status['interfaces']:
                    row = []
                    row.append(_val(ap, 'board.hostname'))
                    row.append(_val(ap, 'host'))
                    row.append('%s' % radio)
                    row.append('%s' % _val(wlan, 'ifname'))
                    row.append('%s' % _val(wlan, 'config.ssid'))
                    row.append('%s' % _val(wlan, 'config.encryption'))
                    row.append(_val(status, 'up',
                                    lambda x: 'up' if x else 'down'))
                    row.append(_val(status, 'config.hwmode'))
                    row.append(_val(status, 'config.htmode'))
                    row.append(_val(status, 'config.txpower'))
                    row.append(_val(status, 'config.channel'))
                    rows.append(', '.join(row))

        out('\n'.join(sorted(rows, cmp_host)))
    IOLoop.instance().run_sync(_run)
