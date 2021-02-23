#!/usr/bin/env python3.6

import sys
import os
from os import path as fpath
import re
import time
from urllib import parse as urlparse

from selenium import webdriver
from selenium.webdriver import firefox
from bs4 import BeautifulSoup

PAGE_LOAD_DELAY_SECS = 1
FIREFOX_PROFILE_DIR = fpath.join(fpath.expanduser('~'), '.mozilla', 'firefox')

DOCUMENT_FMT = '''HTTP/2 200
Content-Type: text/html; charset=utf-8

{document}
'''

ERR_FMT = '''HTTP/2 404
Content-Type: text/plain; charset=utf-8

Error: {err}
'''

if __name__ == "__main__":
    try:
        url_raw, _ = re.subn('[0-9A-Za-z\._-]*://', '', os.getenv('QUERY_STRING', ''), 1)
        url_elems = urlparse.urlsplit(url_raw, scheme='https')
        url = url_elems.geturl()
        options = firefox.options.Options()
        options.add_argument('--headless')
        profile_name = os.getenv('W3M_FIREFOX_PROFILE')
        if profile_name is not None:
            profile_fnames = os.listdir(FIREFOX_PROFILE_DIR)
            [profile] = [f for f in os.listdir(FIREFOX_PROFILE_DIR) if f.endswith('.' + profile_name)] or [None]
            profile = fpath.join(FIREFOX_PROFILE_DIR, profile) if profile is not None else None
        else:
            profile = None
        with webdriver.Firefox(firefox_options=options, firefox_profile=profile) as driver:
            driver.get(url)
            time.sleep(PAGE_LOAD_DELAY_SECS)
            window_location = driver.execute_script('return window.location')
            url_domain = window_location['hostname']
            soup = BeautifulSoup(driver.page_source)
            for a in soup.findAll('a', href=True):
                href_elems = urlparse.urlsplit(a['href'])
                href_netloc = href_elems.netloc if href_elems.netloc != '' else url_domain
                a['href'] = urlparse.urlunsplit(('https', href_netloc, *href_elems[2:]))
                # end for a in soup.findAll('a', href=True)
            for img in soup.findAll('img', src=True):
                src_elems = urlparse.urlsplit(img['src'])
                src_netloc = src_elems.netloc if src_elems.netloc != '' else url_domain
                img['src'] = urlparse.urlunsplit(('https', src_netloc, *src_elems[2:]))
                # end for img in soup.findAll('a', src=True)
            print(DOCUMENT_FMT.format(document=str(soup)))
    except Exception as err:
        print(ERR_FMT.format(err=err))
    #-- end main

