# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

import superdesk
from eve.utils import ParsedRequest
from superdesk.tests import TestCase
from superdesk import get_resource_service
from superdesk.data_consistency.compare_repositories import CompareRepositories
from eve.methods.common import resolve_document_etag
from time import sleep


class RebuildIndexTestCase(TestCase):

    def setUp(self):
        super().setUp()
        with self.app.app_context():
            data = [{'headline': 'test {}'.format(i), 'slugline': 'rebuild {}'.format(i),
                     'type': 'text' if (i % 2 == 0) else 'picture'} for i in range(1, 100)]
            resolve_document_etag(data, 'archive')
            superdesk.app.data._search_backend('archive').bulk_insert('archive', data)
            get_resource_service('archive').post(data)
            sleep(1)  # sleep so Elastic has time to refresh the indexes

    def test_compare_repos(self):
        with self.app.app_context():
            req = ParsedRequest()
            req.args = {}
            req.max_results = 25

            items = get_resource_service('archive').get(req, {})
            self.assertEquals(99, items.count())

            consistency_record = CompareRepositories().run('archive',
                                                           self.app.config['ELASTICSEARCH_URL'],
                                                           self.app.config['ELASTICSEARCH_INDEX'])
            self.assertEquals(consistency_record['mongo'], 99)
            self.assertEquals(consistency_record['elastic'], 198)
            self.assertEquals(consistency_record['identical'], 99)
            self.assertEquals(consistency_record['mongo_only'], 0)
            self.assertEquals(consistency_record['elastic_only'], 99)
            self.assertEquals(consistency_record['inconsistent'], 99)
