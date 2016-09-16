"""
[
    {
        "name": "!card",
        "args": ["name"],
        "category": "MtG",
        "short_description": "Displays info about a Magic card.",
        "long_description": "Displays information about a card from Magic: The Gathering. Using '[[card_name]]' will also trigger the command.",
        "examples": ["!card storm crow", "[[storm crow]]"]
    }
]
"""

import requests, re
from utils.messaging import create_reply, Slack
from utils.formatting import italics, bold, codeblock, link

CARD_DB_ENDPOINT = "http://api.deckbrew.com/mtg/cards/typeahead"
GATHERER_IMAGE_URL = "http://gatherer.wizards.com/Handlers/Image.ashx?type=card&multiverseid="
GATHERER_INFO_URL = "http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid="

def get_card(query):
    result = {
        "fallback": "Could not display card information",
        "mrkdwn_in": ["text", "pretext", "fields"]
    }
    params = {"q": query}
    card_data = requests.get(CARD_DB_ENDPOINT, params=params).json()
    if not card_data:
        result["text"] = "No card found matching _*" + query + "*_."
        return result
    card = card_data[0]
    non_zero_ids = [edition for edition in card["editions"] if edition["multiverse_id"] != 0]
    gatherer_link = link(GATHERER_INFO_URL + str(non_zero_ids[-1]["multiverse_id"]), card["name"])
    tcgplayer_link = link(card["store_url"], "TCGplayer")
    result["text"] = bold(italics(gatherer_link)) + "  //  " + tcgplayer_link
    result["image_url"] = non_zero_ids[-1]["image_url"]
    return result

def on_message(msg, server):
    # heya
    regex = "\[\[([^\[\]]*)\]\]"
    matches = re.findall(regex, msg["text"])
    if not matches:
        regex = "^!card (.+)$"
        matches = re.findall(regex, msg["text"])
    if not matches:
        return
    attachments = []
    for match in matches:
        card_info = get_card(match)
        if card_info:
            attachments.append(card_info)

    slack = Slack(msg, server)
    slack.api_postmessage(text="Magic card(s):", attachments=attachments)
    return
