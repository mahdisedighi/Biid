import hashlib
import json
import math


def masterkala_to_biid(masterkala_product , before_price=None , main_category=2):

    discount = 15
    pricewithdiscount = int(float(masterkala_product["pricewithdiscount"]))
    if before_price is not None:
        if masterkala_product["super_special"]=="1":
            if pricewithdiscount >= before_price:
                masterkala_price = pricewithdiscount + 100_000
            else:
                masterkala_price = before_price
        else:
            masterkala_price = pricewithdiscount
    else:
        if masterkala_product["super_special"]=="1":
            masterkala_price = pricewithdiscount + 100_000
        else:
            masterkala_price = pricewithdiscount



    if masterkala_price < 2_000_000:
        biid_price = masterkala_price + 70_000
    else:
        biid_price = masterkala_price




    biid_product = {
        "name": masterkala_product["name"],
        "main_category": main_category,
        "price": biid_price,
        "compare_at_price": math.ceil(biid_price * 100 / (100 - discount) / 10000) * 10000,
        "product_identifier": masterkala_product["model"],
        "stock": int(masterkala_product["quantity"]),
        "stock_type": "unlimited" if int(masterkala_product["quantity"]) or (pricewithdiscount > 1_930_000) else "out_of_stock",
        "barcode": masterkala_product["model"]
    }



    colors = []
    for option in masterkala_product["optionlist"]:
        if "رنگ" in option["name"]:
            for color in option["product_option_value"]:
                colors.append(color["name"])
        elif "گارانتی" in option["name"]:
            biid_product["guarantee"] = option["product_option_value"][0]["name"]

    return biid_product, colors , pricewithdiscount


def hash_product(dictionary):
    """MD5 hash of a dictionary."""
    dhash = hashlib.md5()
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()
