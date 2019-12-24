from google.cloud import bigquery


class StackOverflow:
    def __init__(self):
        """
        Get properties and get connected
        """
        self.dict_results = {}

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

