#!/usr/bin/python

import argparse
import copy
import os
import sys
import re
import json

from argo_egi_connectors import input
from argo_egi_connectors import output
from argo_egi_connectors.log import Logger

from argo_egi_connectors.config import Global, CustomerConf
from argo_egi_connectors.helpers import filename_date, module_class_name, datestamp, date_check
from urlparse import urlparse


def is_feed(feed):
    data = urlparse(feed)

    if not data.netloc:
        return False
    else:
        return True


class EOSCReader(object):
    def __init__(self, data):
        self.data = data

    def _construct_fqdn(self, http_endpoint):
        return urlparse(http_endpoint).netloc

    def get_groupgroups(self):
        groups = dict()

        for entity in self.data:
            tmp_dict = dict()

            tmp_dict['type'] = 'PROJECT'
            tmp_dict['group'] = 'EOSC'
            tmp_dict['subgroup'] = entity['SITENAME-SERVICEGROUP']
            tmp_dict['tags'] = {'monitored' : '1', 'scope' : 'EOSC'}

            groups.update(tmp_dict)

        return groups

    def get_groupendpoints(self):
        groups = dict()

        for entity in self.data:
            tmp_dict = dict()

            tmp_dict['type'] = 'SERVICEGROUPS'
            tmp_dict['group'] = entity['SITENAME-SERVICEGROUP']
            tmp_dict['service'] = entity['SERVICE_TYPE']
            tmp_dict['hostname'] = '{1}_{0}'.format(entity['Service Unique ID'], self._construct_fqdn(entity['URL']))
            tmp_dict['tags'] = {'scope': 'EOSC', 'monitored': '1'}

            groups.update(tmp_dict)

        return groups


def main():
    global logger, globopts, confcust
    parser = argparse.ArgumentParser(description="""Fetch and construct entities from EOSC-PORTAL feed""")
    parser.add_argument('-c', dest='custconf', nargs=1, metavar='customer.conf', help='path to customer configuration file', type=str, required=False)
    parser.add_argument('-g', dest='gloconf', nargs=1, metavar='global.conf', help='path to global configuration file', type=str, required=False)
    parser.add_argument('-d', dest='date', metavar='YEAR-MONTH-DAY', help='write data for this date', type=str, required=False)
    args = parser.parse_args()
    group_endpoints, group_groups = [], []
    logger = Logger(os.path.basename(sys.argv[0]))

    fixed_date = None
    if args.date and date_check(args.date):
        fixed_date = args.date

    confpath = args.gloconf[0] if args.gloconf else None
    cglob = Global(sys.argv[0], confpath)
    globopts = cglob.parse()

    confpath = args.custconf[0] if args.custconf else None
    confcust = CustomerConf(sys.argv[0], confpath)
    confcust.parse()
    confcust.make_dirstruct()
    confcust.make_dirstruct(globopts['InputStateSaveDir'.lower()])

    for cust in confcust.get_customers():
        custname = confcust.get_custname(cust)

        for job in confcust.get_jobs(cust):
            state = None

            logger.customer = confcust.get_custname(cust)
            logger.job = job

            jobstatedir = confcust.get_fullstatedir(globopts['InputStateSaveDir'.lower()], cust, job)

            custname = confcust.get_custname(cust)
            ams_custopts = confcust.get_amsopts(cust)
            ams_opts = cglob.merge_opts(ams_custopts, 'ams')
            ams_complete, missopt = cglob.is_complete(ams_opts, 'ams')

            feeds = confcust.get_mapfeedjobs(sys.argv[0])
            if is_feed(feeds.keys()[0]):
                # TODO: handle case when topology will be served remotely
                pass
            else:
                try:
                    with open(feeds.keys()[0]) as fp:
                        js = json.load(fp)
                        eosc = EOSCReader(js)
                        group_groups = eosc.get_groupgroups()
                        group_endpoints = eosc.get_groupendpoints()
                        state = True
                except IOError as exc:
                    logger.error('Customer:%s Job:%s : Problem opening %s - %s' % (logger.customer, logger.job, feeds.keys()[0], repr(exc)))
                    state = False

            if fixed_date:
                output.write_state(sys.argv[0], jobstatedir, state,
                                   globopts['InputStateDays'.lower()],
                                   fixed_date.replace('-', '_'))
            else:
                output.write_state(sys.argv[0], jobstatedir, state,
                                   globopts['InputStateDays'.lower()])



if __name__ == '__main__':
    main()

