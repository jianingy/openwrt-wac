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
from .exception import GenericError
from json import dumps as json_encode, loads as json_decode
from tornado.gen import coroutine, Return
from tornado.httpclient import AsyncHTTPClient
from tornado.options import options
from uuid import uuid4
import logging

LOG = logging.getLogger('tornado.application')

UBUS_STATUS_OK = 0
UBUS_STATUS_INVALID_COMMAND = 1
UBUS_STATUS_INVALID_ARGUMENT = 2
UBUS_STATUS_METHOD_NOT_FOUND = 3
UBUS_STATUS_NOT_FOUND = 4
UBUS_STATUS_NO_DATA = 5
UBUS_STATUS_PERMISSION_DENIED = 6
UBUS_STATUS_TIMEOUT = 7
UBUS_STATUS_NOT_SUPPORTED = 8
UBUS_STATUS_UNKNOWN_ERROR = 9
UBUS_STATUS_CONNECTION_FAILED = 10


class UBusServerError(GenericError):
    error_format = 'uci server error: %(reason)s'


class UBusClientError(GenericError):
    error_format = 'ERROR[%(code)s]: %(reason)s'


class UBusClient(object):

    def __init__(self, addr, port=80, username='root', password='daling.com'):
        self.addr = addr
        self.port = port
        self.session = '00000000000000000000000000000000'
        self.username = username
        self.password = password
        self.api_root = 'http://{host}:{port}/ubus'.format(host=addr,
                                                           port=port)

    @coroutine
    def _rpc_call(self, method, *args):
        http_client = AsyncHTTPClient()
        request_id = str(uuid4())
        payload = json_encode({'jsonrpc': '2.0',
                               'id': request_id,
                               'method': method,
                               'params': args})
        resp = yield http_client.fetch(self.api_root,
                                       connect_timeout=options.timeout,
                                       request_timeout=options.timeout,
                                       method='POST',
                                       body=payload)
        if resp.code != 200:
            raise UBusServerError(reason='server returns %s' % resp.code)

        try:
            LOG.debug('rpc returns: %s' % resp.body)
            data = json_decode(resp.body)
        except ValueError:
            raise UBusServerError(reason='server returns malformed json')
        else:
            if data['id'] != request_id:
                UBusServerError(reason='server did not returns'
                                ' correspond request_id')
            if 'result' in data:
                raise Return(data['result'])
            elif 'error' in data:
                error = data['error']
                raise UBusClientError(code=error['code'],
                                      reason=error['message'])
            else:
                UBusServerError(reason='server returns malformed json')

    def _status(self, code):
        return code

    @coroutine
    def call(self, *args):
        params = (self.session,) + args
        result = yield self._rpc_call('call', *params)
        raise Return(result)

    @coroutine
    def list(self, *args):
        params = (self.session,) + args
        result = yield self._rpc_call('list', *params)
        raise Return(result)

    @coroutine
    def login(self, username='root', password='daling.com'):
        cred = dict(username=username, password=password)
        result = yield self.call('session', 'login', cred)
        self.session = result[1]['ubus_rpc_session']
        board_status = yield self.get_board_status()
        if board_status:
            self.kernel = board_status.get('kernel', '')
            self.hostname = board_status.get('hostname', '')
            self.system = board_status.get('system', '')
            self.model = board_status.get('model', '')
            self.release = board_status.get('release', '')

    @coroutine
    def list_clients(self):
        clients = dict()
        hostapds = yield self.list('hostapd.*')
        for hostapd in hostapds.keys():
            clients[hostapd] = (yield self.call(hostapd, 'get_clients', {}))[1]
        raise Return(clients)

    @coroutine
    def del_client(self, wlan_id, mac, ban_time=0, reason=1, deauth=True):
        result = yield self.call('hostapd.wlan%d' % wlan_id,
                                 'del_client',
                                 {'addr': mac,
                                  'reason': reason,
                                  'deauth': deauth,
                                  'ban_time': ban_time})
        raise Return(self._status(result[0]))

    @coroutine
    def get_mac_list(self, wlan_id):
        result = yield self.call('uci', 'get',
                                 {'config': 'wireless',
                                  'section': '@wifi-iface[%d]' % wlan_id,
                                  'option': 'maclist'})
        if result[0] == 0:
            raise Return(result[1]['value'] if len(result) > 1 else [])
        else:
            raise UBusServerError(reason=self._status(result[0]))

    @coroutine
    def set_channel(self, channel, wlan_id):
        result = yield self.call('uci', 'set',
                                 {'config': 'wireless',
                                  'section': 'radio%d' % wlan_id,
                                  'values': {'channel': channel}})
        raise Return(self._status(result[0]))

    @coroutine
    def set_mac_filter_policy(self, policy, wlan_id):
        result = yield self.call('uci', 'set',
                                 {'config': 'wireless',
                                  'section': '@wifi-iface[%d]' % wlan_id,
                                  'values': {'macfilter': policy}})
        raise Return(self._status(result[0]))

    @coroutine
    def set_mac_list(self, mac_list, wlan_id):
        result = yield self.call('uci', 'set',
                                 {'config': 'wireless',
                                  'section': '@wifi-iface[%d]' % wlan_id,
                                  'values': {'maclist': mac_list}})
        raise Return(self._status(result[0]))

    @coroutine
    def set_ssid(self, ssid, wlan_id):
        result = yield self.call('uci', 'set',
                                 {'config': 'wireless',
                                  'section': '@wifi-iface[%d]' % wlan_id,
                                  'values': {'ssid': ssid}})
        raise Return(self._status(result[0]))

    @coroutine
    def set_encryption(self, method, key, wlan_id):
        result = yield self.call('uci', 'set',
                                 {'config': 'wireless',
                                  'section': '@wifi-iface[%d]' % wlan_id,
                                  'values': {'encryption': method,
                                             'key': key}})
        raise Return(self._status(result[0]))

    @coroutine
    def enable_wlan(self, enable, wlan_id):
        result = yield self.call('uci', 'set',
                                 {'config': 'wireless',
                                  'section': '@wifi-iface[%d]' % wlan_id,
                                  'values': {'disabled': 0 if enable else 1}})
        raise Return(self._status(result[0]))

    @coroutine
    def commit(self, config):
        result = yield self.call('uci', 'commit', {'config': config})
        raise Return(self._status(result[0]))

    @coroutine
    def confirm(self, config):
        result = yield self.call('uci', 'confirm', {'config': config})
        raise Return(self._status(result[0]))

    @coroutine
    def get_system_status(self):
        result = yield self.call('system', 'info', {})
        if result[0] != UBUS_STATUS_OK:
            raise Return(dict())
        raise Return(result[1])

    @coroutine
    def get_wireless_status(self):
        result = yield self.call('network.wireless', 'status', {})
        if result[0] != UBUS_STATUS_OK:
            raise Return(dict())
        raise Return(result[1])

    @coroutine
    def get_board_status(self):
        result = yield self.call('system', 'board', {})
        if result[0] != UBUS_STATUS_OK:
            raise Return(dict())
        raise Return(result[1])
