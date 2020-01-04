from flask import Flask
from flask_bootstrap import Bootstrap
import click
from flask import Flask
from flask.cli import AppGroup
from flask import current_app, render_template
from flask_restful import reqparse
from flask import jsonify
import json
import requests
from app import stackoverflow

app = Flask(__name__)
user_cli = AppGroup('admin')
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

    site_obj = so.firestore.get_site_from_name(site)
    if site_obj is not None:
        list_dict_experts = {}
        list_experts = site_obj.expert_list
        list_expert_objects = []
        dict_experts = {}
        # print(f'Expert list {list_experts}')
        for user_id in list_experts:
            if isinstance(user_id, int):
                expert = so.firestore.get_expert_from_id(user_id)
                if expert is not None:
                    list_expert_objects.append(expert)
                    dict_experts[expert.expert_key] = expert.to_dict()
        # print(f'Site: {site_obj.to_dict()}')
        dict_site_experts = {
            "site_site": site,
            "site": site_obj.to_dict(),
            "list_experts": list_experts,
            "dict_experts": dict_experts,
            "page": get_page(args),
            "pagesize": get_pagesize(args),
            "has_more": False
        }
        message = {
            'status': 200,
            'message': 'OK',
            'dict_site_experts': dict_site_experts
        }

    if "error" in message:
        return render_template('error.html', error=message["message"], url="")
    else:
        return render_template('top_rep.html', title="Top Experts", name=site_obj.name, site=site_obj, dict_site_experts=dict_site_experts)


@app.cli.command('import_experts')
@click.argument('test_val')
def admin_import_experts(test_val):
    message = {
        'message': 'OK'
    }

    test = test_val == "true"
    print(f'Test mode: {test}')
    dict_return = so.admin_import_experts(test)
    if "error" in dict_return:
        message["message"] = json.dumps(dict_return)

    else:
        message['count_imported_experts'] = dict_return["num_imported"]

    return jsonify(message)


@app.cli.command('get_site')
@click.argument('site_name')
def get_site(site_name):
    site = so.firestore.get_site_from_name(site_name)

    message = {
        'message': 'OK',
        'site_name': site_name,
        'site_dict': site.to_dict()
    }
    print(message)
    return jsonify(message)


@app.cli.command('import_sites')
@click.argument('test_val')
def admin_import_sites(test_val):
    dict_return = so.admin_import_sites(page=1, test=False)
    message = {
        'message': 'OK',
        'count_imported_sites': dict_return["num_imported"]
    }
    print(message)

    return jsonify(message)


@user_cli.command('delete_sites')
def admin_delete_sites():
    message = {
        'message': 'OK',
        'count_deleted_sites': so.admin_delete_sites()
    }
    resp = jsonify(message)
    print(message)

    return resp


Bootstrap(app)
app.cli.add_command(user_cli)
