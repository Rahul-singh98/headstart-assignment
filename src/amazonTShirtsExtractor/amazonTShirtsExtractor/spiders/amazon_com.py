import json
import scrapy
from urllib.parse import urljoin
import re

from scrapy.http import Response


class AmazonComSpider(scrapy.Spider):
    name = "amazon.com"
    # allowed_domains = ["www.amazon.com"]
    # start_urls = [
    #     "https://www.amazon.com/s?k=shirts&crid=2Y2ZSKPZDTXTB&sprefix=shirt%2Caps%2C432&ref=nb_sb_noss_1"]

    def start_requests(self):
        keyword_list = ['shirts']
        for keyword in keyword_list:
            amazon_search_url = f'https://www.amazon.com/s?k={keyword}&page=1&crid=2Y2ZSKPZDTXTB&sprefix={keyword}&ref=nb_sb_noss_1'
            yield scrapy.Request(url=amazon_search_url, callback=self.discover_product_urls, meta={'keyword': keyword, 'page': 1})

    def discover_product_urls(self, response):
        page = response.meta['page']
        keyword = response.meta['keyword']

        # Get All Pages
        if page == 1:
            available_pages = response.xpath(
                '//*[contains(@class, "s-pagination-item")][not(has-class("s-pagination-separator"))]/text()'
            ).getall()

            last_page = available_pages[-1]
            for page_num in range(2, int(last_page)):
                amazon_search_url = f'https://www.amazon.com/s?k={keyword}&page={page_num}&crid=2Y2ZSKPZDTXTB&sprefix={keyword}&ref=nb_sb_noss_1'
                yield scrapy.Request(url=amazon_search_url, callback=self.parse_product_data, meta={'keyword': keyword, 'page': page_num})

    def parse_product_data(self, response):
        image_data = json.loads(re.findall(r"s-image", response.text)[0])
        variant_data = re.findall(r'dimensionValuesDisplayData"\s*:\s* ({.+?}),\n', response.text)
        feature_bullets = [bullet.strip() for bullet in response.css("#feature-bullets li ::text").getall()]
        price = response.css('.a-price-whole').get("")
        if not price:
            price = response.css('.a-price .a-offscreen ::text').get("")
        yield {
            "name": response.css("#productTitle::text").get("").strip(),
            "price": price,
            "stars": response.css("i[data-hook=average-star-rating] ::text").get("").strip(),
            "rating_count": response.css("div[data-hook=total-review-count] ::text").get("").strip(),
            "feature_bullets": feature_bullets,
            "images": image_data,
            "variant_data": variant_data,
        }

    def parse(self, response: Response, **kwargs):
        filename = "shirts-data.html"
        with open(filename, "wb") as f:
            f.write(response)

        return super().parse(response, **kwargs)
