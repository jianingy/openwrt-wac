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
from click import echo, style
import sys


def debug(msg):
    echo(style('[#] ' + msg, fg='white'))


def info(msg):
    echo(style('[*] ' + msg, fg='blue'))


def success(msg):
    echo(style('[+] ' + msg, fg='green'))


def error(msg):
    echo(style('[!] ' + msg, fg='red'))


def fatal(msg, code=111):
    echo(style('[!] ' + msg, fg='red'))
    sys.exit(code)


def out(msg):
    echo(msg)


def header_out(msg):
    echo(style(msg, fg='blue'), err=True)
