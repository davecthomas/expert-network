from app import app
from app import stackoverflow
from flask import current_app, render_template
from flask_restful import reqparse

so = stackoverflow.StackOverflow()
parser = reqparse.RequestParser()


def get_page(args):
    if args.page is None:
        page = int(1)
    else:
        page = int(args.page)
        if not isinstance(page, int):
            page = int(1)
    return page


def get_pagesize(args):
    if args.pagesize is None:
        pagesize = int(15)
    else:
        pagesize = int(args.pagesize)
        if not isinstance(pagesize, int):
            pagesize = int(15)
    return pagesize


@app.route('/')
@app.route('/index')
def index():
    return "Enter command in url"


@app.route('/sites')
def sites():
    parser.add_argument('page', location='args')
    parser.add_argument('pagesize', location='args')

    args = parser.parse_args()

    return_dict = so.get_sites(get_page(args), get_pagesize(args))
    if "error" in return_dict:
        return render_template('error.html', error=return_dict["error"], url=return_dict["url"])
    else:
        return render_template('sites.html', title="Top Sites", return_dict=return_dict)


@app.route('/users_rep')
def users_rep():
    parser.add_argument('page', location='args')
    parser.add_argument('pagesize', location='args')
    parser.add_argument('site', location='args')
    parser.add_argument('name', location='args')

    args = parser.parse_args()
    if args.name is None:
        name = ""
    else:
        name = args.name

    if args.site is None:
        site = ""
    else:
        site = args.site

    return_dict = so.get_top_users_reputation(site, get_page(args), get_pagesize(args))
    if "error" in return_dict:
        return render_template('error.html', error=return_dict["error"], url=return_dict["url"])
    else:
        return render_template('top_rep.html', title="Top Experts", name=name, site=site, return_dict=return_dict)


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
