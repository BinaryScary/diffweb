import requests
from bs4 import BeautifulSoup # html beautifier
import json # load json config
import os # create diff directory
import difflib # diffing html strings
import unicodedata # filename slugify
import re # filename slugify
import telegram_send # telegram messages
import argparse # argument parsing

# disable ssl warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# set useragent
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:98.0) Gecko/20100101 Firefox/98.0'
}

# string to filename
def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

def visualize(config):
    for item in config:
        if "type" in item and item["type"] == "json":
            continue

        resp = requests.get(item["url"], headers=headers, verify=False)
        resp_text = parse_html(resp.text, item)

        print(item["name"])
        print("--------")
        print("\n".join(resp_text))
        print("--------\n")

def parse_html(html, config_item):
    # format html
    beaut = BeautifulSoup(html, 'html.parser')

    # remove elements from html if del-selector provided
    if "del-selector" in config_item:
        for selector in config_item["del-selector"]:
            for elem in beaut.select(selector):
                elem.decompose()

    # turn selected bs4 html into string list
    html_lines = []
    for i in beaut.select(config_item["selector"]):
        html_lines.extend(str(i).split("\n"))

    return html_lines

def change_detection(config,diffs_path='./diffs/'):
    for item in config:
        if "type" in item and item["type"] == "json":
            continue

        # print(item["name"])
        filename = slugify(item["name"])
        resp = requests.get(item["url"], headers=headers, verify=False)
        resp_text = parse_html(resp.text, item)

        # if first time running, save html to file
        if not os.path.exists(diffs_path+filename):
            diff_file = open(diffs_path+filename, "w")
            diff_file.write(resp.text)
            diff_file.close()
            continue
        diff_file = open(diffs_path+filename, "r")
        diff_text = parse_html(diff_file, item)
        diff_file.close


        # if html is different
        if diff_text != resp_text:
            # create diff
            compare = difflib.unified_diff(diff_text, resp_text, fromfile='before', tofile='after', n=5)
            # send telegram message
            message = "{}\n{}\n---\n{}\n---".format(item["name"],item["url"],"\n".join(compare))
            print(message)
            telegram_send.send(messages=[message])

            # write new html to file
            diff_file = open(diffs_path+filename, "w")
            diff_file.write(resp.text)
            diff_file.close()

# workflow: Inspect->Copy->CSS Selector, test in https://try.jsoup.org/ with unmodified html source, del-selector if needed, visualize to confirm
# **If data is needed after javascript DOM manipulation try to find additional request, I.E JSON, XML, ect, or use Pyppeteer, Selenium**
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Detect changes in web content')
    parser.add_argument('-v', '--visualize', dest='visualize', action='store_true', help='visualize config html selections')
    parser.add_argument('-c', '--config', dest='config', type=str, default="config.json", help='config file')

    args = parser.parse_args()

    with open(args.config, 'r') as f:
      config = json.load(f)

    diffs_path = os.path.dirname(os.path.realpath(__file__))+'/diffs/'
    if not os.path.exists(diffs_path):
        os.makedirs(diffs_path)

    if args.visualize:
        visualize(config)
        quit()

    change_detection(config, diffs_path)
