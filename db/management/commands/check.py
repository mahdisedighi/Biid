import datetime

from django.core.management.base import BaseCommand
from requests import HTTPError
from tqdm import tqdm
from django.db.models import Q

from db.models import Product
from utils.api import Biid, Masterkala
from utils.convert import masterkala_to_biid, hash_product


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--product_ids", nargs="+", type=int, required=False)

    def handle(self, *args, **options):
	try:
            damaged_products = Product.objects.filter(commit=False)
            for p in damaged_products:
                print(p.id)
        except:
            pass
