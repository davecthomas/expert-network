from app import app
from app import stackoverflow
from flask import current_app, render_template

so = stackoverflow.StackOverflow()


@app.route('/')
@app.route('/index')
def index():
    return "Enter command in url"


@app.route('/sites')
def sites():
    return_dict = so.get_sites()
    return render_template('sites.html', return_dict=return_dict)


@app.route('/comments')
def comments():
    return so.get_comments()


@app.route('/bigquery')
def bigquery():
    list_results = so.query_stackoverflow()
    results_str = ""
    for row in list_results:
        result = "{} : {} views".format(row.url, row.view_count)
        results_str = results_str + result
    return results_str
