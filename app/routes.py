from app import app
from app import stackoverflow

so = stackoverflow.StackOverflow()

@app.route('/')
@app.route('/index')
def index():
    list_results = so.query_stackoverflow()
    results_str = ""
    for row in list_results:
        result = "{} : {} views".format(row.url, row.view_count)
        results_str = results_str + result
    return results_str
