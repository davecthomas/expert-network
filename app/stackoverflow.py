from urllib import parse
# from google.cloud import bigquery
# from stackapi import StackAPI
import requests
import json
import pandas as pd
from app import db

SO_DEFAULT_PAGESIZE = int(15)
# This MAX is technically unbounded, but I want to page at this size due to batch limits in Google Cloud Firestore
SO_MAX_PAGESIZE = int(500)


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
        self.firestore = db.Firestore()
        # self.firestore.testWrite()
        # self.firestore.testRead()

    # Get a list of all SO sites, store them in batches of SO_MAX_PAGESIZE,
    # and return a full list of all SO Site objects.
    # Limit is SO_MAX_PAGESIZE per HTTP request; loop until no more "has_more"
    def admin_load_sites(self, page):
        so_params_dict = {}
        so_params_dict.update(self.so_params_dict)
        if not isinstance(page, int):
            page = 1
        so_params_dict["pagesize"] = SO_MAX_PAGESIZE
        has_more = True
        num_loaded = 0
        list_sites_returned = []  # list of Site objects that we return

        while has_more is True:
            so_params_dict["page"] = page
            r = self.s.get(self.so_api_url + self.so_url_sites, params=so_params_dict, headers=self._so_headers)
            if r.status_code != 200:
                return {"error": r.status_code,
                        "url": {"method": self.so_api_url + self.so_url_sites, "params": so_params_dict},
                        "num_loaded": num_loaded}
            else:
                # Each of these is reused per iteration
                r_json = r.json()
                item_list = r_json["items"]

                # Create a batch of sites to store
                list_sites = []
                for item in item_list:
                    dict_site = {"name": item["name"], "name_urlencoded": parse.quote(item["name"]),
                                 "site": item["api_site_parameter"], "link": item["site_url"]}
                    list_sites.append(db.Site(self.firestore.dbcoll_sites, dict_site))

                results_batch_store = self.firestore.batchStoreSites(list_sites)
                if results_batch_store["status"] == "OK":
                    list_sites_returned.extend(list_sites)
                    print("batchStoreSites stored: {results_batch_store['count_stored']}")
                    num_loaded = len(list_sites) + num_loaded
                else:
                    print("batchStoreSites failed: {results_batch_store['attempted_count']}")

                if "has_more" in r_json:
                    has_more = r_json["has_more"]
                else:
                    has_more = False
                page = page + 1

            return {"num_loaded": num_loaded, "list_sites": list_sites_returned}

    # Remove all sites in collection
    def admin_delete_sites(self):
        return self.firestore.batchDeleteSites()

    def get_sites_by_page(self, page, pagesize):
        return_dict = self.firestore.get_sites_by_page(page, pagesize)
        return return_dict

    # Get a list of all SO sites and return a list of Site objects
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
            # df_sites_top100_users = pd.DataFrame()
            r_json = r.json()
            item_list = r_json["items"]
            list_dict_sites = []
            list_sites = []  # list of Site objects
            return_dict = {}
            first = True
            for item in item_list:
                # # For each site in this page, get the top 100 users, by reputation, and calculate each person's reputation ratio
                # r2 = self.s.get(self.so_api_url + self.so_url_users_reputation,
                #                 params={"key": self.so_api_key, "page": 1, "pagesize": 100,
                #                         "site": item["api_site_parameter"]},
                #                 headers=self._so_headers)
                # if r2.status_code != 200:
                #     return {"error": r2.status_code,
                #             "url": {"method": self.so_api_url + self.so_url_users_reputation,
                #                     "params": {"key": self.so_api_key, "page": 1, "pagesize": 100,
                #                                "site": item["api_site_parameter"]}}}
                # else:
                #     return_dict_top100_users = r2.json()
                #     # return_dict_top100_users = self.get_top_users_reputation( item["api_site_parameter"], page=1, pagesize=100)
                #     if "items" in return_dict_top100_users:
                #         df_temp = pd.DataFrame(return_dict_top100_users["items"])
                #         df_list = ["display_name", "reputation", "link", "user_id"]
                #         df_temp = df_temp[df_list]
                #         df_temp["site"] = item["api_site_parameter"]
                #         top100_rep_sum = df_temp["reputation"].sum()
                #         df_temp["reputation_ratio"] = df_temp["reputation"] / top100_rep_sum
                #         df_sites_top100_users = df_sites_top100_users.append(df_temp)
                #         print(df_sites_top100_users)

                dict_site = {"name": item["name"], "name_urlencoded": parse.quote(item["name"]),
                             "site": item["api_site_parameter"], "link": item["site_url"]}
                list_dict_sites.append(dict_site)
            #     list_sites.append(db.Site(self.firestore.dbcoll_sites, dict_site))
            #
            # self.firestore.batchStoreSites(list_sites)

            df_sites_top100_users = df_sites_top100_users.reset_index(drop=True)

            # return_dict["df_sites_top100_users_style"] = df_sites_top100_users.style.format(
            #     {"reputation_ratio": "{:,.2%}"}).set_table_attributes(
            #     'class="table table-sm table-striped table-hover table-responsive"').render()
            # return_dict["df_sites_top100_users"] = df_sites_top100_users
            # return_dict["items"] = list_dict_sites
            return_dict["list_sites"] = list_sites
            return_dict["length"] = len(list_sites)
            return_dict["page"] = int(page)
            return_dict["pagesize"] = int(pagesize)
            if "has_more" in r_json:
                return_dict["has_more"] = r_json["has_more"]
            else:
                return_dict["has_more"] = r_json["has_more"]
            # self.so_current_page_sites_dict = return_dict
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
