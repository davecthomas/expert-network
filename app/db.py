from google.cloud import firestore
from datetime import datetime


class Firestore:
    def __init__(self):
        """
        Requires Project ID, determined by the GCLOUD_PROJECT environment variable
        """
        self.db = firestore.Client(project='expert-network-262703')
        self.dbcoll_test = self.db.collection(u'test')
        self.dbcoll_sites = self.db.collection(u'sites')


    def testWrite(self ):
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
        dict = self.to_dict()
        dict["timestamp"] = firestore.SERVER_TIMESTAMP
        self.dbcoll_sites.document(self.site).set(self.to_dict(), merge=True)

