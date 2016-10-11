#!/usr/bin/env python3
# -*- coding: utf8 -*-

import requests
import grequests
import logging
import sys
from lxml import etree

root_url = "http://bj.lianjia.com"

FORMAT = "[%(asctime)-15s][%(message)s]"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('crawler')
logger.setLevel(logging.INFO)

GREQUESTS_GROUP_MAX = 6

def get_district_urls():
    r = requests.get("{}/zufang/".format(root_url))
    r.encoding = r.apparent_encoding
    root = etree.HTML(r.content)
    hrefs = root.xpath("//div[@id=\"filter-options\"]/dl/dd[@data-index=\"0\"]/div[@class=\"option-list\"]/a")[1:]
    lst = [href.attrib['href'] for href in hrefs]
    return lst

def get_community_seed_urls():
    community_urls = []
    rs = (grequests.get("{0}{1}".format(root_url, url)) for url in get_district_urls())
    res = grequests.map(rs)
    for r in res:
        print(r.status_code)
        r.encoding = r.apparent_encoding
        root = etree.HTML(r.content)
        hrefs = root.xpath("//div[@id=\"filter-options\"]/dl/dd[@data-index=\"0\"]/div[@class=\"option-list sub-option-list\"]/a")[1:]
        lst = [(href.text, href.attrib['href']) for href in hrefs]
        community_urls.extend(lst)
    return community_urls


def get_house_info(node):
    desc = str(node.xpath('h2/a/text()')[0])
    price = str(node.xpath('div[@class=\"col-3\"]/div[@class=\"price\"]/span[@class=\"num\"]/text()')[0])
    return (price, desc)


def get_community_page_nums(total):
    page_num = total//30
    return page_num if (total % 30 == 0) else (page_num + 1)
   
def make_page_groups(urls):
    length = len(urls)
    group_num = length//GREQUESTS_GROUP_MAX
    groups =[urls[i*GREQUESTS_GROUP_MAX:(i+1)*GREQUESTS_GROUP_MAX] for i in range(group_num)]
    if length % GREQUESTS_GROUP_MAX != 0:
        groups.append(urls[group_num*GREQUESTS_GROUP_MAX:])
    return groups

def get_community_houses(url):
    logger.info(url)
    r = requests.get(url)
    r.encoding = r.apparent_encoding
    root = etree.HTML(r.content)
    
    house_nodes = root.xpath("//ul[@id=\"house-lst\"]/li/div[@class=\"info-panel\"]")
    lst = [get_house_info(node) for node in house_nodes]

    total_node = root.xpath("//div[@class=\"list-head clear\"]/h2/span/text()")
    total = int(total_node[0])
    page_num = get_community_page_nums(total)
    page_lst = ["{0}pg{1}".format(url, i) for i in range(2, page_num+1, 1)]
    page_groups =make_page_groups(page_lst)
    logger.info("{0} records, {1} pages, {2} groups.".format(total, page_num, len(page_groups)))

    for group in page_groups:
        rs = (grequests.get(page_url) for page_url in group)
        res = grequests.map(rs)
        for r in res:
            if r is None:
                logger.warning("response is None.")
                continue
            if r.status_code != 200:
                logger.warning("{0} {1} {2}".format(r.status_code, r.reason, r.url))
                continue
            root = etree.HTML(r.content)
            house_nodes = root.xpath("//ul[@id=\"house-lst\"]/li/div[@class=\"info-panel\"]")
            for node in house_nodes:
                lst.append(get_house_info(node))
    logger.info("get {} records.".format(len(lst)))
    return lst


if __name__ == '__main__':
    urls = get_community_seed_urls()
    print(urls)
    for name, url in urls:
        print(name, url)
        lst = get_community_houses('{0}{1}'.format(root_url, url))
        filename = "data/{}.txt".format(name)
        with open(filename, 'a+') as f:
            for price, desc in lst:
                f.write('%s\t%s\n'%(price, desc))
