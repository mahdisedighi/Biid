import datetime
import json
import os
import re
import time
import uuid
import pytz

import requests as req
from curl_cffi import requests


class Client:

    def __init__(self, cookies, proxies=None):
        self.proxies = proxies
        self.timezone = 'BST'  # 'America/Toronto'
        self.cookies = cookies
        self.cookies_resets_at = [datetime.datetime.now().astimezone() for cookie in cookies]
        self.cookie_index = 0
        self.organization_id = self.get_organization_id()

    @property
    def cookie(self):
        return self.cookies[self.cookie_index]['cookie']

    def switch_account(self, current_resets_at=1735689600):
        print(current_resets_at)
        dt_unaware = datetime.datetime.utcfromtimestamp(current_resets_at)
        dt_aware = pytz.timezone(self.timezone).localize(dt_unaware).astimezone()
        self.cookies_resets_at[self.cookie_index] = dt_aware

        resets_at = min(self.cookies_resets_at)
        print('resets ats: ', [str(item) for item in self.cookies_resets_at])
        print('closest resets at:', resets_at)

        while resets_at > datetime.datetime.now().astimezone():
            wait_timedelta = resets_at - datetime.datetime.now().astimezone()
            print(f'waiting: {wait_timedelta}')
            time.sleep(wait_timedelta.total_seconds() + 1)

        self.cookie_index = self.cookies_resets_at.index(resets_at)
        print(f"switched to cookie {self.cookie_index}")
        self.organization_id = self.get_organization_id()

    def get_organization_id(self):
        url = "https://claude.ai/api/organizations"

        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://claude.ai/chats',
            'Content-Type': 'application/json',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Connection': 'keep-alive',
            'Cookie': f'{self.cookie}'
        }

        response = requests.get(url, headers=headers,proxies=self.proxies, impersonate="chrome110")
        print(response)
        if response.status_code == 403:
            print(response.json())
            print(self.cookies[self.cookie_index]['username'], 'expired!')
            return self.switch_account()
        res = response.json()
        uuid = res[0]['uuid']

        return uuid

    def get_content_type(self, file_path):
        # Function to determine content type based on file extension
        extension = os.path.splitext(file_path)[-1].lower()
        if extension == '.pdf':
            return 'application/pdf'
        elif extension == '.txt':
            return 'text/plain'
        elif extension == '.csv':
            return 'text/csv'
        # Add more content types as needed for other file types
        else:
            return 'application/octet-stream'

    # Lists all the conversations you had with Claude
    def list_all_conversations(self):
        url = f"https://claude.ai/api/organizations/{self.organization_id}/chat_conversations"

        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://claude.ai/chats',
            'Content-Type': 'application/json',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Connection': 'keep-alive',
            'Cookie': f'{self.cookie}'
        }

        response = requests.get(url, headers=headers,proxies=self.proxies ,impersonate="chrome110")
        conversations = response.json()

        # Returns all conversation information in a list
        if response.status_code == 200:
            return conversations
        else:
            print(f"Error: {response.status_code} - {response.text}")

    # Send Message to Claude
    def send_message(self, prompt, conversation_id, attachment=None, timeout=500):
        url = "https://claude.ai/api/append_message"

        # Upload attachment if provided
        attachments = []
        if attachment:
            attachment_response = self.upload_attachment(attachment)
            if attachment_response:
                attachments = [attachment_response]
            else:
                return {"Error: Invalid file format. Please try again."}

        # Ensure attachments is an empty list when no attachment is provided
        if not attachment:
            attachments = []

        payload = json.dumps({
            "completion": {
                "prompt": f"{prompt}",
                "timezone": self.timezone,
                "model": "claude-2"
            },
            "organization_uuid": f"{self.organization_id}",
            "conversation_uuid": f"{conversation_id}",
            "text": f"{prompt}",
            "attachments": attachments
        })

        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'text/event-stream, text/event-stream',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://claude.ai/chats',
            'Content-Type': 'application/json',
            'Origin': 'https://claude.ai',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Cookie': f'{self.cookie}',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'TE': 'trailers'
        }

        response = requests.post(url, headers=headers, data=payload,proxies=self.proxies ,impersonate="chrome110",
                                 timeout=500)
        print(response)
        decoded_data = response.content.decode("utf-8")
        print(decoded_data)

        if "too_many_completions" in decoded_data:
            error = json.loads(decoded_data)
            resets_at = error['error']['resets_at']
            self.switch_account(current_resets_at=resets_at)
            return self.send_message(prompt=prompt, conversation_id=self.create_new_chat()['uuid'],
                                     attachment=attachment,
                                     timeout=timeout)

        decoded_data = re.sub('\n+', '\n', decoded_data).strip()
        print(decoded_data)
        data_strings = decoded_data.split('\n')
        print(data_string)
        completions = []
        for data_string in data_strings:
            json_str = data_string[6:].strip()
            data = json.loads(json_str)
            if 'completion' in data:
                completions.append(data['completion'])

        answer = ''.join(completions)

        # Returns answer
        return answer

    # Deletes the conversation
    def delete_conversation(self, conversation_id):
        url = f"https://claude.ai/api/organizations/{self.organization_id}/chat_conversations/{conversation_id}"

        payload = json.dumps(f"{conversation_id}")
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/json',
            'Content-Length': '38',
            'Referer': 'https://claude.ai/chats',
            'Origin': 'https://claude.ai',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Connection': 'keep-alive',
            'Cookie': f'{self.cookie}',
            'TE': 'trailers'
        }

        response = requests.delete(url, headers=headers, data=payload,proxies=self.proxies , impersonate="chrome110")

        # Returns True if deleted or False if any error in deleting
        if response.status_code == 204:
            return True
        else:
            return False

    # Returns all the messages in conversation
    def chat_conversation_history(self, conversation_id):
        url = f"https://claude.ai/api/organizations/{self.organization_id}/chat_conversations/{conversation_id}"

        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://claude.ai/chats',
            'Content-Type': 'application/json',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Connection': 'keep-alive',
            'Cookie': f'{self.cookie}'
        }

        response = requests.get(url, headers=headers,proxies = self.proxies, impersonate="chrome110")

        # List all the conversations in JSON
        return response.json()

    def generate_uuid(self):
        random_uuid = uuid.uuid4()
        random_uuid_str = str(random_uuid)
        formatted_uuid = f"{random_uuid_str[0:8]}-{random_uuid_str[9:13]}-{random_uuid_str[14:18]}-{random_uuid_str[19:23]}-{random_uuid_str[24:]}"
        return formatted_uuid

    def create_new_chat(self):
        url = f"https://claude.ai/api/organizations/{self.organization_id}/chat_conversations"
        uuid = self.generate_uuid()

        payload = json.dumps({"uuid": uuid, "name": ""})
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://claude.ai/chats',
            'Content-Type': 'application/json',
            'Origin': 'https://claude.ai',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Cookie': self.cookie,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'TE': 'trailers'
        }

        response = requests.post(url, headers=headers,proxies = self.proxies, data=payload, impersonate="chrome110")
        
        # Returns JSON of the newly created conversation information
        return response.json()

    # Resets all the conversations
    def reset_all(self):
        conversations = self.list_all_conversations()

        for conversation in conversations:
            conversation_id = conversation['uuid']
            delete_id = self.delete_conversation(conversation_id)

        return True

    def upload_attachment(self, file_path):
        if file_path.endswith('.txt'):
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_type = "text/plain"
            with open(file_path, 'r', encoding='utf-8') as file:
                file_content = file.read()

            return {
                "file_name": file_name,
                "file_type": file_type,
                "file_size": file_size,
                "extracted_content": file_content
            }
        url = 'https://claude.ai/api/convert_document'
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://claude.ai/chats',
            'Origin': 'https://claude.ai',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Connection': 'keep-alive',
            'Cookie': f'{self.cookie}',
            'TE': 'trailers'
        }

        file_name = os.path.basename(file_path)
        content_type = self.get_content_type(file_path)

        files = {
            'file': (file_name, open(file_path, 'rb'), content_type),
            'orgUuid': (None, self.organization_id)
        }

        response = req.post(url, headers=headers, files=files)
        if response.status_code == 200:
            return response.json()
        else:
            return False

    # Renames the chat conversation title
    def rename_chat(self, title, conversation_id):
        url = "https://claude.ai/api/rename_chat"

        payload = json.dumps({
            "organization_uuid": f"{self.organization_id}",
            "conversation_uuid": f"{conversation_id}",
            "title": f"{title}"
        })
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/json',
            'Referer': 'https://claude.ai/chats',
            'Origin': 'https://claude.ai',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Connection': 'keep-alive',
            'Cookie': f'{self.cookie}',
            'TE': 'trailers'
        }

        response = requests.post(url, headers=headers,proxies = self.proxise , data=payload, impersonate="chrome110")

        if response.status_code == 200:
            return True
        else:
            return False
