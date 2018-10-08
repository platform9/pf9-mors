"""
Copyright 2016 Platform9 Systems Inc.(http://www.platform9.com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from flask import Flask, request, jsonify
from lease_manager import LeaseManager
from context_util import enforce, get_context, error_handler
from flask.json import JSONEncoder
from datetime import datetime

DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
APP_NAME = "MORS"


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.strftime(DATE_FORMAT)
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


app = Flask(__name__)
app.debug = True
app.json_encoder = CustomJSONEncoder

lease_manager = None

@enforce(required=['admin'])
@app.route("/v1/tenant/", methods=['GET'], strict_slashes=False)
@error_handler
def get_all_tenants():
    all_tenants = lease_manager.get_tenant_leases(get_context())
    if all_tenants:
        return jsonify({"all_tenants":all_tenants})
    else:
        return jsonify({}), 200, {'ContentType': 'application/json'}

@enforce(required=['_member_'])
@app.route("/v1/tenant/<tenant_id>", methods=['GET'])
@error_handler
def get_tenant(tenant_id):
    tenant_lease = lease_manager.get_tenant_lease(get_context(), tenant_id)
    if not tenant_lease:
        return jsonify({'success': False}), 404, {'ContentType': 'application/json'}
    return jsonify(tenant_lease)


@enforce(required=['admin'])
@app.route("/v1/tenant/<tenant_id>", methods=['PUT', 'POST'])
@error_handler
def add_update_tenant(tenant_id):
    tenant_lease = request.get_json()["vm_lease_policy"]
    if request.method == "POST":
        lease_manager.add_tenant_lease(get_context(), tenant_lease)
    else:
        lease_manager.update_tenant_lease(get_context(), tenant_lease)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}

@enforce(required=['admin'])
@app.route("/v1/tenant/<tenant_id>", methods=['DELETE'])
@error_handler
def delete_tenant_lease(tenant_id):
    lease_manager.delete_tenant_lease(get_context(), tenant_id)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}

#-- Instance - tenant related

@enforce(required=['_member_'])
@app.route("/v1/tenant/<tenant_id>/instances/", methods=['GET'], strict_slashes=False)
@error_handler
def get_tenant_and_instances(tenant_id):
    instances = lease_manager.get_tenant_and_associated_instance_leases(get_context(), tenant_id)
    if not instances:
        return jsonify({'success': False}), 404, {'ContentType': 'application/json'}
    return jsonify(instances)

# --- Instance related ---
@enforce(required=['_member_'])
@app.route("/v1/tenant/<tenant_id>/instance/<instance_id>", methods=['GET'])
@error_handler
def get_vm_lease(tenant_id, instance_id):
    lease_info = lease_manager.get_instance_lease(get_context(), instance_id)
    if lease_info:
        return jsonify(lease_info), 200, {'ContentType': 'application/json'}
    else:
        return jsonify({'error': 'Not found'}), 404, {'ContentType': 'application/json'}

@enforce(required=['_member_'])
@app.route("/v1/tenant/<tenant_id>/instance/<instance_id>", methods=['DELETE'])
@error_handler
def delete_vm_lease(tenant_id, instance_id):
    lease_manager.delete_instance_lease(get_context(), instance_id)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}

@enforce(required=['_member_'])
@app.route("/v1/tenant/<tenant_id>/instance/<instance_id>", methods=['PUT', 'POST'])
@error_handler
def add_update_vm_lease(tenant_id, instance_id):
    lease_obj = request.get_json()
    # ds = '2012-03-01T10:00:00Z' # or any date sting of differing formats.
    date = datetime.strptime(lease_obj['expiry'], DATE_FORMAT)
    lease_obj['expiry'] = date
    if request.method == "POST":
        lease_manager.add_instance_lease(get_context(), tenant_id, lease_obj)
    else:
        lease_manager.update_instance_lease(get_context(), tenant_id, lease_obj)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


# --- Webhooks related ---
@enforce(required=['_member_'])
@app.route("/v1/webhooks", methods=['PUT', 'POST'])
@error_handler
def add_webhook():
    webhook_obj = request.get_json()
    tenant_id = webhook_obj.get('tenant_id')
    instance_id = webhook_obj.get('instance_id')
    if not tenant_id and not instance_id:
        return jsonify({'error': 'Specify tenant_id or instance_id'}), 400, {'ContentType': 'application/json'}
    if request.method == "POST":
        lease_manager.add_webhook(
            get_context(), webhook_obj['url'],
            webhook_obj['method'], webhook_obj['retry_attempts'],
            webhook_obj['body'], webhook_obj['content_type'],
            tenant_id, instance_id)
    else:
        lease_manager.update_instance_webhook(
            get_context(), tenant_id, webhook_obj)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@enforce(required=['_member_'])
@app.route("/v1/webhooks/<res_type>/<res_id>", methods=['GET'])
@error_handler
def get_webhook(res_type='all', res_id='all'):
    webhooks_info = lease_manager.get_webhook(get_context(), res_type, res_id)
    if webhooks_info:
        return jsonify({"webhooks": webhooks_info})
    else:
        return jsonify({}), 200, {'ContentType': 'application/json'}


@enforce(required=['_member_'])
@app.route("/v1/webhooks/delete", methods=['POST'])
@error_handler
def delete_webhook():
    webhook_obj = request.get_json()
    lease_manager.delete_instance_webhook(get_context(), webhook_obj['url'])
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


def start_server(conf):
    global lease_manager
    lease_manager = LeaseManager(conf)
    lease_manager.start()


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


def app_factory(global_config, **local_conf):
    return app
