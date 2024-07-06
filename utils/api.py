import json
import logging
from lxml import etree

from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
from requests import HTTPError

from utils.config import configs
from utils.request import BaseRequests

class Biid(BaseRequests):
    TOKEN = configs.get('biid_token')
    BASE_URL = 'https://biid.shop/api/management/v1'

    def __init__(self):
        super(Biid, self).__init__()
        self.session = requests.Session()
        self._login()

    def _login(self):
        driver = webdriver.Firefox()
        driver.get("https://biid.shop/admin/login/")
        driver.implicitly_wait(100)

        username = driver.find_element(By.XPATH, "/html/body/div[1]/div/form/div[1]/input")
        username.clear()
        username.send_keys(configs.get('biid_username'))

        password = driver.find_element(By.XPATH, "/html/body/div[1]/div/form/div[2]/input")
        password.clear()
        password.send_keys(configs.get('biid_password'))

        login_btn = driver.find_element(By.XPATH, "/html/body/div[1]/div/form/button")
        login_btn.click()
        cookies = driver.get_cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        self.cookies = cookies_dict
        driver.close()



    @property
    def _headers(self):
        headers = {
            'authority': 'biid.shop',
            'accept': 'application/json',
            'accept-language': 'en,fa;q=0.9',
            'cache-control': 'max-age=0',
            'cookie': configs.get('biid_cookie'),
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-user': '?1',
            'service-worker-navigation-preload': 'true',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        }
        return headers

    @property
    def headers(self):
        headers = {
            "Authorization": f"Api-Key {self.TOKEN}",
            "content_type": "application/json",
        }
        return headers

#   not finish
    def get_products(self, page=1):

        next_url = f"{self.BASE_URL}/products/?page={page}"
        while next_url:
            logging.warning(next_url)
            next_url = next_url.replace('http://', 'https://')
            response = requests.get(next_url, headers=self._headers , cookies=self.cookies)
            data = response.json()
            next_url = data.get('next')
            for product in data['result']:
                yield product

    def get_product(self, product_id):
        url = f"{self.BASE_URL}/products/{product_id}/"
        response = requests.get(url, headers=self._headers , cookies=self.cookies)

        product = response.json()
        return product

    def get_product_variants(self, product_id):
        url = f"{self.BASE_URL}/products/{product_id}/variants/"
        response = requests.get(url, headers=self._headers , cookies=self.cookies )
        try:
            data = response.json()
            return data['result']
        except:
            pass

    def remove_product_variant(self, product_id, variant_id):
        url = f"{self.BASE_URL}/products/{product_id}/variants/{variant_id}/"
        response = requests.delete(url, headers=self.headers , cookies=self.cookies)
        return response

    def remove_product(self, product_id):
        url = f"{self.BASE_URL}/products/{product_id}/"
        response = self.delete(url, headers=self.headers , cookies=self.cookies)
        return response

    def update_product_variant(self, product_id, variant_id, updates):
        url = f"{self.BASE_URL}/products/{product_id}/variants/{variant_id}/"
        response = requests.put(
            url,
            headers=self.headers,
            json=updates,
            cookies=self.session.cookies
        )
        return response

    def add_product_attribute(self, product_id, attribute, value):
        url = f"{self.BASE_URL}/products/{product_id}/attributes/secondary/"
        payload = {"attribute": attribute, "value": value}
        response = requests.post(
            url,
            headers=self.headers,
            data=payload,
            cookies=self.session.cookies
        )
        return response

    def get_images(self, product_id):
        url = f"{self.BASE_URL}/products/{product_id}/images/"
        response = requests.get(url, headers=self._headers , cookies=self.cookies)
        data = response.json()
        images = data['result']
        return images

    def update_image(self, product_id, image_id, updates):
        url = f"{self.BASE_URL}/products/{product_id}/images/{image_id}/"
        response = requests.put(url, headers=self.headers, json=updates , cookies=self.session.cookies)
        return response.json()

    def remove_image(self, product_id, image_id):
        url = f"{self.BASE_URL}/products/{product_id}/images/{image_id}/"
        response = requests.delete(url, headers=self.headers , cookies=self.session.cookies)
        return response

    def get_categories(self):
        url = f"{self.BASE_URL}/categories/"
        response = requests.get(url , headers=self._headers , cookies=self.cookies)
        return response.json()

    def add_category(self , category):
        url = f"{self.BASE_URL}/categories/"
        response = requests.post(url , headers=self.headers , json=category , cookies=self.session.cookies)
        return response

    def add_tag(self , product_id , value):
        url = f'{self.BASE_URL}/products/{product_id}/tags/'
        tag = {
            'pk': product_id,
            'value': value[0:64]
        }
        response = requests.post(url , headers=self.headers , json=tag , cookies=self.session.cookies)
        return response

    def add_product(self, product , categories , brand):
        url = f"{self.BASE_URL}/products/"
        cat_id = 0
        res = False
        parent = 2
        for category in categories:
            for cat in self.get_categories()['result']:
                if cat['name'] == category:
                    parent = int(cat['id'])
                    res = True
            if res == False:
                cat_j = {
                    "name" : f"{category}",
                    'parent' : parent,
                }
                x = self.add_category(cat_j)
                parent = int(x.json()['id'])
            res = False


            
        product['main_category'] = parent


        res = False
        for bra in self.get_brands()['result']:
            if bra['name'] == brand:
                bra_id = int(bra['id'])
                res = True
        if res == False:
            bra_j = {
                "name":f"{brand}"    
            }
            x = self.add_brand(bra_j)
            bra_id = int(x.json()['id'])

        product['brand'] = bra_id


        
        response = requests.post(
            url,
            headers=self.headers,
            json=product,
            cookies=self.session.cookies
        )
        data = response.json()
        product_id = data['id']
        return product_id

    def update_product(self, product_id, updates):
        url = f"{self.BASE_URL}/products/{product_id}/"

        response = requests.put(
            url,
            headers=self.headers,
            json=updates,
            cookies=self.session.cookies
        )

        return response

    def update_price(self, product_id, price):
        updates = {"price": int(price), "compare_at_price": int(price * 1.18)}
        return self.update_product(product_id, updates)

    def set_product_out_of_stock(self, product_id):
        updates = {"stock_type": "out_of_stock", "stock": 0}
        return self.update_product(product_id, updates)

    def set_product_stock(self, product_id, stock):
        updates = {"stock_type": "limited", "stock": stock}
        return self.update_product(product_id, updates)

    def add_image_to_product(self, product_id, image_url, image_alt):
        url = f"{self.BASE_URL}/products/{product_id}/images/"
        response = requests.post(
            url,
            headers=self.headers,
            data={"image_url": image_url, "image_alt": image_alt},
            cookies=self.session.cookies
        )
        return response

    def add_colors_to_product(self, product_id, colors):
        url = f"{self.BASE_URL}/products/{product_id}/attributes/main/"

        try:
            response = requests.post(
                url,
                headers=self.headers,
                data={"attribute": "رنگ", "value": colors},
                cookies=self.session.cookies
            )
            return response
        except:
            return False

    def remove_colors_from_product(self, product_id):
        attribute = 'رنگ'
        url = f"{self.BASE_URL}/products/{product_id}/attributes/main/{attribute}/"

        try:
            response = requests.delete(
                url,
                headers=self.headers,
                cookies=self.session.cookies
            )
            return True
        except HTTPError:
            return False

    def get_brands(self):
        url = f"{self.BASE_URL}/brands/"
        response = requests.get(
            url,
            headers=self.headers,
            cookies=self.session.cookies
            )
        return response.json()

    def add_brand(self , name):
        url = f"{self.BASE_URL}/brands/"

        response = requests.post(
            url,
            json = name,
            headers=self.headers,
            cookies=self.session.cookies
            )

        return response


class Masterkala(BaseRequests):
    TOKEN = configs.get('masterkala_token')
    BASE_URL = "https://masterkala.com/api/2.1.1.0.0/?route=third_party"
    IMAGE_BASE_URL = "https://masterkala.com/image"

    @property
    def headers(self):
        return {
            "token": self.TOKEN,
            "content_type": "text/plain"
        }

    def get_product_attributes(self, product_id):
        url = f"https://masterkala.com/api/2.1.1.0.0/?route=product/getproductattribute"

        data = {
            "productids": [
                str(product_id)
            ],
            "compare": "0"
        }

        response =requests.post(url, json=data)
        data = response.json()
        return data[0]['list']

    def get_product_details(self, product_id):
        url = f'https://masterkala.com/api/2.1.1.0.0/?route=product/getproductdetail&t={product_id}'
        data = f'{{"productid": {product_id}}}'
        response = self.post(url, data=data)
        data = response.json()
        return data

    @staticmethod
    def is_used_product(product_details):
        for tag in product_details['tags']:
            try:
                if tag['text'] in ['دارای ایراد ظاهری', 'جعبه آسیب دیده', 'دارای ایراد جزئی', 'دارای ایراد فنی']:
                    return True
            except:
                return False

    def get_products(self, page=1):
        url = f"{self.BASE_URL}/all_products"
        product_exists = True
        while product_exists:
            response = self.post(
                url,
                headers=self.headers,
                data=f'{{"page": {page}}}',
            )
            logging.warning(f'masterkala page: {page}')
            page += 1
            data = response.json()
            products = data['list']
            if not products:
                product_exists = False
            for product in products:
                assert product.get('product_id')
                product_details = self.get_product_details(product['product_id'])
                if self.is_used_product(product_details):
                    continue
                yield product

    def get_product(self, product_id=None, model=None):
        url = f"{self.BASE_URL}/product_detail"
        response = requests.post(
            url,
            headers=self.headers,
            data=f'{{"product_id":"{product_id}", "model":"{model}"}}'.encode("utf-8"),

        )
        product = response.json()
        assert product.get('product_id')
        return product
