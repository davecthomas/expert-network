from app import app
from app import stackoverflow
from flask import current_app, render_template
from flask_restful import reqparse
from flask import jsonify
import json

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

    return_dict = so.get_sites_by_page(get_page(args), get_pagesize(args))
    if "error" in return_dict:
        return render_template('error.html', error=return_dict["error"], url=return_dict["url"])
    else:
        return render_template('sites.html', title="Top Sites", return_dict=return_dict)


@app.route('/admin/load_sites')
def admin_load_sites():
    dict_return = so.admin_load_sites(page=1)
    message = {
            'status': 200,
            'message': 'OK',
            'count_loaded_sites': dict_return["num_loaded"]
    }
    # Debug
    # for site in dict_return["list_sites"]:
    #     print(site.site)
    resp = jsonify(message)
    resp.status_code = 200

    return resp


@app.route('/admin/delete_sites')
def admin_delete_sites():
    message = {
            'status': 200,
            'message': 'OK',
            'count_deleted_sites': so.admin_delete_sites()
    }
    resp = jsonify(message)
    resp.status_code = 200

    return resp


@app.route('/admin/load_experts')
def admin_load_experts():
    dict_return = so.admin_load_experts()
    if "error" in dict_return:
        message = {
            'status': json.dumps(dict_return)
        }
    else:
        message = {
                'status': 200,
                'message': 'OK',
                'count_loaded_experts': dict_return["num_loaded"]
        }
    # Debug
    # for site in dict_return["list_sites"]:
    #     print(site.site)
    resp = jsonify(message)
    resp.status_code = 200

    return resp


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

#
# @app.route('/comments')
# def comments():
#     return so.get_comments()

#
# @app.route('/bigquery')
# def bigquery():
#     list_results = so.query_stackoverflow()
#     results_str = ""
#     for row in list_results:
#         result = "{} : {} views".format(row.url, row.view_count)
#         results_str = results_str + result
#     return results_str
