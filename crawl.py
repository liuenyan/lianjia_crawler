#!/usr/bin/env python3
# -*- coding: utf8 -*-

import requests
import grequests
import logging
from lxml import etree

root_url = "http://bj.lianjia.com/zufang/"

FORMAT = "[%(asctime)-15s] %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('crawler')
logger.setLevel(logging.INFO)


def get_district_urls():
    r = requests.get(root_url)
    r.encoding = r.apparent_encoding
    root = etree.HTML(r.content)
    hrefs = root.xpath("//div[@id=\"filter-options\"]/dl/dd[@data-index=\"0\"]/div[@class=\"option-list\"]/a")[1:]
    lst = [href.attrib['href'] for href in hrefs]
    return lst


def get_community_urls(district_url):
    r = requests.get(district_url)
    r.encoding = r.apparent_encoding
    root = etree.HTML(r.content)
    hrefs = root.xpath("//div[@id=\"filter-options\"]/dl/dd[@data-index=\"0\"]/div[@class=\"option-list sub-option-list\"]/a")[1:]
    lst = [(href.text, href.attrib['href']) for href in hrefs]
    return lst


def get_house_info(node):
    desc = str(node.xpath('h2/a/text()')[0])
    price = str(node.xpath('div[@class=\"col-3\"]/div[@class=\"price\"]/span[@class=\"num\"]/text()')[0])
    return (price, desc)


def get_first_community_page(url):
    logger.info(url)
    r = requests.get(url)
    r.encoding = r.apparent_encoding
    root = etree.HTML(r.content)
    total_node = root.xpath("//div[@class=\"list-head clear\"]/h2/span/text()")
    total = int(total_node[0])
    page_num = total//30;
    if total%30 != 0:
        page_num += 1
    house_nodes = root.xpath("//ul[@id=\"house-lst\"]/li/div[@class=\"info-panel\"]")

    lst = []
    for node in house_nodes:
        lst.append(get_house_info(node))

    for i in range(2, page_num+1, 1):
        get_other_community_page("%spg%d/"%(url, i), lst)

    return lst


def get_other_community_page(url, lst):
    logger.info(url)
    r = requests.get(url)
    r.encoding = r.apparent_encoding
    root = etree.HTML(r.content)
    house_nodes = root.xpath("//ul[@id=\"house-lst\"]/li/div[@class=\"info-panel\"]")
    for node in house_nodes:
        lst.append(get_house_info(node))


def get_community_seed_urls():
    community_urls = []
    for url in get_district_urls():
        cu = get_community_urls('http://bj.lianjia.com%s'%url)
        community_urls.extend(cu)

    return community_urls
    

if __name__ == '__main__':
    for url in get_community_seed_urls():
        lst = get_first_community_page('http://bj.lianjia.com%s'%url[1])
        with open('data/%s.txt'%url[0], 'w') as f:
            for price, desc in lst:
                f.write('%s\t%s\n'%(price, desc))

