from google.cloud import firestore
from datetime import datetime

GOOGLE_FIRESTORE_MAX_BATCH_SIZE = int(500)

class Firestore:
    def __init__(self):
        """
        Requires Project ID, determined by the GCLOUD_PROJECT environment variable
        """
        self.db = firestore.Client(project='expert-network-262703')
        self.dbcoll_test = self.db.collection(u'test')
        self.dbcoll_sites = self.db.collection(u'sites')

    def testWrite(self):
        doc_ref = self.dbcoll_test.document(u'test1')

        doc_ref.set({
            u'datetime': datetime.now()
        }, merge=True)

    def testRead(self):
        doc_ref = self.dbcoll_test.document(u'test1')

        try:
            doc = doc_ref.get()
            print(u'Document data: {}'.format(doc.to_dict()))
        except google.cloud.exceptions.NotFound:
            print(u'No such document!')

    # Store a batch of up to 500 sites (limited by Google Cloud Batch transaction limits)
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
        sites = self.dbcoll_sites.stream()
        print("Deleting sites:")
        batch = self.db.batch()
        count_deleted = 0
        for site in sites:
            # print(u'{} => {}'.format(site.id, site.to_dict()))
            batch.delete(self.dbcoll_sites.document(site.id))
            count_deleted = count_deleted + 1
        # Commit the delete
        batch.commit()
        return count_deleted


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
