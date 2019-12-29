from google.cloud import firestore
from datetime import datetime
import itertools as it

GOOGLE_FIRESTORE_MAX_BATCH_SIZE = int(500)

class Firestore:
    def __init__(self):
        """
        Requires Project ID, determined by the GCLOUD_PROJECT environment variable
        """
        self.db = firestore.Client(project='expert-network-262703')
        self.dbcoll_test = self.db.collection(u'test')
        self.dbcoll_sites = self.db.collection(u'sites')
        self.all_sites_stream = self.dbcoll_sites.order_by(u'name').stream()
        self.all_sites_list = list(self.all_sites_stream)
        self.len_all_sites_list = len(self.all_sites_list)

    # def testWrite(self):
    #     doc_ref = self.dbcoll_test.document(u'test1')
    #
    #     doc_ref.set({
    #         u'datetime': datetime.now()
    #     }, merge=True)
    #
    # def testRead(self):
    #     doc_ref = self.dbcoll_test.document(u'test1')
    #
    #     try:
    #         doc = doc_ref.get()
    #         print(u'Document data: {}'.format(doc.to_dict()))
    #     except google.cloud.exceptions.NotFound:
    #         print(u'No such document!')

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

        print("page {page}, pagesize {pagesize}")
        for site in slice_list:
            print(u'{} => {}'.format(site.id, site.to_dict()))

        return return_dict


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
        return self.dict_site

    def write(self):
        self.dict_site["timestamp"] = firestore.SERVER_TIMESTAMP
        self.dbcoll_sites.document(self.site).set(self.dict_site, merge=True)
