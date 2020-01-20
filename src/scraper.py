from bs4 import BeautifulSoup
from random import randint

import re
import requests

class WikiRecommender(object):
    def __init__(self):
        self.topics = set()

    def generate_summary(self, topic):
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "format": "json",
            "action" : "query",
            "prop" : "extracts",
            "exintro" : "",
            "explaintext" : "",
            "redirects" : "1",
            "titles" : topic
        }
        r = requests.get(url, params=params)
        title = r.json()['query']['pages'].popitem()[1]['title']
        extract = r.json()['query']['pages'].popitem()[1]['extract']
        return (title, extract)

    def get_content(self):
        if len(self.topics) == 0:
            return ("No Topics", "No Topics to follow. Send me topics to follow")
        else:
            topic = self.topics.pop()
            return self.generate_summary(topic)

    def follow_topic(self, topic):
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action" : "opensearch",
            "search" : topic,
            "limit" : 1,
            "namespace" : 0,
            "format" : "json",
        }
        r = requests.get(url, params=params)
        if len(r.json()[3]) == 0:
            return 0

        root_page = r.json()[1][0]
        r = requests.get(r.json()[3][0])
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.find_all(
            # Filter to match all anchor tags like <a href="/wiki/XYZ"></a>
            # and not match <a href="/wiki/Help:XYZ"></a>
            lambda tag: (tag.name == "a" and
                         len(tag.attrs) == 2 and
                         "title" in tag.attrs and
                         "href" in tag.attrs and
                         re.match("\/wiki\/[^:]*$", tag.attrs["href"]))
        )
        new_topics = list(map(lambda tag: tag["title"], links))
        self.topics.update(new_topics)
        return len(new_topics)
