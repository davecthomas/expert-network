from google.cloud import firestore
from datetime import datetime
import itertools as it
import json

GOOGLE_FIRESTORE_MAX_BATCH_SIZE = int(500)

class Firestore:
    def __init__(self):
        """
        Requires Project ID, determined by the GCLOUD_PROJECT environment variable
        """
        self.db = firestore.Client(project='expert-network-262703')
        self.dbcoll_sites = self.db.collection(u'sites')
        self.dbcoll_experts = self.db.collection(u'experts')
        self.all_sites_stream = self.dbcoll_sites.order_by(u'name').stream()
        fs_sites_list = list(self.all_sites_stream)
        # Convert a list of Firestore objects to a list of Site objects
        self.all_sites_list = []
        for fs_site in fs_sites_list:
            dict_site = fs_site.to_dict()
            self.all_sites_list.append(Site(self.dbcoll_sites, fs_site.to_dict()))

        self.len_all_sites_list = len(self.all_sites_list)
        # print(f'{self.len_all_sites_list}: {self.all_sites_list}')

    # Store a batch of up to 500 sites (limited by Google Cloud Batch transaction limits)
    # This can be done repeatedly without concern, due to merge=True
    def batchStoreSites(self, list_sites):
        len_list = len(list_sites)
        count_stored = 0
        if len_list > GOOGLE_FIRESTORE_MAX_BATCH_SIZE:
            return {"status": "Failed", "attempted_count": len_list}

        batch = self.db.batch()
        for site in list_sites:
            batch.set(self.dbcoll_sites.document(site.site), site.to_dict(), merge=True)
            count_stored = count_stored + 1

        # Commit the batch
        batch.commit()

        return {"status": "OK", "count_stored": count_stored}

    # Delete all sites in collection and return number of sites deleted
    def batchDeleteSites(self):
        print("Deleting sites:")
        batch = self.db.batch()
        count_deleted = 0
        for site in self.all_sites_stream:
            # print(u'{} => {}'.format(site.id, site.to_dict()))
            batch.delete(self.dbcoll_sites.document(site.id))
            count_deleted = count_deleted + 1
        # Commit the delete
        batch.commit()
        return count_deleted

    # Delete all sites in collection and return number of sites deleted
    def get_sites_by_page(self, page, pagesize):
        if page > 0:
            page = page - 1
        return_dict = {}
        return_dict["page"] = int(page)
        return_dict["pagesize"] = int(pagesize)
        slice_list = it.islice(self.all_sites_list, page*pagesize, page*pagesize+pagesize)
        return_dict["list_sites"] = list(slice_list)
        return_dict["length"] = len(return_dict["list_sites"])

        if page*pagesize+pagesize >= self.len_all_sites_list:
            return_dict["has_more"] = False
        else:
            return_dict["has_more"] = True

        # print(f"page {page}, pagesize {pagesize}")
        # for site in return_dict["list_sites"]:
        #     dict_site = site.to_dict()
        #     print(f'{site.name} => {dict_site}')

        return return_dict

    # Store a batch of up to 500 experts (limited by Google Cloud Batch transaction limits)
    # This can be done repeatedly without concern, due to merge=True
    def batch_store_experts(self, list_experts):
        len_list = len(list_experts)
        count_stored = 0
        if len_list > GOOGLE_FIRESTORE_MAX_BATCH_SIZE:
            list_of_batches = [list_experts[i:i + GOOGLE_FIRESTORE_MAX_BATCH_SIZE] for i in range(0, len(list_experts), GOOGLE_FIRESTORE_MAX_BATCH_SIZE)]
        else:
            list_of_batches = [list_experts]

        for batch_of_experts in list_of_batches:
            # batch = self.db.batch()
            for expert in batch_of_experts:
                # print(f"{expert.to_dict()}")
                # batch.set(self.dbcoll_experts.document(expert.user_id), expert.to_dict(), merge=True)
                count_stored = count_stored + 1
            # batch.commit()

        return {"status": "OK", "count_stored": count_stored}


class Site:
    # {"name": item["name"], "name_urlencoded": parse.quote(item["name"]),
    # "site": item["api_site_parameter"], "link": item["site_url"]}
    def __init__(self, dbcoll_sites, dict_site):
        self.dict_site = dict_site
        self.dbcoll_sites = dbcoll_sites

        if "name" in dict_site:
            self.name = dict_site["name"]
        else:
            self.name = None
        if "name_urlencoded" in dict_site:
            self.name_urlencoded = dict_site["name_urlencoded"]
        else:
            self.name_urlencoded = None
        if "site" in dict_site:
            self.site = dict_site["site"]
        else:
            self.site = None
        if "link" in dict_site:
            self.link = dict_site["link"]
        else:
            self.link = None

    def to_dict(self):
        return self.dict_site

    def __repr__(self):
        return json.dumps(self.dict_site)

    # Non-batched write is currently unused
    def write(self):
        self.dict_site["timestamp"] = firestore.SERVER_TIMESTAMP
        self.dbcoll_sites.document(self.site).set(self.dict_site, merge=True)


class Expert:
    # {"user_id": item["user_id"], "display_name": item["display_name"]),
    # "link": item["link"], "site": item["site"], "reputation": item["reputation"]}
    def __init__(self, dbcoll_experts, dict_expert):
        self.dict_expert = dict_expert
        self.dbcoll_experts = dbcoll_experts

        if "user_id" in dict_expert:
            self.user_id = dict_expert["user_id"]
        else:
            self.user_id = None
        if "display_name" in dict_expert:
            self.display_name = dict_expert["display_name"]
        else:
            self.display_name = None
        if "link" in dict_expert:
            self.link = dict_expert["link"]
        else:
            self.link = None
        if "site" in dict_expert:
            self.site = dict_expert["site"]
        else:
            self.site = None

        self.total_reputation = 0
        self.site_reputation = {}
        # Store a dictionary of {site_a: reputation_a, site_b: reputation_b}
        # and a total_reputation (although this is unused currently)
        if "site" in dict_expert:
            if "reputation" in dict_expert:
                self.site_reputation[dict_expert["site"]] = dict_expert["reputation"]
                self.total_reputation = self.total_reputation + dict_expert["reputation"]
            else:
                self.site_reputation[dict_expert["site"]] = None

    def to_dict(self):
        return self.dict_expert

    def __repr__(self):
        return json.dumps(self.dict_expert)

    # Non-batched write is currently unused
    def write(self):
        self.dict_expert["timestamp"] = firestore.SERVER_TIMESTAMP
        self.dbcoll_sites.document(self.user_id).set(self.dict_expert, merge=True)
