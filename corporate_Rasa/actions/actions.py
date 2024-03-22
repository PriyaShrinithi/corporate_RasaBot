# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa.shared.core.events import UserUtteranceReverted
from rasa_sdk.events import SlotSet, FollowupAction
import openai
import os

class ValidateRoleWritForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_role_writ_form"

    def validate_job_role(self,
        slot_value: Any, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict[Text, Any])->Dict[Text, Any]:

        valid_job_role = ['manager', 'team lead', 'employee']
        job_role = slot_value.lower()
        if not job_role or job_role not in valid_job_role: 
            dispatcher.utter_message(response = "utter_ask_job_role")
            if not job_role:
                job_role = None
        print("job_role: ", job_role)
        return {'job_role': job_role}

    def validate_writ_comm(self,
        slot_value: Any, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict[Text, Any])->Dict[Text, Any]:

        valid_writ_comm = ['mail', 'text message', 'form']
        writ_comm = slot_value.lower()
        if not writ_comm or writ_comm not in valid_writ_comm: 
            dispatcher.utter_message(response = "utter_ask_writ_comm")
            if not writ_comm:
                writ_comm = None
        print("writ_comm: ", writ_comm)
        return {'writ_comm': writ_comm}

    def validate_recipient(self, 
        slot_value: Any, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict[Text, Any])->Dict[Text, Any]:

        valid_recipient = ['peer', 'subordinate', 'superior', 'NA']
        recipient = slot_value.lower() if slot_value else None
        writ_comm = tracker.get_slot('writ_comm')
        print("writ_comm: ", writ_comm)
        if writ_comm == 'mail':
            if not recipient or recipient not in valid_recipient or recipient == 'NA':
                dispatcher.utter_message(response="utter_ask_recipient")
                if not recipient:
                    recipient = None
        else:
            recipient = "NA"
        print("recipient: ", recipient)    
        return {'recipient': recipient}

class ActionGenerateTranslation(Action):
    def name(self) -> Text:
        return "action_generate_translation"

    def run(self, 
            dispatcher: CollectingDispatcher, 
            tracker: Tracker, 
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        #print("all events: ", tracker.events)
        print("all slots: ", tracker.slots)
        
        stanza = str(tracker.latest_message.get('text'))
        print("stanza: ", stanza)
        
        #dispatcher.utter_message(text=f"User said the following: {stanza}")
        job_role = tracker.get_slot('job_role').lower()
        writ_comm = tracker.get_slot('writ_comm').lower()
        recipient = tracker.get_slot('recipient').lower()
        print('writ_comm: ', writ_comm)
        
        stanza_token = len(stanza.split())
        print("stanza_token before conditions: ", stanza_token)
        #token_length = 0
        if writ_comm == 'mail':
            stanza_token = min(stanza_token, 125) + 50
        elif writ_comm == 'text message':
            stanza_token = min(stanza_token, 50) + 15
        elif writ_comm == 'form':
            stanza_token = min(stanza_token, 75) + 25     
        
        print("stanza_token after conditions: ",stanza_token)


        api_key = os.getenv('GPT_API') #should mask this
        if api_key is None:
            print("open ai api key is None")
        else:
            openai.api_key = api_key
        behavior = f"Your response should be strictly less than {stanza_token} words and should be completed to sense. You are a corporate translator and you translate given text in a corporate language. Write the following text in corporate language from the perspective  of a {job_role} in the form of a {writ_comm}"
        if writ_comm == 'mail':
            behavior = behavior + f" to a {recipient}."
        else:
            behavior = behavior+"."
        print(behavior)
        response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                        {"role": "user", "content": stanza},
                        {"role": "system", "content": behavior}
                ],
        )
        print()
        print("response: ",response)
        generated_translation = response.choices[0].message.content
        print()
        print("generated response: ",generated_translation)
        dispatcher.utter_message(text=generated_translation)

        return []