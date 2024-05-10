import re
import time

from django.core.management.base import BaseCommand
from claude_api import Client
from utils.api import Biid, Masterkala
from utils.content import generate_prompt


class Command(BaseCommand):

    def handle(self, *args, **options):

        b = Biid()
        mk = Masterkala()

        for biid_product_short in b.get_products(page=1):
            try:
                if (biid_product_short['stock_type'] != 'out_of_stock') and (biid_product_short['main_category'] == 2):
                    biid_product = b.get_product(biid_product_short['id'])
                    mk_product_details = mk.get_product_details(biid_product['product_identifier'])
    
                    images_url = [mk_product_details['info']['image']] + [image['image'] for image in
                                                                          mk_product_details['images']]
                    images_url = ['https://masterkala.com/image/' + image_url for image_url in images_url]
    
                    old_images = b.get_images(biid_product['id'])
    
                    if (len(old_images) == len(images_url)) and (len(images_url) > 1):
                        print(f"product id={biid_product['id']} already has features and images")
                        continue
    
                    mk_product_attributes = mk.get_product_attributes(biid_product['product_identifier'])
    
                    for attribute in mk_product_attributes:
                        try:
                            b.add_product_attribute(biid_product['id'], attribute=attribute['name'],
                                                    value=attribute['text'])
                        except Exception as e:
                            if 'Conflict' in str(e):
                                print(f"product id={biid_product['id']} already has \"{attribute['name']}\"")
                            elif 'Bad Request' in str(e):
                                print(
                                    f"product id={biid_product['id']} - value for field \"{attribute['name']}\" is not valid")
                            else:
                                print(e)
                                raise e

                    for old_image in old_images:
                        b.remove_image(biid_product['id'], old_image['id'])

                    for image_url in images_url:
                        try:
                            b.add_image_to_product(biid_product['id'], image_url=image_url, image_alt=biid_product['name'])
                        except Exception as e:
                            if 'Bad Request' in str(e):
                                print(
                                    f"product id={biid_product['id']} - image \"{image_url}\" is not valid")
                            else:
                                print(e)
                                raise e

                    print(f"images and features for product id={biid_product['id']} added successfully")

            except:
                continue
