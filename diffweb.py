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
        resp = requests.get(item["url"], headers=headers, verify=False)
        resp_beaut = BeautifulSoup(resp.text, 'html.parser')
        print(resp_beaut)

        # remove elements from html if del-selector provided
        if "del-selector" in item:
            for selector in item["del-selector"]:
                for elem in resp_beaut.select(selector):
                    elem.decompose()

        # turn selected bs4 html into string
        resp_text = []
        for i in resp_beaut.select(item["selector"]):
            resp_text.extend(str(i).split("\n"))

        print(item["name"])
        print("--------")
        print("\n".join(resp_text))
        print("--------\n")


def change_detection(config):
    for item in config:
        # print(item["name"])
        filename = slugify(item["name"])
        resp = requests.get(item["url"], headers=headers, verify=False)
        resp_beaut = BeautifulSoup(resp.text, 'html.parser')

        # if first time running, save html to file
        if not os.path.exists('./diffs/'+filename):
            diff_file = open('./diffs/'+filename, "w")
            diff_file.write(resp.text)
            diff_file.close()
            continue
        diff_file = open('./diffs/'+filename, "r")
        diff_beaut = BeautifulSoup(diff_file, 'html.parser')
        diff_file.close

        # remove elements from html if del-selector provided
        if "del-selector" in item:
            for selector in item["del-selector"]:
                for elem in diff_beaut.select(selector):
                    elem.decompose()
                for elem in resp_beaut.select(selector):
                    elem.decompose()

        # turn selected bs4 html into string
        diff_text = []
        for i in diff_beaut.select(item["selector"]):
            diff_text.extend(str(i).split("\n"))
        resp_text = []
        for i in resp_beaut.select(item["selector"]):
            resp_text.extend(str(i).split("\n"))

        # if html is different
        if diff_text != resp_text:
            # create diff
            compare = difflib.unified_diff(diff_text, resp_text, fromfile='before', tofile='after', n=5)
            # send telegram message
            message = "{}\n{}\n---\n{}\n---".format(item["name"],item["url"],"\n".join(compare))
            print(message)
            telegram_send.send(messages=[message])

            # write new html to file
            diff_file = open('./diffs/'+filename, "w")
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

    if not os.path.exists('diffs'):
        os.makedirs('diffs')

    if args.visualize:
        visualize(config)
        quit()

    change_detection(config)
