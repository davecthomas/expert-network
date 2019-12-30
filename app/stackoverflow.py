from urllib import parse
# from google.cloud import bigquery
# from stackapi import StackAPI
import requests
import json
import pandas as pd
from requests.adapters import HTTPAdapter

from app import db
import time

SO_DEFAULT_PAGESIZE = int(15)
# This MAX is technically unbounded, but I want to page at this size due to batch limits in Google Cloud Firestore
SO_MAX_PAGESIZE = int(500)  # There are currently < 400 sites in SO, so this feature isn't relevant, yet.
# This should be 100, but I don't want to overrun my Google Firestore limit of 20K writes (and 50K reads) per day
SO_NUM_TOP_EXPERTS = int(25)
SO_503_INTER_REQUEST_BACKOFF_SLEEP_SECONDS = 300


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
        self.s.mount(self.so_api_url, HTTPAdapter(max_retries=3))
        self.so_url_sites = "sites"
        self.so_url_users_reputation = "users?order=desc&sort=reputation"
        self.so_filter_include_total = "!9Z(-x-Q)8"  # add &filter= to include a count of all results
        self.so_current_page_sites_dict = None
        self.firestore = db.Firestore()
        self.all_sites_list = self.firestore.all_sites_list
        self.len_all_sites_list = len(self.firestore.all_sites_list)
        self.timeout_longwait = (10, 600)  # Tuple of <to remote machine>, <response>

    # Get a list of all SO sites, store them in batches of SO_MAX_PAGESIZE,
    # and return a full list of all SO Site objects.
    # Limit is SO_MAX_PAGESIZE per HTTP request; loop until no more "has_more"
    def admin_import_sites(self, page):
        so_params_dict = {}
        so_params_dict.update(self.so_params_dict)
        if not isinstance(page, int):
            page = 1
        so_params_dict["pagesize"] = SO_MAX_PAGESIZE
        has_more = True
        num_imported = 0
        list_sites_returned = []  # list of Site objects that we return

        while has_more is True:
            so_params_dict["page"] = page
            r = self.s.get(self.so_api_url + self.so_url_sites, params=so_params_dict, headers=self._so_headers)
            if r.status_code != 200:
                return {"error": r.status_code,
                        "url": {"method": self.so_api_url + self.so_url_sites, "params": so_params_dict},
                        "num_imported": num_imported}
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
                    num_imported = len(list_sites) + num_imported
                else:
                    print("batchStoreSites failed: {results_batch_store['attempted_count']}")

                if "has_more" in r_json:
                    has_more = r_json["has_more"]
                else:
                    has_more = False
                page = page + 1

            return {"num_imported": num_imported, "list_sites": list_sites_returned}

    # Remove all sites in collection
    def admin_delete_sites(self):
        return self.firestore.batchDeleteSites()

    def get_sites_by_page(self, page, pagesize):
        return_dict = self.firestore.get_sites_by_page(page, pagesize)
        return_dict["page"] = return_dict["page"] + 1
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
                dict_site = {"name": item["name"], "name_urlencoded": parse.quote(item["name"]),
                             "site": item["api_site_parameter"], "link": item["site_url"]}
                list_dict_sites.append(dict_site)
            return_dict["list_sites"] = list_sites
            return_dict["length"] = len(list_sites)
            return_dict["page"] = int(page)
            return_dict["pagesize"] = int(pagesize)
            if "has_more" in r_json:
                return_dict["has_more"] = r_json["has_more"]
            else:
                return_dict["has_more"] = r_json["has_more"]
            return return_dict

    # Get a list of top SO experts, get top reputation per site, store these
    # No paging needed, since we only get top 100 users
    def admin_import_experts(self):
        so_params_dict = {}
        so_params_dict.update(self.so_params_dict)
        page = so_params_dict["page"] = 1
        pagesize = so_params_dict["pagesize"] = SO_NUM_TOP_EXPERTS
        dict_experts_returned = {}
        num_imported = 0

        print(f"admin_import_experts num sites: {self.len_all_sites_list}")

        for site in self.all_sites_list:
            so_params_dict["site"] = site.site
            print(f"{site.site}")

            r = self.s.get(self.so_api_url + self.so_url_users_reputation, params=so_params_dict,
                           headers=self._so_headers)
            if r.status_code != 200:
                # Retry
                print(f'Retrying on error {r.status_code}:{r.reason} for {site.site}')
                # This may sleep for a mandatory backoff period, or a much longer period if 503
                self.check_for_backoff(r)

                r = self.s.get(self.so_api_url + self.so_url_users_reputation, params=so_params_dict,
                               headers=self._so_headers)
                if r.status_code != 200:
                    dict_error = {"error": r.status_code,
                                  "url": {"method": self.so_api_url + self.so_url_users_reputation,
                                          "params": so_params_dict}}
                    if r.status_code < 500:
                        dict_error["json"] = r.json()
                    print(f"admin_import_experts: {json.dumps(dict_error)}")
                    # Continue (log but ignore this failed http get from SO)
                    continue
                else:
                    dict_experts = self.import_experts_for_site(site, r.json())
            else:
                dict_experts = self.import_experts_for_site(site, r.json())

            dict_experts_returned = self.merge_experts(dict_experts, dict_experts_returned)

            num_imported = num_imported + len(dict_experts)
            print(f"{num_imported} experts imported...")

            # Sleep to back off hammering SO
            self.check_for_backoff(r)

        # Curious: get the expert with the most sites

        return {"num_imported": num_imported, "dict_experts_returned": dict_experts_returned}

    @staticmethod
    def check_for_backoff(r):
        if r.status_code < 500:
            r_json = r.json()  # json not found in 500 errors
            if "backoff" in r_json:
                secs = r_json["backoff"]
                print(f"SO mandated throttle of {secs} seconds...")
                time.sleep(secs)
        # 503 error means the service is unavailable, so back off anyway, for couple minutes...
        else:
            print(f"SO site unavailable (503 error), so backing off "
                  f"{SO_503_INTER_REQUEST_BACKOFF_SLEEP_SECONDS} seconds...")
            time.sleep(SO_503_INTER_REQUEST_BACKOFF_SLEEP_SECONDS)

    def import_experts_for_site(self, site, r_json):
        return_dict = {}
        item_list = r_json["items"]
        dict_experts = {}
        df_list = pd.DataFrame(item_list)
        df_list_columns = ["display_name", "reputation", "link", "user_id"]
        df_list = df_list[df_list_columns]
        df_list["site"] = site.site
        all_rep_sum = df_list["reputation"].sum()
        df_list["reputation_ratio"] = df_list["reputation"] / all_rep_sum
        df_list['reputation_ratio'] = df_list['reputation_ratio'].astype(float).map("{:.2%}".format)
        # df_item_list = df_list.to_dict(orient='records')
        for i, dict_expert in df_list.iterrows():
            expert = db.Expert(self.firestore.dbcoll_experts, dict_expert)
            dict_experts[expert.user_id] = expert

        results_batch_store = self.firestore.batch_store_experts(dict_experts)
        if results_batch_store["status"] != "OK":
            print(f"num_imported failed: {results_batch_store['attempted_count']}")
        # else:
        #     print(df_list)
        return dict_experts

    # If the expert in the first dict is found in the second dict, update the expert
    # Merge the first dict into the second, after you delete any duplicates
    def merge_experts(self, dict_experts, dict_experts_returned):
        list_keys_to_delete = []
        for user_id, expert in dict_experts.items():
            if user_id in dict_experts_returned:
                site_to_add = next(iter(expert.sites))
                expert_master = dict_experts_returned[user_id]
                # print(f'Found same user {user_id} from site {site_to_add} in site {expert_master.sites}')
                # This should add another site record to their reputation, total reputation increments
                expert_master.add_site(expert, site_to_add)
                # print(f"After merge: {expert_master}")
                list_keys_to_delete.append(user_id)

        for key in list_keys_to_delete:
            del dict_experts[key]

        dict_experts_returned.update(dict_experts)
        return dict_experts_returned

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
