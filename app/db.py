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

    # Store a batch of up to 500 sites (limited by Google Cloud Batch transaction limits)
    # This can be done repeatedly without concern, due to merge=True
    def batchStoreSites(self, list_sites, test=False):
        len_list = len(list_sites)
        count_stored = 0
        if len_list > GOOGLE_FIRESTORE_MAX_BATCH_SIZE:
            return {"status": "Failed", "attempted_count": len_list}
        if not test:
            batch = self.db.batch()
        for site in list_sites:
            if not test:
                batch.set(self.dbcoll_sites.document(site.site), site.to_dict(), merge=True)
            else:
                print(f'Test commit of {site.to_dict()}')
            count_stored = count_stored + 1

        # Commit the batch
        if not test:
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
        slice_list = it.islice(self.all_sites_list, page * pagesize, page * pagesize + pagesize)
        return_dict["list_sites"] = list(slice_list)
        return_dict["length"] = len(return_dict["list_sites"])

        if page * pagesize + pagesize >= self.len_all_sites_list:
            return_dict["has_more"] = False
        else:
            return_dict["has_more"] = True

        return return_dict

    # Store a batch of up to 500 experts (limited by Google Cloud Batch transaction limits)
    # This can be done repeatedly without concern, due to merge=True
    # Test mode allows printing rather than storing.
    def batch_store_experts(self, dict_experts, test=True):
        len_dict = len(dict_experts)
        # print(f'batch_store_experts with dict of length {len_dict}')
        count_stored = 0
        this_batch_length = 0
        count_batches = 0

        if not test:
            batch = self.db.batch()
        for expert_key, expert in dict_experts.items():
            if not test:
                # print(f'Adding to batch: {expert_key}: {expert.to_dict()}')
                batch.set(self.dbcoll_experts.document(expert_key), expert.to_dict(), merge=True)
            # else:
            #     print(f'Test of {expert_key}: {expert.to_dict()}')
            count_stored = count_stored + 1
            this_batch_length = this_batch_length + 1
            if (this_batch_length >= GOOGLE_FIRESTORE_MAX_BATCH_SIZE) | (count_stored >= len_dict):
                count_batches = count_batches + 1
                # print(
                #     f'{count_batches}{count_stored}: Committing batch of length {this_batch_length} out of a dict of {len_dict} keys.')
                if not test:
                    batch.commit()
                    batch = self.db.batch()
                this_batch_length = 0

        batch = None
        return {"status": "OK", "count_stored": count_stored}

    def get_experts_by_site(self, site_name):
        site = self.dbcoll_sites.where(u'site', u'==', site_name).get()
        print(f'List contains {len(site.expert_list)} experts')
        for expert in site.expert_list:
            print(u'{} => {}'.format(expert.expert_key, expert.to_dict()))
        return site.expert_list

    def get_site_from_name(self, site_name):
        site_obj = None
        sites = self.dbcoll_sites.where(u'site', u'==', site_name).get()
        for site in sites:
            site_obj = Site(self.dbcoll_sites, site.to_dict())
            # print(f'{site_obj.to_dict()}')
        return site_obj

    def get_expert_from_id(self, user_id):
        expert_obj = None
        # print(f'ID: {user_id}')
        experts = self.dbcoll_experts.where(u'user_id', u'==', user_id).get()
        for expert in experts:
            print(f'DB {expert.to_dict()}')
            expert_obj = Expert(self.dbcoll_experts, expert.to_dict())
            print(f'OBJ {expert_obj.to_dict()}')
        return expert_obj


class Site:
    # {"name": item["name"], "name_urlencoded": parse.quote(item["name"]),
    # "site": item["api_site_parameter"], "link": item["site_url"]}
    def __init__(self, dbcoll_sites, dict_site):
        self.dict_site = dict_site
        self.dbcoll_sites = dbcoll_sites
        self.timestamp = datetime.now()

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
        if "expert_list" in dict_site:
            self.expert_list = dict_site["expert_list"]
        else:
            self.expert_list = []
            self.dict_site["expert_list"] = []

    def add_expert_list(self, expert_list, test=False):
        self.expert_list = expert_list
        self.timestamp = datetime.now()
        self.dbcoll_sites.document(self.site).update({u'expert_list': expert_list})
        print(f'Adding {expert_list} to {self.name}')

    def to_dict(self):
        return {"name": self.name, "name_urlencoded": self.name_urlencoded,
                "site": self.site, "link": self.link, "expert_list": self.expert_list,
                "timestamp": self.timestamp}

    def __repr__(self):
        return json.dumps(self.dict_site)

    # Non-batched write is currently unused
    def update_firestore(self):
        self.timestamp = datetime.now()
        self.dbcoll_sites.document(self.site).set(self.to_dict(), merge=True)


class Expert:
    # {"expert_key": expert_key, "user_id": item["user_id"], "display_name": item["display_name"]),
    # "link": item["link"], "sites": {site: "reputation": rep,
    # "reputation_ratio": "0.00%", "reputation_ratio_val": ratio},
    # "total_reputation": total }
    # Note: init adds an empty sites {} dictionary. Sites must be added with add_site.
    def __init__(self, dbcoll_experts, dict_expert):
        self.dict_expert = dict_expert
        self.dbcoll_experts = dbcoll_experts
        self.total_reputation = 0

        if "expert_key" in dict_expert:
            self.expert_key = dict_expert["expert_key"]
        else:
            self.expert_key = None
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
        if "sites" in dict_expert:
            self.sites = dict_expert["sites"]
            # if isinstance(self.sites, dict):
            #     for site_name, site_dict in self.sites.items():
            #         if "reputation" in site_dict:
            #             self.total_reputation = self.total_reputation + site_dict["reputation"]
        else:
            self.sites = {}
        if "total_reputation" in dict_expert:
            self.total_reputation = dict_expert["total_reputation"]

        self.timestamp = datetime.now()

    def add_site(self, dict_expert):
        if "site" in dict_expert:
            site_key = dict_expert["site"]
            self.sites[site_key] = {"site": site_key, "reputation": None, "reputation_ratio": None}
            if "reputation" in dict_expert:
                self.sites[site_key]["reputation"] = dict_expert["reputation"]
                self.total_reputation = self.total_reputation + dict_expert["reputation"]
            if "reputation_ratio" in dict_expert:
                self.sites[site_key]["reputation_ratio"] = dict_expert["reputation_ratio"]
            if "reputation_ratio_val" in dict_expert:
                self.sites[site_key]["reputation_ratio_val"] = dict_expert["reputation_ratio_val"]
            self.timestamp = datetime.now()

    @staticmethod
    def check_and_merge(dict_expert, dict_experts_returned, test=False):
        if dict_expert["expert_key"] in dict_experts_returned:
            expert = dict_experts_returned[dict_expert["expert_key"]]
            expert.add_site(dict_expert)
            # As a test, show any experts with more than three sites
            # count_sites = 0
            # for site_key, site in expert.sites.items():
            #     count_sites = count_sites + 1
            #     if count_sites > 2:
            #         print(f'\n\n\n\nMore than 2 sites found for {expert}')
            expert.update_firestore(test)
            return True
        else:
            return False

    def to_dict(self):
        sites = {}
        for site_name, site in self.sites.items():
            sites[site_name] = {"site": site_name, "reputation": site["reputation"],
                                "reputation_ratio": site["reputation_ratio"]}
        to_dict = {"expert_key": self.expert_key, "user_id": self.user_id, "display_name": self.display_name,
                   "link": self.link,
                   "total_reputation": self.total_reputation, "sites": sites, "timestamp": self.timestamp}
        # print(f'to_dict: {to_dict}')
        return to_dict

    def __repr__(self):
        return json.dumps({"expert_key": self.expert_key, "user_id": self.user_id, "display_name": self.display_name,
                           "link": self.link,
                           "total_reputation": self.total_reputation, "sites": self.sites, "timestamp": self.timestamp})

    # Non-batched write
    def update_firestore(self, test=False):
        self.timestamp = datetime.now()
        to_dict = self.to_dict()
        if not test:
            self.dbcoll_experts.document(self.expert_key).set(self.to_dict(), merge=True)
        # print(f'Updating {self.expert_key} with {to_dict}')
