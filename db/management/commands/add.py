import datetime
from django.core.management.base import BaseCommand
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from db.models import Product ,Type_Product
from utils.api import Biid, Masterkala
from utils.convert import masterkala_to_biid, hash_product
import json

# in code baraye add product az masterkala be biid shop estafade mishe
# ma tamame moshakhati ke to masterkalamored estefade anjam mise ro be biid shop ovordim
# bade ezafe kardan mahsole be biid shop ma time ezafe kardan oon ma sayer moshakasate kala ro be db ezafe mokonim


class Command(BaseCommand):

    @staticmethod
    def product_exists(masterkala_product):
        try:
            Product.objects.get(identifier=int(masterkala_product['product_id']))
            return True
        except:
            return False

    def handle(self, *args, **options):

        mk = Masterkala()
        b = Biid()

        for masterkala_product_short in mk.get_products():
            try:
                if self.product_exists(masterkala_product_short):
                    print(f"product id={masterkala_product_short['product_id']} already exists")
                    continue

                masterkala_product = mk.get_product(masterkala_product_short['product_id'])
                biid_product, colors = masterkala_to_biid(masterkala_product)

                # *********************************

                if not biid_product['stock']:
                    print(f"product id={masterkala_product_short['product_id']} is out of stock")
                    continue

                masterkala_product_attributes = mk.get_product_attributes(masterkala_product_short['product_id'])
                masterkala_product_details = mk.get_product_details(masterkala_product_short['product_id'])
                images_url = [masterkala_product_details['info']['image']] + [image['image'] for image in
                                                                              masterkala_product_details['images']]
                # images_url = ['https://masterkala.com/image/' + image_url for image_url in images_url]

                if not images_url:
                    print(f"product id={masterkala_product_short['product_id']} has no image")
                    continue

                masterkala_product_id = int(masterkala_product_short['product_id'])

                url = f"https://masterkala.com/product/{masterkala_product_id}"
                driver = webdriver.Firefox()
                driver.get(url)
                driver.implicitly_wait(100)
                typee = driver.find_elements(By.CLASS_NAME, 'v-breadcrumbs__item')

                li = []

                for i in typee:
                    li.append(i.text)
                li.pop(0)

                driver.close()

                brand = masterkala_product['manufacturer_name']
                product_id = b.add_product(biid_product, li, brand)
                p = Product.objects.create(id=product_id,
                                           identifier=masterkala_product['product_id'],
                                           from_masterkala=True,
                                           )

                for image_url in images_url:
                    try:
                        b.add_image_to_product(product_id, image_url=image_url, image_alt=biid_product['name'])
                    except:
                        pass

                for attribute in masterkala_product_attributes:
                    try:
                        b.add_product_attribute(product_id,
                                                attribute=attribute['name'],
                                                value=attribute['text'])
                    except:
                        pass

                b.add_colors_to_product(product_id, colors)
                variants = b.get_product_variants(product_id)
                for variant in variants:
                    b.update_product_variant(product_id, variant['id'], {'product_identifier': biid_product['barcode']})

                value = biid_product['name']
                pro_id = product_id
                b.add_tag(product_id=pro_id, value=value)
                p.commit = True
                p.save()
                print(
                    f"masterkala product id={masterkala_product_short['product_id']} successfully added to biid product id={product_id}")
            except:
                pass
