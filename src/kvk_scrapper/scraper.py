import scrapy
import re, os
from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from scrapy import signals
import boto3
import pandas as pd
from datetime import datetime

# TODO: refactor into a dictionary with weights
INDUSTRY_IDS = [10101010,
    10101020,
    10102010,
    10102020,
    10102030,
    10102040,
    10102050,
    15101010,
    15101020,
    15101030,
    15101040,
    15101050,
    15102010,
    15103010,
    15103020,
    15104010,
    15104020,
    15104025,
    15104030,
    15104040,
    15104045,
    15104050,
    15105010,
    15105020,
    20101010,
    20102010,
    20103010,
    20104010,
    20104020,
    20105010,
    20106010,
    20106015,
    20106020,
    20107010,
    20201010,
    20201050,
    20201060,
    20201070,
    20201080,
    20202010,
    20202020,
    20301010,
    20302010,
    20303010,
    20304010,
    20304020,
    20305010,
    20305020,
    20305030,
    25101010,
    25101020,
    25102010,
    25102020,
    25201010,
    25201020,
    25201030,
    25201040,
    25201050,
    25202010,
    25203010,
    25203020,
    25203030,
    25301010,
    25301020,
    25301030,
    25301040,25301040,25301040,25301040,25301040,25301040,25301040,25301040,25301040,25301040,25301040,25301040,25301040,25301040,25301040,25301040,25301040,25301040, # Restaurants
    25302010,
    25302020,25302020,25302020,25302020,25302020,25302020,25302020,25302020,25302020,25302020,25302020,25302020,25302020,25302020,25302020,25302020,25302020, # Companies providing consumer services not classified elsewhere. Includes residential services, home security, legal services, personal services, renovation & interior design services, consumer auctions and wedding & funeral services.

    25501010,
    25502020,
    25503010,
    25503020,
    25504010,
    25504020,
    25504030,
    25504040,
    25504050,
    25504060,
    30101010,
    30101020,
    30101030,30101030,30101030,30101030,30101030,30101030,30101030,30101030,30101030,30101030,30101030,30101030,30101030,30101030,30101030,30101030,30101030,30101030, #  food retail
    30101040,
    30201010,
    30201020,
    30201030,
    30202010,  30202010,  30202010,  30202010,  30202010,  30202010,  30202010,  30202010,  30202010,  30202010,  30202010,  30202010,  30202010,  30202010,  # Agricultural Products
    30202030,
    30203010,
    30301010,
    30302010,
    35101010,
    35101020,
    35102010,
    35102015,
    35102020,
    35102030,
    35103010,
    35201010,
    35202010,
    35203010,
    40101010,
    40101015,
    40102010,
    40201020,
    40201030,
    40201040,
    40202010,
    40203010,
    40203020,
    40203030,
    40203040,
    40204010,
    40301010,
    40301020,
    40301030,
    40301040,
    40301050,
    45102010,
    45102020,
    45102030,
    45103010,
    45103020,
    45201020,
    45202030,
    45203010,
    45203015,
    45203020,
    45203030,
    45301010,
    45301020,
    50101010,
    50101020,
    50102010,
    50201010,
    50201020,
    50201030,
    50201040,
    50202010,
    50202020,
    50203010,
    55101010,
    55102010,
    55103010,
    55104010,
    55105010,
    55105020,
    60101010,
    60101020,
    60101030,
    60101040,
    60101050,
    60101060,
    60101070,
    60101080,
    60102010,
    60102020,
    60102030,
    60102040,60102040,60102040,60102040,60102040,60102040,60102040,60102040,60102040,60102040,60102040,60102040,60102040,60102040,60102040,60102040,] # Real Estate Services


#~ https://zoeken.kvk.nl/search.ashx?handelsnaam=a&kvknummer=&straat=&postcode=&huisnummer=&plaats=Haag&hoofdvestiging=1&rechtspersoon=1&nevenvestiging=1&zoekvervallen=0&zoekuitgeschreven=1&start=0&error=false&searchfield=uitgebreidzoeken&_=1669457836514
base_url ='https://zoeken.kvk.nl/search.ashx?kvknummer=&straat=&postcode=&huisnummer=&plaats=haag&hoofdvestiging=1&rechtspersoon=1&nevenvestiging=1&zoekvervallen=0&zoekuitgeschreven=1&error=false&searchfield=uitgebreidzoeken&_=1669410953425&handelsnaam='
urls = []
for digit in range(0, 10):
    urls.append(base_url+chr(digit)) # 0, 1, 2 ..

for a in range(97,123):
    urls.append(base_url+chr(a))
    for b in range(97,123): # a, b, c
        urls.append(base_url+chr(a)+chr(b)) #  aa, ab, ac ... wa, wb, wb ...

bucket_region=os.getenv('AWS_REGION')
if bucket_region is None:
    bucket_region = "eu-west-2"

bucket_name=os.getenv('KVK_SCRAPPING_RESULTS_BUCKET')
if bucket_name is None:
    bucket_name = "kvk-scrapping-results"

DETECTED_MAX_RECORD = 1000
DETECTED_RPP = 10
URL_REGEX = r'([-a-zA-Z0-9.]{2,256}\.[a-z]{2,4})\b(?:\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?'
NT_NAMESPACE = 'https://hackathonforgood.org/policy/company'


class KVKSigmaCrawler(scrapy.Spider):
    name = "kvk_sigma_crawler"
    start_urls = urls

    def get_meta_attr(self, meta, attr_name, default_value):
        attr_value = ''
        if attr_name in meta:
            attr_value = meta.get(attr_name)
        else:
            attr_value = default_value

        return attr_value

    def extract_site_urls(self, legal_name, descr):
        urls = []
        for match in re.finditer(URL_REGEX, legal_name):
            urls.append(match[0])

        descr_urls = re.search(URL_REGEX, descr)
        if descr_urls is not None:
            urls.append(descr_urls.group(1))

        return ", ".join(urls)

    def parse(self, response):
#        print("request:=====================",response.request.meta)
        prev_start_url = self.get_meta_attr(response.request.meta, 'starturl', response.url)
        print('prev start url ', prev_start_url)
        start_record  = self.get_meta_attr(response.request.meta, 'startrecord', 0)
        print('prev start record ', start_record)

        start_record += DETECTED_RPP

#        print("response:=====================", response, response.url)
        for pair in response.url.split('&'):
            if '=' in pair:
                key = pair.split('=')[0]
                value = pair.split('=')[1]
                print(key,value)

        RECORDS_NUMBER_SELECTOR =  '.searchpage .feedback > strong ::text'
        records_number = response.css(RECORDS_NUMBER_SELECTOR).extract_first()
        if len(records_number) > 0:
            records_number = int(records_number)
        else:
            records_number = 0
        print("total records", records_number)

        SET_SELECTOR = '.searchpage .results > li'
        for entity in response.css(SET_SELECTOR):
            LEGAL_NAME_SELECTOR = '.more-search-info > p ::text'
            KVK_SELECTOR = '.content .kvk-meta > li ::text'
            DESCR_SNIPPET_SELECTOR = '.snippet-result ::text'

            attributes = entity.css(KVK_SELECTOR)

            kvk = attributes.extract_first()
            if kvk.startswith('KVK '):
                kvk = kvk[4:]

            legal_name = entity.css(LEGAL_NAME_SELECTOR).extract_first()
            addr = attributes.getall()[2]
            descr = entity.css(DESCR_SNIPPET_SELECTOR).getall()[2]
            postal = attributes.getall()[3]
            location = attributes.getall()[4]
            site_url = self.extract_site_urls(legal_name, descr)

            yield {
                'legal_name': legal_name,
                'kvk': kvk,
                'address': addr,
                'postal': postal,
                'location': location,
                'description': descr,
                'sites': site_url,
            }

        if start_record == DETECTED_MAX_RECORD or records_number <= start_record:
            return

        if records_number > DETECTED_RPP:
            next_url = prev_start_url + '&start=' + str(start_record)
            print("next request url:",next_url)
            yield scrapy.Request(
                url=next_url,
                meta={
                    'starturl': prev_start_url,
                    'startrecord': start_record,
                    },
                callback=self.parse
            )

def write_s3_object(contents):
    df = pd.DataFrame(contents).drop_duplicates(subset=['kvk'])
    csv_content = df.to_csv(index=False)
    print("contents:", csv_content)

    object_key_suffix = datetime.today().strftime('%Y_%m_%d_%H_%M_%S')

    print("Target bucket '{0}', region '{1}'".format(bucket_name, bucket_region))

    ntriple_items = []
    industry_num = 0
    for raw in df.T.to_dict().values():
        kvk = raw['kvk']
        address = raw['address']
        postal = raw['postal']
        location = raw['location']
        sites = raw['sites']
        legal_name = raw['legal_name']
        industry_id = INDUSTRY_IDS[industry_num]

        ntriple_items.append('<{0}/{1}> <{0}/legalName> "{2}" .'.format(NT_NAMESPACE, kvk, legal_name.replace('"', '').replace("'",'')))
        ntriple_items.append('<{0}/{1}> <{0}/address> "{2}" .'.format(NT_NAMESPACE, kvk, address.replace('"', '').replace("'",'')))
        ntriple_items.append('<{0}/{1}> <{0}/postal> "{2}" .'.format(NT_NAMESPACE, kvk, postal.replace('"', '').replace("'",'')))
        ntriple_items.append('<{0}/{1}> <{0}/location> "{2}" .'.format(NT_NAMESPACE, kvk, location.replace('"', '').replace("'",'')))
        ntriple_items.append('<{0}/{1}> <https://hackathonforgood.org/policy/belongsTo> <https://hackathonforgood.org/policy/subindustry/{2}> .'.format(NT_NAMESPACE, kvk, industry_id))

        if len(sites) > 0:
            ntriple_items.append('<{0}/{1}> <{0}/sites> "{2}" .'.format(NT_NAMESPACE, kvk, sites.replace('"', '').replace("'",'')))

        industry_num = industry_num + 1
        if industry_num >= len(INDUSTRY_IDS):
           industry_num = 0

    ntriples_content = "\n".join(ntriple_items)
    s3_client = boto3.client(service_name='s3', region_name=bucket_region)

    csv_object_key = "scrapings/kvk_scrape_"+object_key_suffix+".csv"
    ntriple_object_key = "scrapings/kvk_scrape_"+object_key_suffix+".nt"
    s3_client.put_object(Bucket=bucket_name, Body=csv_content, Key=csv_object_key)
    s3_client.put_object(Bucket=bucket_name, Body=ntriples_content, Key=ntriple_object_key)

    print("written s3 objects: {}, {}".format(csv_object_key, ntriple_object_key ))

########################################################################################################################

if __name__ == "__main__":
    results = []

    def crawler_results(signal, sender, item, response, spider):
        results.append(item)

    dispatcher.connect(crawler_results, signal=signals.item_scraped)

    process = CrawlerProcess()
    process.crawl(KVKSigmaCrawler)

    process.start()
    joined = process.join()


    write_s3_object(results)