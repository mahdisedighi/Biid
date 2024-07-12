############################################################################
## Django ORM Standalone Python Template
############################################################################
""" Here we'll import the parts of Django we need. It's recommended to leave
these settings as is, and skip to START OF APPLICATION section below """

# Turn off bytecode generation
import sys
sys.dont_write_bytecode = True

# Django specific settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject99.settings')
import django
django.setup()

# Import your models for use in your script
from db.models import *
from utils.api import Masterkala
############################################################################
## START OF APPLICATION
############################################################################
""" Replace the code below with your own """

if __name__ == '__main__':
    ma = Masterkala()
    p = ma.get_product(985)
    print(p)