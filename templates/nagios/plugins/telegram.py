#!/usr/local/bin/python2
# MIT License
#
# Copyright (c) 2017 Florian Kaiser
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import print_function

import argparse
import json

try:
    # Python 2
    from urllib import urlencode
    from urllib import urlopen
except ImportError:
    # Python 3
    from urllib.parse import urlencode
    from urllib.request import urlopen


def pretty_json(json_string):
    return json.dumps(json.loads(json_string), indent=2, sort_keys=True)


class UndefinedArgument():
    pass


class TelegramBot():
    def __init__(self, endpoint, token, verbose=False):
        self.endpoint = endpoint
        self.token = token
        self.verbose = verbose

    def log(self, *messages):
        print(*messages)

    def _make_url(self, method, args):
        args = '?%s' % urlencode(args) if args else ''
        return '%s/bot%s/%s%s' % (self.endpoint, self.token, method, args)

    def _urlopen(self, url, data=UndefinedArgument()):
        if isinstance(data, UndefinedArgument):
            response = urlopen(url)
        else:
            response = urlopen(url, data.encode('utf-8'))

        response_text = response.read().decode('utf-8')

        if self.verbose:
            try:
                pretty_response_text = pretty_json(response_text)
            except ValueError:
                pretty_response_text = response_text
            self.log(url, data, response.code, pretty_response_text)

        return response.code, response_text

    def get(self, method, args={}):
        return self._urlopen(self._make_url(method, args))

    def post(self, method, args={}, data=''):
        if type(data) == dict:
            data = urlencode(data)
        return self._urlopen(self._make_url(method, args), data)

    def sendMessage(self, args):
        data = dict()
        data['chat_id'] = args.chat_id
        data['text'] = args.text
        data['disable_web_page_preview'] = args.disable_web_page_preview
        data['disable_notification'] = args.disable_notification
        if args.parse_mode is not None:
            data['parse_mode'] = args.parse_mode
        if args.reply_to_message_id is not None:
            data['reply_to_message_id'] = args.reply_to_message_id
        if args.reply_markup is not None:
            data['reply_markup'] = args.reply_markup

        return self.post('sendMessage', data=data)

    def getUpdates(self, args):
        data = dict()
        if args.offset is not None:
            data['offset'] = args.offset
        if args.limit is not None:
            data['limit'] = args.limit
        if args.timeout is not None:
            data['timeout'] = args.timeout
        if args.allowed_updates is not None:
            data['allowed_updates'] = args.allowed_updates

        return self.get('getUpdates', args=data)


def parse_args():
    parser = argparse.ArgumentParser(description='Simple Telegram Bot API Client')
    parser.add_argument('--endpoint', help='Telegram API endpoint', default='https://api.telegram.org')
    parser.add_argument('--token', help='Telegram Bot Token', required=True)
    parser.add_argument('--verbose', help='Verbose output', default=False, action='store_true')
    command_parser = parser.add_subparsers(help='Command')

    sendmessage_parser = command_parser.add_parser('sendMessage')
    sendmessage_parser.set_defaults(command='sendMessage')
    sendmessage_parser.add_argument('--chat-id', help='unique identifier for the target chat or username of the target channel', required=True)
    sendmessage_parser.add_argument('--text', help='text of the message to be sent', required=True)
    parsemode_parser = sendmessage_parser.add_mutually_exclusive_group()
    parsemode_parser.set_defaults(parse_mode=None)
    parsemode_parser.add_argument('--html', dest='parse_mode', const='html', action='store_const', help='text uses HTML formatting')
    parsemode_parser.add_argument('--markdown', dest='parse_mode', const='markdown', action='store_const', help='text uses Markdown formatting')
    sendmessage_parser.add_argument('--disable-web-page-preview', action='store_true', default=False, help='disable link previews for links in this message')
    sendmessage_parser.add_argument('--disable-notification', action='store_true', default=False, help='send the message silently - users will receive a notification with no sound')
    sendmessage_parser.add_argument('--reply-to-message-id', help='if the message is a reply, ID of the original message')
    sendmessage_parser.add_argument('--reply-markup', help='Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.')

    getupdates_parser = command_parser.add_parser('getUpdates')
    getupdates_parser.set_defaults(command='getUpdates')
    getupdates_parser.add_argument('--offset', help='Identifier of the first update to be returned. Must be greater by one than the highest among the identifiers of previously received updates. By default, updates starting with the earliest unconfirmed update are returned. An update is considered confirmed as soon as getUpdates is called with an offset higher than its update_id. The negative offset can be specified to retrieve updates starting from -offset update from the end of the updates queue. All previous updates will forgotten.')
    getupdates_parser.add_argument('--limit', help='Limits the number of updates to be retrieved. Values between 1-100 are accepted. Defaults to 100.')
    getupdates_parser.add_argument('--timeout', help='Timeout in seconds for long polling. Defaults to 0, i.e. usual short polling. Should be positive, short polling should be used for testing purposes only.')
    getupdates_parser.add_argument('--allowed-updates', help='List the types of updates you want your bot to receive. For example, specify ["message", "edited_channel_post", "callback_query"] to only receive updates of these types. See Update for a complete list of available update types. Specify an empty list to receive all updates regardless of type (default). If not specified, the previous setting will be used. Please note that this parameter doesn\'t affect updates created before the call to the getUpdates, so unwanted updates may be received for a short period of time.')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    if args.verbose:
        print(args)

    telegrambot = TelegramBot(args.endpoint, args.token, verbose=args.verbose)
    if args.command == 'sendMessage':
        telegrambot.sendMessage(args)
    elif args.command == 'getUpdates':
        _, response_text = telegrambot.getUpdates(args)
        print(pretty_json(response_text))
    else:
        raise NotImplementedError()
