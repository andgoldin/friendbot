""" Functions for abstracting messaging utilities """

import inspect
import re
import traceback
import requests
import json
#import logging

from formatting import at, codeblock, monospace

#LOGGER = logging.getLogger(__name__)
CHANNEL_DEFAULT = "msgchannel"
API_POST_ENDPOINT = "https://slack.com/api/chat.postMessage"


class Slack(object):
    """ Class to hold slack utility functions to be passed into plugins """

    def __init__(self, msg, server):
        self.user_id = msg["user"]
        self.channel_id = msg["channel"]
        self.user_name = server.slack.server.users[self.user_id].name
        if hasattr(server.slack.server, "channels"):
            self.channel_name = server.slack.server.channels[self.channel_id].name
        else:
            self.channel_name = CHANNEL_DEFAULT
        self.server = server

    def send_reply(self, text):
        """ Send a reply given the message information in the object """
        message = at(self.user_name, text=text)
        return self.server.slack.rtm_send_message(self.channel_id, message)

    def send_message(self, channel, text):
        """ Sends a reply message given an existing message """
        channel_id = self.server.slack.server.channels.find(channel).id
        return self.server.slack.rtm_send_message(channel_id, text)

    def api_postmessage(self, channel=None, text=None, attachments=None):
        """ Posts message using Web API """
        if not text and not attachments:
            return
        if not channel:
            channel = self.channel_id
        post_data = {
            "username": "friendbot",
            "token": self.server.slack.token,
            #"token": "xoxp-36640528672-36814676500-37336105063-b0966e49b0",
            "channel": channel
        }
        if text:
            post_data["text"] = text
        if attachments:
            post_data["attachments"] = json.dumps(attachments)
        return requests.post(API_POST_ENDPOINT, params=post_data)


def create_reply(msg, server, mapping, auth_func=None, logging=True):
    """
    Given a mapping of command strings to functions, as well as a message/server objects,
    constructs and returns a reply. It checks if the message's text matches any command,
    and if so, calls the associated function using the extracted parameters, and returns
    the result as the reply. If there is no match, returns None.
    """
    slack = Slack(msg, server)
    channel = slack.channel_name
    user = slack.user_name

    # determine if message text matches the command
    func = None
    params = None
    for item in mapping:
        command = item["command"]
        regex = command[1:] if command.startswith(".") else command
        match = re.findall("^" + regex + "( .*)?$", msg["text"])
        if match:
            func = item["function"]
            params = match[0]
            break
    if not func:
        return

    # actually do the thing
    try:
        # if logging:
        #     user_log(func, channel, user)
        if len(inspect.getargspec(func)[0]) == 1:
            return at(user, func(slack))
        if type(params) is str or type(params) is unicode:
            return at(user, func(slack, params))
        return at(user, func(slack, *params))
    except:
        error_msg = "Error when calling function " + \
            monospace(func.__name__) + ":\n"
        error_msg += codeblock(traceback.format_exc())
        return at(user, error_msg)
