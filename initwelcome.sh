#!/bin/bash

# initwelcome.sh: sets welcome screen
# Execute once only

if [ ! -f access_token ]; then
    echo "Error! Please put your Facebook access_token in ./access_token"
    exit 1
fi

ACCESS_TOKEN="$( cat ./access_token )"

# Greeting Text
curl -X POST -H "Content-Type: application/json" -d '{
  "setting_type":"greeting",
  "greeting":{
    "text":"Hello {{user_first_name}}, welcome to NewsBot."
  }
}' "https://graph.facebook.com/v2.6/me/thread_settings?access_token=${ACCESS_TOKEN}"

# Get Started button
curl -X POST -H "Content-Type: application/json" -d '{
  "setting_type":"call_to_actions",
  "thread_state":"new_thread",
  "call_to_actions":[
    {
      "payload":"Get Started"
    }
  ]
}' "https://graph.facebook.com/v2.6/me/thread_settings?access_token=${ACCESS_TOKEN}"