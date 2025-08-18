#!/usr/local/bin/python
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

import eventlet
eventlet.monkey_patch()
from eventlet import wsgi
from paste.deploy import loadapp
import argparse, logging
import logging.handlers
import sys
from mors import mors_wsgi
from mors.constants import ROOT_LOGGER

from six.moves.configparser import ConfigParser


def _get_arg_parser():
    parser = argparse.ArgumentParser(description="Lease Manager for VirtualMachines")
    parser.add_argument('--config-file', dest='config_file', default='/etc/pf9/pf9-mors.ini')
    parser.add_argument('--paste-ini', dest='paste_file')
    return parser.parse_args()

def _configure_logging(conf):
    log_level = conf.get(
        "DEFAULT",
        "log_level",
        fallback=logging.INFO,
    )
    log_file = conf.get("DEFAULT", "log_file")
    log_format = logging.Formatter('%(asctime)s %(name)-12s %(levelname)s %(message)s')
    logger = logging.getLogger(ROOT_LOGGER)
    logger.setLevel(log_level)
    file_handler = logging.handlers.RotatingFileHandler(log_file,
                                                   maxBytes=1024 * 1024 * 5,
                                                   backupCount=5)
    stderr_handler = logging.StreamHandler(stream=sys.stderr)

    for handler in logger.handlers:                                                         
        logger.removeHandler(handler)

    our_handlers = [stderr_handler, file_handler]
    for handler in our_handlers:
        handler.setLevel(log_level)
        handler.setFormatter(log_format)
        logger.addHandler(handler)


def start_server(conf, paste_ini):
    _configure_logging(conf)
    paste_file = None
    if paste_ini:
        paste_file = paste_ini
    else:
        paste_file = conf.get("DEFAULT", "paste-ini")

    wsgi_app = loadapp('config:%s' % paste_file, 'main')
    mors_wsgi.start_server(conf)
    wsgi.server(eventlet.listen(('', conf.getint("DEFAULT", "listen_port"))), wsgi_app)


if __name__ == '__main__':
    parser = _get_arg_parser()
    conf = ConfigParser()
    conf.readfp(open(parser.config_file))
    start_server(conf, parser.paste_file)
