from app import app
from app import stackoverflow
from flask import render_template

so = stackoverflow.StackOverflow()


@app.route('/')
@app.route('/index')
def index():
    return "Enter command in url"


@app.route('/sites')
def sites():
    return so.get_sites()


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
