from urllib import parse
# from google.cloud import bigquery
# from stackapi import StackAPI
import requests
import json
import pandas as pd
from app import db

SO_DEFAULT_PAGESIZE = int(15)


class StackOverflow:
    def __init__(self):
        """
        See app settings at https://stackapps.com/apps/oauth/view/16909
        """
        self.so_client_id = 16909
        self.so_api_key = "fBn0lLrgtPLjJeot2NKAbw(("
        self.dict_results = {}
        # self.site = StackAPI('stackoverflow')
        self.s = requests.Session()
        self._so_headers = {}
        self.so_default_pagesize = SO_DEFAULT_PAGESIZE
        self.so_params_dict = {"key": self.so_api_key, "pagesize": self.so_default_pagesize}
        self.so_api_url = "https://api.stackexchange.com/2.2/"
        self.so_url_sites = "sites"
        self.so_url_users_reputation = "users?order=desc&sort=reputation"
        self.so_filter_include_total = "!9Z(-x-Q)8"  # add &filter= to include a count of all results
        self.so_current_page_sites_dict = None
        self.db = db.Firestore()
        # self.db.testWrite()
        # self.db.testRead()

    def get_sites(self, page, pagesize=SO_DEFAULT_PAGESIZE):
        so_params_dict = {}
        so_params_dict.update(self.so_params_dict)
        if isinstance(page, int):
            so_params_dict["page"] = page
        if isinstance(pagesize, int):
            so_params_dict["pagesize"] = pagesize

        r = self.s.get(self.so_api_url + self.so_url_sites, params=so_params_dict, headers=self._so_headers)
        if r.status_code != 200:
            return {"error": r.status_code,
                    "url": {"method": self.so_api_url + self.so_url_sites, "params": so_params_dict}}
        else:
            df_sites_top100_users = pd.DataFrame()
            r_json = r.json()
            item_list = r_json["items"]
            list_dict_sites = []
            return_dict = {}
            first = True
            for item in item_list:
                # For each site in this page, get the top 100 users, by reputation, and calculate each person's reputation ratio
                r2 = self.s.get(self.so_api_url + self.so_url_users_reputation,
                                params={"key": self.so_api_key, "page": 1, "pagesize": 100,
                                        "site": item["api_site_parameter"]},
                                headers=self._so_headers)
                if r2.status_code != 200:
                    return {"error": r2.status_code,
                            "url": {"method": self.so_api_url + self.so_url_users_reputation,
                                    "params": {"key": self.so_api_key, "page": 1, "pagesize": 100,
                                               "site": item["api_site_parameter"]}}}
                else:
                    return_dict_top100_users = r2.json()
                    # return_dict_top100_users = self.get_top_users_reputation( item["api_site_parameter"], page=1, pagesize=100)
                    if "items" in return_dict_top100_users:
                        df_temp = pd.DataFrame(return_dict_top100_users["items"])
                        df_list = ["display_name", "reputation", "link", "user_id"]
                        df_temp = df_temp[df_list]
                        df_temp["site"] = item["api_site_parameter"]
                        top100_rep_sum = df_temp["reputation"].sum()
                        df_temp["reputation_ratio"] = df_temp["reputation"] / top100_rep_sum
                        df_sites_top100_users = df_sites_top100_users.append(df_temp)
                        print(df_sites_top100_users)

                dict_site = {"name": item["name"], "name_urlencoded": parse.quote(item["name"]),
                             "site": item["api_site_parameter"], "link": item["site_url"]}
                list_dict_sites.append(dict_site)
                db.Site(self.db.dbcoll_sites, dict_site).write()

            df_sites_top100_users = df_sites_top100_users.reset_index(drop=True)

            return_dict["df_sites_top100_users_style"] = df_sites_top100_users.style.format(
                {"reputation_ratio": "{:,.2%}"}).set_table_attributes(
                'class="table table-sm table-striped table-hover table-responsive"').render()
            return_dict["df_sites_top100_users"] = df_sites_top100_users
            return_dict["items"] = list_dict_sites
            return_dict["length"] = len(list_dict_sites)
            return_dict["page"] = int(page)
            return_dict["pagesize"] = int(pagesize)
            if "has_more" in r_json:
                return_dict["has_more"] = r_json["has_more"]
            else:
                return_dict["has_more"] = r_json["has_more"]
            self.so_current_page_sites_dict = return_dict
            return return_dict

    def get_top_users_reputation(self, site, page, pagesize=SO_DEFAULT_PAGESIZE):
        so_params_dict = {}
        so_params_dict.update(self.so_params_dict)
        if isinstance(page, int):
            so_params_dict["page"] = page
        if isinstance(pagesize, int):
            so_params_dict["pagesize"] = pagesize

        so_params_dict["site"] = site

        r = self.s.get(self.so_api_url + self.so_url_users_reputation, params=so_params_dict, headers=self._so_headers)
        if r.status_code != 200:
            return {"error": r.status_code,
                    "url": {"method": self.so_api_url + self.so_url_users_reputation, "params": so_params_dict}}
        else:
            return_dict = {}
            df_site_top100_users = None
            if self.so_current_page_sites_dict is not None:
                df = self.so_current_page_sites_dict["df_sites_top100_users"]
                df_site_top100_users = df.loc[df["site"] == site]
                return_dict["df_site_top100_users"] = df_site_top100_users
                # print(self.so_current_page_sites_dict)
                # print("BBBBBB")
                # print(return_dict["df_site_top100_users"])

            r_json = r.json()
            item_list = r_json["items"]
            list_dict_users = []
            for item in item_list[:pagesize]:
                list_dict_users.append(
                    {"name": item["display_name"], "link": item["link"], "reputation": item["reputation"]})
                # "reputation_ratio": df_site_top100_users.loc[df_site_top100_users['name'] == item["display_name"], "reputation_ratio"].iloc[0]})
            return_dict["items"] = list_dict_users
            return_dict["length"] = len(list_dict_users)
            return_dict["page"] = page
            return_dict["pagesize"] = pagesize
            if "has_more" in r_json:
                return_dict["has_more"] = r_json["has_more"]
            else:
                return_dict["has_more"] = r_json["has_more"]

            return return_dict

    # def get_comments(self):
    #     return self.site.fetch('comments')

    # def query_stackoverflow(self):
    #     if "results" not in self.dict_results.keys():
    #         client = bigquery.Client(project='expert-network-262703')
    #
    #         query_job = client.query("""
    #             SELECT
    #               CONCAT(
    #                 'https://stackoverflow.com/questions/',
    #                 CAST(id as STRING)) as url,
    #               view_count
    #             FROM `bigquery-public-data.stackoverflow.posts_questions`
    #             WHERE tags like '%google-bigquery%'
    #             ORDER BY view_count DESC
    #             LIMIT 10""")
    #
    #         # results = query_job.result()  # Waits for job to complete.
    #         self.dict_results["results"] = query_job
    #
    #     return self.dict_results["results"]
