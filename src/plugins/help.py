"""
[
    {
        "name": "!help",
        "args": ["(command)"],
        "category": "Other",
        "short_description": "The command you used to see this description",
        "long_description": "Gives detailed help documentation for the given command, or a brief overview of all commands if no command is provided.",
        "examples": ["!help", "!help card"]
    }
]
"""

from utils.messaging import Slack
from utils.formatting import at, codeblock, bold, italics, monospace

import json, re

def on_message(msg, server):
    slack = Slack(msg, server)
    match = re.findall('^!help( .*)?$', msg['text'])
    if not match:
        return
    command = match[0].strip().replace('.', '')

    all_help_docs = []
    for mod_name in server.hooks["extendedhelp"]:
        doc_list = json.loads(server.hooks["extendedhelp"][mod_name])
        all_help_docs.extend(doc_list)

    # specific command
    if command:
        doc = [item for item in all_help_docs if command.lower() == item["name"].lower()][0]
        help_str = 'To the rescue!\n'
        output = doc['name']
        arglist = []
        for arg in doc['args']:
            if arg.startswith('('):
                arglist.append('[<' + arg.replace('(', '').replace(')', '') + '>]')
            else:
                arglist.append('<' + arg + '>')
        output += (' ' + ' '.join(arglist) if arglist else '') + '\n\n'
        output += doc['long_description'] + '\n\n'
        output += 'Example usage(s):\n\t' + '\n\t'.join(doc['examples'])
        return at(slack.user_name, help_str + codeblock(output))

    command_lists = {}
    for doc in all_help_docs:
        arglist = []
        for arg in doc['args']:
            if arg.startswith('('):
                arglist.append('[<' + arg.replace('(', '').replace(')', '') + '>]')
            else:
                arglist.append('<' + arg + '>')
        help_str = monospace(doc['name'] + (' ' + ' '.join(arglist) if arglist else ''))
        help_str += ': ' + italics(doc['short_description'])
        if "category" not in doc:
            doc["category"] = "Unspecified"
        if doc["category"] not in command_lists:
            command_lists[doc["category"]] = [help_str]
        else:
            command_lists[doc["category"]].append(help_str)
    bot_reply = "Here is the full list of accepted commands. "
    bot_reply += "Use `.help <command_name>` for details on a specific command.\n>>>"
    for category in sorted(command_lists):
        bot_reply += bold(category) + "\n"
        bot_reply += "\n".join(sorted(command_lists[category])) + "\n"
    return at(slack.user_name, bot_reply)
