#!/usr/bin/env python3
# encoding: utf-8

"""Record audio based on noisy detection and save."""

import configargparse
import logging
import struct
import wave
import os
import sys
import requests
from bs4 import BeautifulSoup
from dateutil import parser
import pandas as pd
import datetime
import re

# NOTE: you need this func to generate separate audio file

def get_parser():
    """Get default arguments."""
    parser = configargparse.ArgumentParser(
        description="Scraping training data from the new england journal of medicine websit.",
        config_file_parser_class=configargparse.YAMLConfigFileParser,
        formatter_class=configargparse.ArgumentDefaultsHelpFormatter,
    )
    # general configuration
    parser.add("--config", is_config_file=True, help="Config file path")
    parser.add(
        "--config2",
        is_config_file=True,
        help="Second config file path that overwrites the settings in `--config`",
    )
    parser.add(
        "--config3",
        is_config_file=True,
        help="Third config file path that overwrites the settings "
        "in `--config` and `--config2`",
    )
    ##
    parser.add_argument("--vol_start", type=int, default=336, help="The oldest avaliable journal.")
    parser.add_argument("--vol_end", type=int, default=None, help="The latest avaliable journal.")
    parser.add_argument("--output", "-o", type=str, default="", help = "Export file path. Write file for each volume ")
    ##

    return parser


def search_page(vol, page):
    print(f'Scraping from volume {vol} page {page}', end = ":\t")
    url = f"https://nejm.jp/abstract/vol{vol}.p{page}"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
    page = requests.get(url, headers = headers)
    soup = BeautifulSoup(page.content)
    results = [parag.text for parag in soup.select(".add")]
    try:
        new = soup.select("#sectionWrap a")[0].attrs['href']
    except Exception:
        print("0 training sets added.")
        return []
    en_page = requests.get(new, headers = headers)
    en_soup = BeautifulSoup(en_page.content)
    en_results = [parag.text for parag in en_soup.select("#article_Abstract .f-body")]
    if not en_results:
        en_results = [parag.text for parag in en_soup.select("#article_body .f-body")]
    tmp = [(url, jp, new, en) for jp, en in zip(results, en_results)]
    print(f"{len(tmp)} training sets added.")
    return tmp

def search_volume(vol, num):
    url = f"https://nejm.jp/contents/idx.vol{vol}.no{num}"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
    page = requests.get(url, headers = headers)
    soup = BeautifulSoup(page.content)
    results = [int(re.match('/abstract/vol\d+.p(\d+)', parag.attrs['href'])[1]) for parag in soup.select(".link02 a")]
    if not soup.select(".pageNum"):
        raise Exception("No items found.")
    return sum([search_page(vol, page) for page in results], [])

def search_all(output, vol_start = 336, vol_end = None):
    vol, num = vol_start, 1
    total_results = []
    vol_results = []
    while not vol_end or vol <= vol_end:
        try:
            vol_results += search_volume(vol, num)
            num += 1
        except Exception as e:
            if num == 1:
                break
            if vol_results:
                pd.DataFrame(vol_results, columns = ['jp_url', 'jp_txt', 'en_url', 'en_txt']).to_csv(f'{output}/vol_{vol}.csv', index = False)
                total_results += vol_results
                vol_results = []
            vol, num = vol + 1, 1
    return total_results
                

def main(args):
    """Run the main scraping function."""
    parser = get_parser()
    args = parser.parse_args(args)

    result = search_all(args.output, args.vol_start, args.vol_end)
    ## If you want to save all data, uncomment lines below
    ## pd.DataFrame(result, columns = ['jp_url', 'jp_txt', 'en_url', 'en_txt']).to_csv(f'{args.output}/total.csv', index = False)


if __name__ == "__main__":
    main(sys.argv[1:])
