# -*- coding: utf-8 -*-
import httplib as http

import mock
from nose.tools import *  # noqa
from boto.exception import S3ResponseError

from framework.auth import Auth
from tests.base import OsfTestCase, get_default_metaschema
from tests.factories import ProjectFactory, AuthUserFactory

from website.addons.base import testing
from website.addons.s3.provider import S3Provider
from website.addons.s3.settings import BUCKET_LOCATIONS
from website.addons.s3.tests.utils import S3AddonTestCase
from website.addons.s3.utils import validate_bucket_name, validate_bucket_location
from website.util import api_url_for


class TestS3Views(S3AddonTestCase, testing.views.OAuthAddonConfigViewsTestCaseMixin):
    def setUp(self):
        self.mock_can_list = mock.patch('website.addons.s3.views.utils.can_list')
        self.mock_can_list.return_value = True
        self.mock_can_list.start()
        self.mock_uid = mock.patch('website.addons.s3.views.utils.get_user_info')
        self.mock_uid.return_value = {'id': '1234567890', 'display_name': 's3.user'}
        self.mock_uid.start()
        self.mock_exists = mock.patch('website.addons.s3.views.utils.bucket_exists')
        self.mock_exists.return_value = True
        self.mock_exists.start()
        super(TestS3Views, self).setUp()

    def tearDown(self):
        self.mock_can_list.stop()
        self.mock_uid.stop()
        self.mock_exists.stop()
        super(TestS3Views, self).tearDown()

    def test_s3_settings_input_empty_keys(self):
        url = self.project.api_url_for('s3_add_user_account')
        rv = self.app.post_json(url,{
            'access_key': '',
            'secret_key': ''
        }, auth=self.user.auth, expect_errors=True)
        assert_equals(rv.status_int, http.BAD_REQUEST)
        assert_in('All the fields above are required.', rv.body)

    def test_s3_settings_input_empty_access_key(self):
        url = self.project.api_url_for('s3_add_user_account')
        rv = self.app.post_json(url,{
            'access_key': '',
            'secret_key': 'Non-empty-secret-key'
        }, auth=self.user.auth, expect_errors=True)
        assert_equals(rv.status_int, http.BAD_REQUEST)
        assert_in('All the fields above are required.', rv.body)

    def test_s3_settings_input_empty_secret_key(self):
        url = self.project.api_url_for('s3_add_user_account')
        rv = self.app.post_json(url,{
            'access_key': 'Non-empty-access-key',
            'secret_key': ''
        }, auth=self.user.auth, expect_errors=True)
        assert_equals(rv.status_int, http.BAD_REQUEST)
        assert_in('All the fields above are required.', rv.body)

    @mock.patch('website.addons.s3.views.utils.bucket_exists')
    def test_s3_set_no_bucket(self, _):
        self.node_settings.external_account = self.ExternalAccountFactory()
        self.node_settings.bucket = 'abucket'
        self.node_settings.save()
        assert_equal(self.node_settings.bucket, 'abucket')
        rv = self.app.put_json(
            self.project.api_url_for('s3_set_config'),
            {}, auth=self.user.auth
        )
        self.node_settings.reload()
        assert_equal(self.node_settings.bucket, '')

    def test_s3_set_bucket_no_settings(self):
        user = AuthUserFactory()
        self.project.add_contributor(user, save=True)
        url = self.project.api_url_for('s3_set_config')
        res = self.app.put_json(
            url, {'s3_bucket': 'hammertofall'}, auth=user.auth,
            expect_errors=True
        )
        assert_equal(res.status_code, http.BAD_REQUEST)

    def test_s3_set_bucket_no_auth(self):

        user = AuthUserFactory()
        user.add_addon('s3')
        self.project.add_contributor(user, save=True)
        url = self.project.api_url_for('s3_set_config')
        res = self.app.put_json(
            url, {'s3_bucket': 'hammertofall'}, auth=user.auth,
            expect_errors=True
        )
        assert_equal(res.status_code, http.FORBIDDEN)

    def test_s3_set_bucket_registered(self):
        registration = self.project.register_node(
            get_default_metaschema(), Auth(self.user), '', ''
        )

        url = registration.api_url_for('s3_set_config')
        res = self.app.put_json(
            url, {'s3_bucket': 'hammertofall'}, auth=self.user.auth,
            expect_errors=True,
        )

        assert_equal(res.status_code, http.BAD_REQUEST)

    @mock.patch('website.addons.s3.views.utils.can_list', return_value=False)
    def test_user_settings_cant_list(self, mock_can_list):
        url = api_url_for('s3_add_user_account')
        rv = self.app.post_json(url, {
            'access_key': 'aldkjf',
            'secret_key': 'las'
        }, auth=self.user.auth, expect_errors=True)
        assert_equals(rv.status_int, http.BAD_REQUEST)
        assert_in('Unable to list buckets.', rv.body)

    def test_s3_remove_node_settings_owner(self):
        url = self.node_settings.owner.api_url_for('s3_deauthorize_node')
        ret = self.app.delete(url, auth=self.user.auth)
        result = self.Serializer().serialize_settings(node_settings=self.node_settings, current_user=self.user)
        assert_equal(result['hasBucket'], False)
        assert_equal(result['nodeHasAuth'], False)

    def test_s3_remove_node_settings_unauthorized(self):
        url = self.node_settings.owner.api_url_for('s3_deauthorize_node')
        ret = self.app.delete(url, auth=None, expect_errors=True)

        assert_equal(ret.status_code, 401)

    def test_s3_get_node_settings_owner(self):
        self.node_settings.set_auth(self.external_account, self.user)
        self.node_settings.bucket = 'bucket'
        self.node_settings.save()
        url = self.node_settings.owner.api_url_for('s3_get_config')
        res = self.app.get(url, auth=self.user.auth)

        result = res.json['result']
        assert_equal(result['nodeHasAuth'], True)
        assert_equal(result['userIsOwner'], True)
        assert_equal(result['bucket'], self.node_settings.bucket)

    def test_s3_get_node_settings_unauthorized(self):
        url = self.node_settings.owner.api_url_for('s3_get_config')
        unauthorized = AuthUserFactory()
        ret = self.app.get(url, auth=unauthorized.auth, expect_errors=True)

        assert_equal(ret.status_code, 403)

    ## Overrides ##

    @mock.patch('website.addons.s3.views.utils.get_bucket_names')
    def test_folder_list(self, mock_names):
        mock_names.return_value = ['bucket1', 'bucket2']
        # pass
        super(TestS3Views, self).test_folder_list()

    def test_set_config(self):
        self.node_settings.external_account = self.ExternalAccountFactory()
        self.node_settings.save()
        url = self.project.api_url_for('{0}_set_config'.format(self.ADDON_SHORT_NAME))
        res = self.app.put_json(url, {
            's3_bucket': self.folder
        }, auth=self.user.auth)
        assert_equal(res.status_code, http.OK)
        self.project.reload()
        assert_equal(
            self.project.logs[-1].action,
            '{0}_bucket_linked'.format(self.ADDON_SHORT_NAME)
        )
        assert_equal(res.json['bucket'], self.folder)
        

class TestCreateBucket(S3AddonTestCase):

    def setUp(self):

        super(TestCreateBucket, self).setUp()

        self.user = AuthUserFactory()
        self.consolidated_auth = Auth(user=self.user)
        self.auth = self.user.auth
        self.project = ProjectFactory(creator=self.user)

        self.project.add_addon('s3', auth=self.consolidated_auth)
        self.project.creator.add_addon('s3')

        self.user_settings = self.user.get_addon('s3')
        self.user_settings.access_key = 'We-Will-Rock-You'
        self.user_settings.secret_key = 'Idontknowanyqueensongs'
        self.user_settings.save()

        self.node_settings = self.project.get_addon('s3')
        self.node_settings.bucket = 'Sheer-Heart-Attack'
        self.node_settings.user_settings = self.project.creator.get_addon('s3')

        self.node_settings.save()

    def test_bad_names(self):
        assert_false(validate_bucket_name('bogus naMe'))
        assert_false(validate_bucket_name(''))
        assert_false(validate_bucket_name('no'))
        assert_false(validate_bucket_name('.cantstartwithp'))
        assert_false(validate_bucket_name('or.endwith.'))
        assert_false(validate_bucket_name('..nodoubles'))
        assert_false(validate_bucket_name('no_unders_in'))

    def test_names(self):
        assert_true(validate_bucket_name('imagoodname'))
        assert_true(validate_bucket_name('still.passing'))
        assert_true(validate_bucket_name('can-have-dashes'))
        assert_true(validate_bucket_name('kinda.name.spaced'))

    def test_bad_locations(self):
        assert_false(validate_bucket_location('Venus'))
        assert_false(validate_bucket_location('AlphaCentari'))
        assert_false(validate_bucket_location('CostaRica'))

    def test_locations(self):
        assert_true(validate_bucket_location(''))
        assert_true(validate_bucket_location('EU'))
        assert_true(validate_bucket_location('us-west-1'))

    @mock.patch('website.addons.s3.views.utils.create_bucket')
    @mock.patch('website.addons.s3.views.utils.get_bucket_names')
    def test_create_bucket_pass(self, mock_names, mock_make):
        mock_make.return_value = True
        mock_names.return_value = [
            'butintheend',
            'it',
            'doesntevenmatter'
        ]
        url = self.project.api_url_for('create_bucket')
        ret = self.app.post_json(
            url,
            {
                'bucket_name': 'doesntevenmatter',
                'bucket_location': '',
            },
            auth=self.user.auth
        )

        assert_equals(ret.status_int, http.OK)
        assert_in('doesntevenmatter', ret.json['buckets'])

    @mock.patch('website.addons.s3.views.utils.create_bucket')
    def test_create_bucket_fail(self, mock_make):
        error = S3ResponseError(418, 'because Im a test')
        error.message = 'This should work'
        mock_make.side_effect = error

        url = "/api/v1/project/{0}/s3/newbucket/".format(self.project._id)
        ret = self.app.post_json(url, {'bucket_name': 'doesntevenmatter'}, auth=self.user.auth, expect_errors=True)

        assert_equals(ret.body, '{"message": "This should work", "title": "Problem connecting to S3"}')

    @mock.patch('website.addons.s3.views.utils.create_bucket')
    def test_bad_location_fails(self, mock_make):
        url = "/api/v1/project/{0}/s3/newbucket/".format(self.project._id)
        ret = self.app.post_json(
            url,
            {
                'bucket_name': 'doesntevenmatter',
                'bucket_location': 'not a real bucket location',
            },
            auth=self.user.auth,
            expect_errors=True)

        assert_equals(ret.body, '{"message": "That bucket location is not valid.", "title": "Invalid bucket location"}')
