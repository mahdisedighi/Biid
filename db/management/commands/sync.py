from django.core.management.base import BaseCommand
from django.db import IntegrityError
from requests import HTTPError
from tqdm import tqdm

from db.models import Product
from utils.api import Biid


class Command(BaseCommand):

    def handle(self, *args, **options):

        b = Biid()
        product_ids = []
        for product_short in tqdm(b.get_products(page=1)):
            if product_short['main_category'] == 2:
                product = b.get_product(product_short['id'])
                try:
                    p, created = Product.objects.get_or_create(
                        id=product['id'],
                        identifier=product['product_identifier'],
                        from_masterkala=True)
                    product_ids.append(p.id)
                except IntegrityError:
                    p_org = Product.objects.get(
                        identifier=product['product_identifier']
                    )
                    print(f"product id={product['id']} is duplicate of product id={p_org.id}")
                if created:
                    print(f"product id={p.id} added to database")
                if not product['product_identifier']:
                    print(f"product id={product['id']} has no identifier")

        products_to_delete = Product.objects.exclude(pk__in=product_ids)

        for p in products_to_delete:
            print(f"product id={p.id} removed from database")
            p.delete()
