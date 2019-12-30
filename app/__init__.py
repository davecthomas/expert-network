from flask import Flask
from flask_bootstrap import Bootstrap
import click
from flask import Flask
from flask.cli import AppGroup
from flask import jsonify
import json
from app import stackoverflow

app = Flask(__name__)
user_cli = AppGroup('admin')
so = stackoverflow.StackOverflow()


@user_cli.command('import_experts')
def admin_import_experts():
    message = {
        'message': 'OK'
    }

    dict_return = so.admin_import_experts()
    if "error" in dict_return:
        message["message"] = json.dumps(dict_return)

    else:
        message['count_imported_experts'] = dict_return["num_imported"]

    return jsonify(message)


@user_cli.command('import_sites')
def admin_import_sites():
    dict_return = so.admin_import_sites(page=1)
    message = {
        'message': 'OK',
        'count_imported_sites': dict_return["num_imported"]
    }

    return jsonify(message)


@user_cli.command('delete_sites')
def admin_delete_sites():
    message = {
        'message': 'OK',
        'count_deleted_sites': so.admin_delete_sites()
    }
    resp = jsonify(message)

    return resp


Bootstrap(app)
app.cli.add_command(user_cli)
