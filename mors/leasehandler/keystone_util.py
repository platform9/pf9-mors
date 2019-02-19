from cinderclient import client as cinderclient
from credsmgrclient.client import Client as credsmgrclient
from credsmgrclient.common import exceptions as credsexc
from keystoneauth1 import loading
from keystoneauth1.exceptions.catalog import EndpointNotFound
from keystoneclient.v3 import client as keystoneclient
from neutronclient.v2_0 import client as neutronclient
from novaclient import client as novaclient
from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class OSClient(object):

    def __init__(self):
        session = _register_keystoneauth_opts_get_session(CONF,
                                                          'service_auth')
        region_name = CONF.service_auth.region_name
        self.nova = novaclient.Client("2.1", session=session,
                                      region_name=region_name)
        self.cinder = cinderclient.Client("3", session=session,
                                          region_name=region_name)
        self.neutron = neutronclient.Client(session=session,
                                            region_name=region_name)
        self.keystone = keystoneclient.Client(session=session)
        try:
            credsmgr_url = session.get_endpoint(service_type='credsmgr',
                                                region_name=region_name)
            self.credsclient = credsmgrclient(credsmgr_url,
                                              token=session.get_token())
        except (EndpointNotFound, credsexc.HTTPBadGateway):
            LOG.error('Credentials Manager service is not running')
            self.credsclient = None


def _register_keystoneauth_opts_get_session(conf, section):
    loading.register_auth_conf_options(conf, section)
    loading.register_session_conf_options(conf, section)
    conf.register_opt(cfg.StrOpt('region_name'), group=section)
    auth = loading.load_auth_from_conf_options(conf, section)
    session = loading.load_session_from_conf_options(conf, section, auth=auth)
    return session