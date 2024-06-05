import re
from django.core.management.base import BaseCommand

from claude import claude_client
from claude import claude_wrapper

from utils.api import Biid, Masterkala
from utils.content import generate_prompt

from db.models import Product
import datetime
import time

# to in file ma description darim ke ba estefade as ketabkhone claude-api-py in karo anjam mide
# ma as api estefade nemikonim bejash as cookie estefade mikonim as moshkeli to estefade as ketabkhone dashti mitoni as to github search koni
# in code faghat kalahaye to db ro mored estefade gharar mide
# ma bekhater mahdodiyat haye estefade as claude be ezaye ye tedad pardazesh sleep dadim ta account ban nash
# ma dar inja time daghigh pardazesh ro save mikonim

class Command(BaseCommand):
    def add_arguments(self, parser):
         parser.add_argument("--use_proxy", action='store_true')

    def handle(self, *args, **options):


        b = Biid()
        mk = Masterkala()

        cookies = "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"

        client = claude_client.ClaudeClient(cookies)

        organizations = client.get_organizations()
        claude_obj = claude_wrapper.ClaudeWrapper(client, organization_uuid=organizations[0]['uuid'])
        new_conversation_data = claude_obj.start_new_conversation("New Conversation" ,"hi claude")
        conversation_uuid = new_conversation_data['uuid']
        # You can get the response from the initial message you sent with:
        initial_response = new_conversation_data['response']
        # You can get the title of the new chat you created with this:
        chat_title = new_conversation_data['title']

        x = 1
        
        while True:
            time.sleep(43200)
            for product in b.get_products(page=1):
                try:
                    product_detail = b.get_product(product['id'])
                    if (not product_detail['description']) and (Product.objects.get(id=int(product['id'])).identifier):
                        identifier = str(Product.objects.get(id=int(product['id'])).identifier)
                        mk_product = mk.get_product_details(identifier)

                        if not int(mk_product["info"]['quantity']):
                            print(f"product id={product_detail['id']} ignored because is out of stock")
                            continue

                        mk_product_description = re.sub(r"<b class='highlight'>[\s\S]*<\/b>", '',
                                                        mk_product['info']['description'])
                        mk_product_description = re.sub(r"\n|\r|\t", '', mk_product_description)

                        prompt = generate_prompt(product=mk_product['info']['name'], description=mk_product_description)

                        try:
                            response = claude_obj.send_message(prompt, conversation_uuid=conversation_uuid)
                        except Exception as e:
                            print(f"ERROR: {e}")
                            continue
                        response = re.sub(r"\n|\r|\t", '', response['completion'])
                        description_match = re.search(r"<response>([\s\S]*)<\/response>", response)
                        if not description_match:
                            print(f"can't  produce description for product id={product_detail['id']} ")
                            continue
                        description = description_match[1]
                        b.update_product(product_detail['id'], {'description': description})
                        print(f"description for product id={product_detail['id']} produced successfully")
                        p = Product.objects.get(id=int(product['id']))
                        p.composed_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        p.save()
                        if x % 6 == 0:
                            new_conversation_data = claude_obj.start_new_conversation("New Conversation", "hi claude")
                            conversation_uuid = new_conversation_data['uuid']
                        if x == 24:
                            time.sleep(21600)
                            x = 0
                        print(x)
                except:
                    pass

    

