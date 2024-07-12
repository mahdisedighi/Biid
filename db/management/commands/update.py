import datetime

from django.core.management.base import BaseCommand
from requests import HTTPError
from tqdm import tqdm
from django.db.models import Q

from db.models import Product
from utils.api import Biid, Masterkala
from utils.convert import masterkala_to_biid, hash_product

# in file gharare kare update to anjam bede
# ma dar ebteda moshkel update gheymat ro dashtim ke dar in rabete ma bayad be type kala deghat konim chon har kala tanavo mokhtalefi dare
# dar enteha bayad behet bagem ke ma time update ro save mikonim ke mitoni to db bebini
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--product_ids", nargs="+", type=int, required=False)
        parser.add_argument("--update_all", action='store_true')

    def handle(self, *args, **options):

        mk = Masterkala()
        b = Biid()
        now = datetime.datetime.now()
        period = datetime.timedelta(hours=0)
        checkpoint = now - period
        queryset = Product.objects.filter(
            Q(synced_at__lt=checkpoint) | Q(synced_at__isnull=True),
            from_masterkala=True,
            deleted=False)

        if options["product_ids"]:
            queryset = queryset.filter(pk__in=options["product_ids"])

        for product_object in tqdm(list(queryset), desc='updating'):
            try:
                before_price = b.get_product(product_object.id)['price']
                main_category = b.get_product(product_object.id)['main_category']
                masterkala_product = mk.get_product(product_object.identifier)
                
                biid_product, colors = masterkala_to_biid(masterkala_product, before_price = before_price , main_category=main_category)
                
                
                if biid_product["stock"]:
                    if int(float(masterkala_product["pricewithdiscount"])) < 1_930_000:
                        biid_product['stock'] = 0
                        biid_product['stock_type'] = 'out_of_stock'
                                                
                        
                product_hash = hash_product(biid_product)
                if (product_object.product_hash == product_hash) and not options['product_ids']:
                    continue

                product_object.commit = False
                product_object.save()

                update_keys = ['stock', 'stock_type', 'product_identifier','price', 'compare_at_price']

                biid_updates = {key: biid_product[key] for key in update_keys}

                try:
                    b.get_product(product_object.id)
                except HTTPError as e:
                    if '404 Client Error' in str(e):
                        print(f"product id={product_object.id} deleted")
                        product_object.delete()
                        continue

                b.remove_colors_from_product(product_object.id)
                
                variants = b.get_product_variants(product_object.id)
    
                for variant in variants:
                    b.remove_product_variant(product_object.id, variant['id'])


                b.update_product(product_object.id, biid_updates)

                if colors:
                    b.add_colors_to_product(product_object.id, colors)
                

                variants = b.get_product_variants(product_object.id)
                for variant in variants:
                    b.update_product_variant(product_object.id, variant['id'],
                                                 {'product_identifier': biid_product['barcode'] , "price" : biid_product['price'] , 'compare_at_price': biid_product['compare_at_price'] })
        
            


                
                time =datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                product_object.synced_at = time
                product_object.updated_at = time
                product_object.product_hash = product_hash
                product_object.commit = True
                product_object.save()
                print(f"update succesfuly {product_object.id}")
            except:
                continue
