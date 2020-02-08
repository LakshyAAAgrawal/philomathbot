from bs4 import BeautifulSoup
from random import randint

import re
import urllib.parse
import requests
import random

class WikiRecommender(object):
    def __init__(self):
        self.sources = dict()
        self.targets = dict()
        self.recommendation_list = []

    def generate_summary(self, topic, sourcelist):
        try:
            summary_text = self.summary_text
        except:
            self.summary_text = True
            summary_text = self.summary_text
        if summary_text:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "format": "json",
                "action" : "query",
                "prop" : "extracts",
                "exintro" : "",
                "exsectionformat" : "wiki",
                "explaintext" : "",
                "redirects" : "1",
                "titles" : topic
            }
            r = requests.get(url, params=params)
            extract = r.json()['query']['pages'].popitem()[1]['extract']
        else:
            extract = ""
        title = topic
        sources = ", ".join(sourcelist)
        return (title, extract, sources,"en.wikipedia.org/wiki/" + urllib.parse.quote(title))

    def list_of_followed(self):
        return list(self.sources)

    def unfollow_topic(self, topic):
        root_page, list_to_unfollow = self.list_of_topics_in_page(topic)
        if root_page == "":
            return
        for unwanted_topic in list_to_unfollow:
            if unwanted_topic in self.targets:
                for source in self.targets[unwanted_topic]:
                    self.sources[source].difference_update(set([unwanted_topic]))
                del self.targets[unwanted_topic]
        if root_page in self.sources:
            del self.sources[root_page]
        if topic in self.sources:
            del self.sources[topic]
        self.update_recommendation_list()

    def update_recommendation_list(self):
        self.recommendation_list = []
        for target in self.targets:
            self.recommendation_list.append((len(self.targets[target]), target))
        self.recommendation_list.sort()

    def get_recommended_item(self):
        temp = []
        for target_freq, target in self.recommendation_list:
            temp.extend([target] * target_freq)
        rand = random.randint(0, len(temp) - 1)
        topic = temp[rand]
        for source in self.targets[topic]:
            self.sources[source] = self.sources[source].difference(set([topic]))
        sourcelist = self.targets[topic]
        del self.targets[topic]
        self.update_recommendation_list()
        return topic, sourcelist

    def toggle_summary(self):
        try:
            self.summary_text = not self.summary_text
        except:
            self.summary_text = False

    def get_content(self):
        if len(self.sources) == 0:
            return ("No Topics", "No Topics to follow. Send me topics to follow", "None", "wikipedia.org")
        else:
            topic, sources = self.get_recommended_item()
            return self.generate_summary(topic, sources)

    def list_of_topics_in_page(self, page_title):
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action" : "opensearch",
            "search" : page_title,
            "limit" : 1,
            "namespace" : 0,
            "format" : "json",
        }
        r = requests.get(url, params=params)
        if len(r.json()[3]) == 0:
            return "", []
        print(r.json())
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
        return root_page, new_topics

    def follow_topic(self, topic):
        root_page, new_topics = self.list_of_topics_in_page(topic)
        if root_page == "":
            return 0
        if root_page in self.sources:
            self.sources[root_page].update(new_topics)
        else:
            self.sources[root_page] = set(new_topics)

        for newtopic in new_topics:
            if newtopic in self.targets:
                self.targets[newtopic].add(root_page)
            else:
                self.targets[newtopic] = set([root_page])

        if root_page in self.targets:
            for source in self.targets[root_page]:
                self.sources[source].difference_update(set([root_page]))
            del self.targets[root_page]
        self.update_recommendation_list()
        return len(new_topics)
