from google.cloud import bigquery
from stackapi import StackAPI
import requests
import json

class StackOverflow:
    def __init__(self):
        """
        See app settings at https://stackapps.com/apps/oauth/view/16909
        """
        self.so_client_id = 16909
        self.so_api_key = "fBn0lLrgtPLjJeot2NKAbw(("
        self.dict_results = {}
        self.site = StackAPI('stackoverflow')
        self.s = requests.Session()
        self._so_headers = {}
        self.so_params_dict = {"key": self.so_api_key, "pagesize": 100}

    def get_sites(self):

        r = self.s.get("https://api.stackexchange.com/2.2/sites", params=self.so_params_dict, headers=self._so_headers)
        if r.status_code != 200:
            return r.status_code
        else:
            r_json = r.json()
            item_list = r_json["items"]
            list_dict_sites = []
            return_dict = {}
            for item in item_list:
                list_dict_sites.append({"name": item["name"], "link": item["site_url"]})
            return_dict["items"] = list_dict_sites
            return_dict["length"] = len(list_dict_sites)
            return return_dict

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

