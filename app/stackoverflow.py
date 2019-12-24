from google.cloud import bigquery
from stackapi import StackAPI
import requests
import json

class StackOverflow:
    def __init__(self):
        """
        Get properties and get connected
        """
        self.dict_results = {}
        self.site = StackAPI('stackoverflow')
        self.s = requests.Session()
        self._so_headers = {}

    def get_sites(self):
        params_dict = {}
        r = self.s.get("https://api.stackexchange.com/2.2/sites", params=params_dict, headers=self._so_headers)
        if r.status_code != 200:
            return r.status_code
        else:
            r_json = r.json()
            item_list = r_json["items"]
            list_dict_sites = []
            for item in item_list:
                list_dict_sites.append({"name": item["name"], "link": item["site_url"]})
            return json.dumps(list_dict_sites)

    def get_comments(self):
        self.comments = self.site.fetch('comments')
        return self.comments

    def query_stackoverflow(self):
        if "results" not in self.dict_results.keys():
            client = bigquery.Client(project='expert-network-262703')

            query_job = client.query("""
                SELECT
                  CONCAT(
                    'https://stackoverflow.com/questions/',
                    CAST(id as STRING)) as url,
                  view_count
                FROM `bigquery-public-data.stackoverflow.posts_questions`
                WHERE tags like '%google-bigquery%'
                ORDER BY view_count DESC
                LIMIT 10""")

            # results = query_job.result()  # Waits for job to complete.
            self.dict_results["results"] = query_job

        return self.dict_results["results"]

