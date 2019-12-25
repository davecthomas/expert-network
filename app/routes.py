from app import app
from app import stackoverflow
from flask import current_app, render_template
from flask_restful import reqparse

so = stackoverflow.StackOverflow()
parser = reqparse.RequestParser()

@app.route('/')
@app.route('/index')
def index():
    return "Enter command in url"


@app.route('/sites')
def sites():
    parser.add_argument('page', location='args')
    parser.add_argument('pagesize', location='args')

    args = parser.parse_args()
    if args.page is None:
        page = 1
    else:
        page = int(args.page)
        if not isinstance(page, int):
            page = 1

    if args.pagesize is None:
        page = 1
    else:
        page = int(args.page)
        if not isinstance(page, int):
            page = 1
    return_dict = so.get_sites(page)
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
