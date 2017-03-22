import os
import sys
import json

import requests
from flask import Flask, request
import feedparser
import re
import math
import opengraph
import random
import urllib2
from newspaper import Article

app = Flask(__name__)
# Current user preferences
dictionary = dict()
# Payload string
payloadFinal = ""
# Dictionary to contain info about the news. title = {link : image}
dictOfNews = dict()
ultraDictOfNews = dict()

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text
                    if (message_text.isdigit() and int(message_text) <= 5):
                        send_message(sender_id, "You have %s minutes to read? That's short! Anyway, here you go!" % message_text)
                        log("value of payload final is {payload}".format(payload = payloadFinal))
                        result = send_feed(payloadFinal, int(message_text))
                        send_message(sender_id, "Alright, you'll be able to finish this article within the amount of time you've chosen! Title: %s" % result)
                        # To fix sending the generic template
                        # send_generic_template(sender_id)
                    elif (message_text.isdigit() and int(message_text) <= 10 and int(message_text) > 5):
                        send_message(sender_id, "Alright, get ready for a long read!")
                        log("value of payload final is {payload}".format(payload = payloadFinal))
                        result = send_feed(payloadFinal, int(message_text))
                        send_message(sender_id, "Alright, you'll be able to finish this article within the amount of time you've chosen! Title: %s" % result)
                    else:
                        send_message(sender_id, "Sorry, I didn't understand you! :(")

                elif messaging_event.get("delivery"):  # delivery confirmation
                    pass

                elif messaging_event.get("optin"):  # optin confirmation
                    pass

                elif messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    received_postback(messaging_event)

                else:
                    log("Webhook return unknown event " + messaging_event)

    return "ok", 200


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
def received_postback(event):

    sender_id = event["sender"]["id"]
    recipient_id = event["recipient"]["id"]

    payload = event["postback"]["payload"]
    log("received postback from {recipient} with payload {payload}".format(recipient = recipient_id, payload = payload))

    if payload == "Get Started":
        send_message(sender_id, "Welcome to NewsBot! Choose some topics that you're interested in!")
        send_postback_button(sender_id)

    elif payload == "Tech":
        # Defines the current key value as 0
        payloadFinal = payload
        dictionary[payloadFinal] = 0
        send_message(sender_id, "Choose how much time you have to read!")

    elif payload == "Politics":
        payloadFinal = payload
        dictionary[payloadFinal] = 0
        send_message(sender_id, "Choose how much time you have to read!")

    elif payload == "Global Affairs":
        payloadFinal = re.sub(r"\s", "+", payload)
        dictionary[payloadFinal] = 0
        send_message(sender_id, "Choose how much time you have to read!")

    else:
        send_message(sender_id, "Postback recieved")

# TODO: Fix up this method call to send carousels as well.
def send_generic_template(recipient_id, array):
    log("sending postback message to {recipient}".format(recipient = recipient_id))
    data = json.dumps({
      "recipient": {
        "id": recipient_id
      },
      "message": {
        "attachment": {
          "type": "template",
          "payload": {
            "template_type": "generic",
            "elements": [
              {
                "title": "Your Tech News",
                "image_url": "https://petersfancybrownhats.com/company_image.png",
                "subtitle": "Find out more about the latest tech",
                "default_action": {
                  "type": "web_url",
                  "url": "https://peterssendreceiveapp.ngrok.io/view?item=103",
                  "messenger_extensions": true,
                  "webview_height_ratio": "tall",
                  "fallback_url": "https://peterssendreceiveapp.ngrok.io/"
                },
                "buttons": [
                  {
                    "type": "web_url",
                    "url": "https://petersfancybrownhats.com",
                    "title": "View Article"
                  },
                  {
                    "type": "postback",
                    "title": "Lets talk!",
                    "payload": "talk"
                  }
                ]
              }
            ]
          }
        }
      }
    })
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def send_postback_button(recipient_id):
    log("sending postback message to {recipient}".format(recipient = recipient_id))
    data = json.dumps({
        "message": {
            "attachment": {
                "payload": {
                    "buttons": [
                    {   
                        "payload": "Tech",
                        "type": "postback",
                        "title": "Tech"
                    },
                {
                    "payload": "Politics",
                    "title": "Politics",
                    "type": "postback"
                }, 
                { "payload": "Global Affairs",
                  "title": "Global Affairs",
                  "type": "postback"
                },
            ],
            "template_type": "button",
            "text": "What categories are you interested in?"
          },
          "type": "template"
        }
      },
      "recipient": {
        "id": recipient_id
      }
    })
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def read_time(link):
    articleLink = Article(link)
    articleLink.download()
    articleLink.parse()
    articleText = articleLink.text
    splitText = articleText.strip().split(" ")
    if (len(splitText) <= 275.0):
        return 1.0
    else:
        answer = math.ceil(len(articleText) / 275.0)
        return answer
# TODO: Update send_feed with new entries for the post (currently 0 is placeholder for image values (fix regex)
def send_feed(payload, timeToRead):
    rssFeed = feedparser.parse("https://news.google.com/news/section?q=%s&output=rss" % payload)
    for post in rssFeed.entries:
        totalRead = read_time(post.link)
        if (totalRead <= timeToRead):
            try:
                imageURL = opengraph.OpenGraph(post.link)['image']
            except urllib2.HTTPError:
                imageURL = 0
            ultraDictOfNews[post.title] = {'time':answer, 'image':imageURL, 'link':post.link}
    randomKey = random.choice(ultraDictOfNews.keys())
    linkToArticle = ultraDictOfNews[randomKey]['link']
    stringResult = "This article is %.1f minutes: %s (Link: %s)" % (ultraDictOfNews[randomKey]['time'], randomKey, linkToArticle )
    del ultraDictOfNews[randomKey]
    return stringResult

def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)