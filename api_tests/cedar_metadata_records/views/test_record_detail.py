import pytest
from urllib.parse import urlparse

from .test_record import TestCedarMetadataRecord

from api.base.settings import API_BASE, API_PRIVATE_BASE

from osf.utils.permissions import READ, WRITE

from osf_tests.factories import AuthUserFactory

@pytest.mark.django_db
class TestCedarMetadataRecordDetailPrivateProjectPublishedMetadata(TestCedarMetadataRecord):

    def test_record_detail_for_node_with_admin_auth(self, app, node, user, cedar_template, cedar_record_for_node, cedar_record_metadata_json):

        admin = user
        resp = app.get(f'/_/cedar_metadata_records/{cedar_record_for_node._id}/', auth=admin.auth)
        assert resp.status_code == 200
        data = resp.json['data']

        assert data['id'] == cedar_record_for_node._id
        assert data['type'] == 'cedar-metadata-records'
        assert data['attributes']['metadata'] == cedar_record_metadata_json
        assert data['attributes']['is_published'] is True
        assert data['relationships']['target']['data'] == {'id': node._id, 'type': 'nodes'}
        assert urlparse(data['relationships']['target']['links']['related']['href']).path == f'/{API_BASE}nodes/{node._id}/'
        assert data['relationships']['template']['data'] == {'id': cedar_template._id, 'type': 'cedar-metadata-templates'}
        assert urlparse(data['relationships']['template']['links']['related']['href']).path == f'/{API_PRIVATE_BASE}cedar_metadata_templates/{cedar_template._id}/'
        assert urlparse(data['links']['self']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node._id}/'
        assert urlparse(data['links']['metadata_download']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node._id}/metadata_download/'

    def test_record_detail_for_node_with_write_auth(self, app, node, cedar_template, cedar_record_for_node, cedar_record_metadata_json):

        write = AuthUserFactory()
        node.add_contributor(write, permissions=WRITE)
        node.save()
        resp = app.get(f'/_/cedar_metadata_records/{cedar_record_for_node._id}/', auth=write.auth)
        assert resp.status_code == 200
        data = resp.json['data']

        assert data['id'] == cedar_record_for_node._id
        assert data['type'] == 'cedar-metadata-records'
        assert data['attributes']['metadata'] == cedar_record_metadata_json
        assert data['attributes']['is_published'] is True
        assert data['relationships']['target']['data'] == {'id': node._id, 'type': 'nodes'}
        assert urlparse(data['relationships']['target']['links']['related']['href']).path == f'/{API_BASE}nodes/{node._id}/'
        assert data['relationships']['template']['data'] == {'id': cedar_template._id, 'type': 'cedar-metadata-templates'}
        assert urlparse(data['relationships']['template']['links']['related']['href']).path == f'/{API_PRIVATE_BASE}cedar_metadata_templates/{cedar_template._id}/'
        assert urlparse(data['links']['self']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node._id}/'
        assert urlparse(data['links']['metadata_download']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node._id}/metadata_download/'

    def test_record_detail_for_node_with_read_auth(self, app, node, user, cedar_template, cedar_record_for_node, cedar_record_metadata_json):

        read = AuthUserFactory()
        node.add_contributor(read, permissions=READ)
        node.save()
        resp = app.get(f'/_/cedar_metadata_records/{cedar_record_for_node._id}/', auth=read.auth)
        assert resp.status_code == 200
        data = resp.json['data']

        assert data['id'] == cedar_record_for_node._id
        assert data['type'] == 'cedar-metadata-records'
        assert data['attributes']['metadata'] == cedar_record_metadata_json
        assert data['attributes']['is_published'] is True
        assert data['relationships']['target']['data'] == {'id': node._id, 'type': 'nodes'}
        assert urlparse(data['relationships']['target']['links']['related']['href']).path == f'/{API_BASE}nodes/{node._id}/'
        assert data['relationships']['template']['data'] == {'id': cedar_template._id, 'type': 'cedar-metadata-templates'}
        assert urlparse(data['relationships']['template']['links']['related']['href']).path == f'/{API_PRIVATE_BASE}cedar_metadata_templates/{cedar_template._id}/'
        assert urlparse(data['links']['self']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node._id}/'
        assert urlparse(data['links']['metadata_download']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node._id}/metadata_download/'

    # TODO: discuss and fix permission
    @pytest.mark.skip(reason='discuss and fix permission')
    def test_record_detail_for_node_with_invalid_auth(self, app, user_alt, cedar_record_for_node):

        resp = app.get(f'/_/cedar_metadata_records/{cedar_record_for_node._id}/', auth=user_alt.auth)
        assert resp.status_code == 401

    # TODO: discuss and fix permission
    @pytest.mark.skip(reason='discuss and fix permission')
    def test_record_detail_for_node_with_no_auth(self, app, cedar_record_for_node):
        resp = app.get(f'/_/cedar_metadata_records/{cedar_record_for_node._id}/', auth=None)
        assert resp.status_code == 401


@pytest.mark.django_db
class TestCedarMetadataRecordDetailPrivateProjectDraftMetadata(TestCedarMetadataRecord):

    def test_record_detail_for_node_with_admin_auth(self, app, node_alt, user, cedar_template, cedar_draft_record_for_node_alt, cedar_record_metadata_json):

        admin = user
        resp = app.get(f'/_/cedar_metadata_records/{cedar_draft_record_for_node_alt._id}/', auth=admin.auth)
        assert resp.status_code == 200
        data = resp.json['data']

        assert data['id'] == cedar_draft_record_for_node_alt._id
        assert data['type'] == 'cedar-metadata-records'
        assert data['attributes']['metadata'] == cedar_record_metadata_json
        assert data['attributes']['is_published'] is False
        assert data['relationships']['target']['data'] == {'id': node_alt._id, 'type': 'nodes'}
        assert urlparse(data['relationships']['target']['links']['related']['href']).path == f'/{API_BASE}nodes/{node_alt._id}/'
        assert data['relationships']['template']['data'] == {'id': cedar_template._id, 'type': 'cedar-metadata-templates'}
        assert urlparse(data['relationships']['template']['links']['related']['href']).path == f'/{API_PRIVATE_BASE}cedar_metadata_templates/{cedar_template._id}/'
        assert urlparse(data['links']['self']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_draft_record_for_node_alt._id}/'
        assert urlparse(data['links']['metadata_download']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_draft_record_for_node_alt._id}/metadata_download/'

    def test_record_detail_for_node_with_write_auth(self, app, node_alt, cedar_template, cedar_draft_record_for_node_alt, cedar_record_metadata_json):

        write = AuthUserFactory()
        node_alt.add_contributor(write, permissions=WRITE)
        node_alt.save()
        resp = app.get(f'/_/cedar_metadata_records/{cedar_draft_record_for_node_alt._id}/', auth=write.auth)
        assert resp.status_code == 200
        data = resp.json['data']

        assert data['id'] == cedar_draft_record_for_node_alt._id
        assert data['type'] == 'cedar-metadata-records'
        assert data['attributes']['metadata'] == cedar_record_metadata_json
        assert data['attributes']['is_published'] is False
        assert data['relationships']['target']['data'] == {'id': node_alt._id, 'type': 'nodes'}
        assert urlparse(data['relationships']['target']['links']['related']['href']).path == f'/{API_BASE}nodes/{node_alt._id}/'
        assert data['relationships']['template']['data'] == {'id': cedar_template._id, 'type': 'cedar-metadata-templates'}
        assert urlparse(data['relationships']['template']['links']['related']['href']).path == f'/{API_PRIVATE_BASE}cedar_metadata_templates/{cedar_template._id}/'
        assert urlparse(data['links']['self']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_draft_record_for_node_alt._id}/'
        assert urlparse(data['links']['metadata_download']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_draft_record_for_node_alt._id}/metadata_download/'

    # TODO: discuss and fix permission
    @pytest.mark.skip(reason='discuss and fix permission')
    def test_record_detail_for_node_with_read_auth(self, app, node_alt, cedar_draft_record_for_node_alt):

        read = AuthUserFactory()
        node_alt.add_contributor(read, permissions=READ)
        node_alt.save()

        resp = app.get(f'/_/cedar_metadata_records/{cedar_draft_record_for_node_alt._id}/', auth=read.auth)
        assert resp.status_code == 401

    # TODO: discuss and fix permission
    @pytest.mark.skip(reason='discuss and fix permission')
    def test_record_detail_for_node_with_invalid_auth(self, app, user_alt, cedar_draft_record_for_node_alt):

        resp = app.get(f'/_/cedar_metadata_records/{cedar_draft_record_for_node_alt._id}/', auth=user_alt.auth)
        assert resp.status_code == 401

    # TODO: discuss and fix permission
    @pytest.mark.skip(reason='discuss and fix permission')
    def test_record_detail_for_node_with_no_auth(self, app, cedar_draft_record_for_node_alt):
        resp = app.get(f'/_/cedar_metadata_records/{cedar_draft_record_for_node_alt._id}/', auth=None)
        assert resp.status_code == 401


@pytest.mark.django_db
class TestCedarMetadataRecordDetailPublicProjectPublishedMetadata(TestCedarMetadataRecord):

    def test_record_detail_for_node_with_admin_auth(self, app, node_pub, user, cedar_template, cedar_record_for_node_pub, cedar_record_metadata_json):

        admin = user
        resp = app.get(f'/_/cedar_metadata_records/{cedar_record_for_node_pub._id}/', auth=admin.auth)
        assert resp.status_code == 200
        data = resp.json['data']

        assert data['id'] == cedar_record_for_node_pub._id
        assert data['type'] == 'cedar-metadata-records'
        assert data['attributes']['metadata'] == cedar_record_metadata_json
        assert data['attributes']['is_published'] is True
        assert data['relationships']['target']['data'] == {'id': node_pub._id, 'type': 'nodes'}
        assert urlparse(data['relationships']['target']['links']['related']['href']).path == f'/{API_BASE}nodes/{node_pub._id}/'
        assert data['relationships']['template']['data'] == {'id': cedar_template._id, 'type': 'cedar-metadata-templates'}
        assert urlparse(data['relationships']['template']['links']['related']['href']).path == f'/{API_PRIVATE_BASE}cedar_metadata_templates/{cedar_template._id}/'
        assert urlparse(data['links']['self']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node_pub._id}/'
        assert urlparse(data['links']['metadata_download']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node_pub._id}/metadata_download/'

    def test_record_detail_for_node_with_write_auth(self, app, node_pub, cedar_template, cedar_record_for_node_pub, cedar_record_metadata_json):

        write = AuthUserFactory()
        node_pub.add_contributor(write, permissions=WRITE)
        node_pub.save()
        resp = app.get(f'/_/cedar_metadata_records/{cedar_record_for_node_pub._id}/', auth=write.auth)
        assert resp.status_code == 200
        data = resp.json['data']

        assert data['id'] == cedar_record_for_node_pub._id
        assert data['type'] == 'cedar-metadata-records'
        assert data['attributes']['metadata'] == cedar_record_metadata_json
        assert data['attributes']['is_published'] is True
        assert data['relationships']['target']['data'] == {'id': node_pub._id, 'type': 'nodes'}
        assert urlparse(data['relationships']['target']['links']['related']['href']).path == f'/{API_BASE}nodes/{node_pub._id}/'
        assert data['relationships']['template']['data'] == {'id': cedar_template._id, 'type': 'cedar-metadata-templates'}
        assert urlparse(data['relationships']['template']['links']['related']['href']).path == f'/{API_PRIVATE_BASE}cedar_metadata_templates/{cedar_template._id}/'
        assert urlparse(data['links']['self']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node_pub._id}/'
        assert urlparse(data['links']['metadata_download']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node_pub._id}/metadata_download/'

    def test_record_detail_for_node_with_read_auth(self, app, node_pub, user, cedar_template, cedar_record_for_node_pub, cedar_record_metadata_json):

        read = AuthUserFactory()
        node_pub.add_contributor(read, permissions=READ)
        node_pub.save()
        resp = app.get(f'/_/cedar_metadata_records/{cedar_record_for_node_pub._id}/', auth=read.auth)
        assert resp.status_code == 200
        data = resp.json['data']

        assert data['id'] == cedar_record_for_node_pub._id
        assert data['type'] == 'cedar-metadata-records'
        assert data['attributes']['metadata'] == cedar_record_metadata_json
        assert data['attributes']['is_published'] is True
        assert data['relationships']['target']['data'] == {'id': node_pub._id, 'type': 'nodes'}
        assert urlparse(data['relationships']['target']['links']['related']['href']).path == f'/{API_BASE}nodes/{node_pub._id}/'
        assert data['relationships']['template']['data'] == {'id': cedar_template._id, 'type': 'cedar-metadata-templates'}
        assert urlparse(data['relationships']['template']['links']['related']['href']).path == f'/{API_PRIVATE_BASE}cedar_metadata_templates/{cedar_template._id}/'
        assert urlparse(data['links']['self']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node_pub._id}/'
        assert urlparse(data['links']['metadata_download']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node_pub._id}/metadata_download/'

    def test_record_detail_for_node_with_invalid_auth(self, app, node_pub, user_alt, cedar_template, cedar_record_for_node_pub, cedar_record_metadata_json):

        resp = app.get(f'/_/cedar_metadata_records/{cedar_record_for_node_pub._id}/', auth=user_alt.auth)
        assert resp.status_code == 200
        data = resp.json['data']

        assert data['id'] == cedar_record_for_node_pub._id
        assert data['type'] == 'cedar-metadata-records'
        assert data['attributes']['metadata'] == cedar_record_metadata_json
        assert data['attributes']['is_published'] is True
        assert data['relationships']['target']['data'] == {'id': node_pub._id, 'type': 'nodes'}
        assert urlparse(data['relationships']['target']['links']['related']['href']).path == f'/{API_BASE}nodes/{node_pub._id}/'
        assert data['relationships']['template']['data'] == {'id': cedar_template._id, 'type': 'cedar-metadata-templates'}
        assert urlparse(data['relationships']['template']['links']['related']['href']).path == f'/{API_PRIVATE_BASE}cedar_metadata_templates/{cedar_template._id}/'
        assert urlparse(data['links']['self']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node_pub._id}/'
        assert urlparse(data['links']['metadata_download']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node_pub._id}/metadata_download/'

    def test_record_detail_for_node_with_no_auth(self, app, node_pub, cedar_template, cedar_record_for_node_pub, cedar_record_metadata_json):

        resp = app.get(f'/_/cedar_metadata_records/{cedar_record_for_node_pub._id}/', auth=None)
        assert resp.status_code == 200
        data = resp.json['data']

        assert data['id'] == cedar_record_for_node_pub._id
        assert data['type'] == 'cedar-metadata-records'
        assert data['attributes']['metadata'] == cedar_record_metadata_json
        assert data['attributes']['is_published'] is True
        assert data['relationships']['target']['data'] == {'id': node_pub._id, 'type': 'nodes'}
        assert urlparse(data['relationships']['target']['links']['related']['href']).path == f'/{API_BASE}nodes/{node_pub._id}/'
        assert data['relationships']['template']['data'] == {'id': cedar_template._id, 'type': 'cedar-metadata-templates'}
        assert urlparse(data['relationships']['template']['links']['related']['href']).path == f'/{API_PRIVATE_BASE}cedar_metadata_templates/{cedar_template._id}/'
        assert urlparse(data['links']['self']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node_pub._id}/'
        assert urlparse(data['links']['metadata_download']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_record_for_node_pub._id}/metadata_download/'


@pytest.mark.django_db
class TestCedarMetadataRecordDetailPublicProjectDraftMetadata(TestCedarMetadataRecord):

    def test_record_detail_for_node_with_admin_auth(self, app, node_pub_alt, user, cedar_template, cedar_draft_record_for_node_pub_alt, cedar_record_metadata_json):

        admin = user
        resp = app.get(f'/_/cedar_metadata_records/{cedar_draft_record_for_node_pub_alt._id}/', auth=admin.auth)
        assert resp.status_code == 200
        data = resp.json['data']

        assert data['id'] == cedar_draft_record_for_node_pub_alt._id
        assert data['type'] == 'cedar-metadata-records'
        assert data['attributes']['metadata'] == cedar_record_metadata_json
        assert data['attributes']['is_published'] is False
        assert data['relationships']['target']['data'] == {'id': node_pub_alt._id, 'type': 'nodes'}
        assert urlparse(data['relationships']['target']['links']['related']['href']).path == f'/{API_BASE}nodes/{node_pub_alt._id}/'
        assert data['relationships']['template']['data'] == {'id': cedar_template._id, 'type': 'cedar-metadata-templates'}
        assert urlparse(data['relationships']['template']['links']['related']['href']).path == f'/{API_PRIVATE_BASE}cedar_metadata_templates/{cedar_template._id}/'
        assert urlparse(data['links']['self']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_draft_record_for_node_pub_alt._id}/'
        assert urlparse(data['links']['metadata_download']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_draft_record_for_node_pub_alt._id}/metadata_download/'

    def test_record_detail_for_node_with_write_auth(self, app, node_pub_alt, cedar_template, cedar_draft_record_for_node_pub_alt, cedar_record_metadata_json):

        write = AuthUserFactory()
        node_pub_alt.add_contributor(write, permissions=WRITE)
        node_pub_alt.save()
        resp = app.get(f'/_/cedar_metadata_records/{cedar_draft_record_for_node_pub_alt._id}/', auth=write.auth)
        assert resp.status_code == 200
        data = resp.json['data']

        assert data['id'] == cedar_draft_record_for_node_pub_alt._id
        assert data['type'] == 'cedar-metadata-records'
        assert data['attributes']['metadata'] == cedar_record_metadata_json
        assert data['attributes']['is_published'] is False
        assert data['relationships']['target']['data'] == {'id': node_pub_alt._id, 'type': 'nodes'}
        assert urlparse(data['relationships']['target']['links']['related']['href']).path == f'/{API_BASE}nodes/{node_pub_alt._id}/'
        assert data['relationships']['template']['data'] == {'id': cedar_template._id, 'type': 'cedar-metadata-templates'}
        assert urlparse(data['relationships']['template']['links']['related']['href']).path == f'/{API_PRIVATE_BASE}cedar_metadata_templates/{cedar_template._id}/'
        assert urlparse(data['links']['self']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_draft_record_for_node_pub_alt._id}/'
        assert urlparse(data['links']['metadata_download']).path == f'/{API_PRIVATE_BASE}cedar_metadata_records/{cedar_draft_record_for_node_pub_alt._id}/metadata_download/'

    # TODO: discuss and fix permission
    @pytest.mark.skip(reason='discuss and fix permission')
    def test_record_detail_for_node_with_read_auth(self, app, node_pub_alt, user, cedar_draft_record_for_node_pub_alt):

        read = AuthUserFactory()
        node_pub_alt.add_contributor(read, permissions=READ)
        node_pub_alt.save()

        resp = app.get(f'/_/cedar_metadata_records/{cedar_draft_record_for_node_pub_alt._id}/', auth=read.auth)
        assert resp.status_code == 401

    # TODO: discuss and fix permission
    @pytest.mark.skip(reason='discuss and fix permission')
    def test_record_detail_for_node_with_invalid_auth(self, app, user_alt, cedar_draft_record_for_node_pub_alt):

        resp = app.get(f'/_/cedar_metadata_records/{cedar_draft_record_for_node_pub_alt._id}/', auth=user_alt.auth)
        assert resp.status_code == 401

    # TODO: discuss and fix permission
    @pytest.mark.skip(reason='discuss and fix permission')
    def test_record_detail_for_node_with_no_auth(self, app, cedar_draft_record_for_node_pub_alt):

        resp = app.get(f'/_/cedar_metadata_records/{cedar_draft_record_for_node_pub_alt._id}/', auth=None)
        assert resp.status_code == 401

@pytest.mark.django_db
class TestCedarMetadataRecordDetailPrivateRegistrationPublishedMetadata(TestCedarMetadataRecord):
    # TODO: implement this
    pass


@pytest.mark.django_db
class TestCedarMetadataRecordDetailPrivateRegistrationDraftMetadata(TestCedarMetadataRecord):
    # TODO: implement this
    pass


@pytest.mark.django_db
class TestCedarMetadataRecordDetailPublicRegistrationPublishedMetadata(TestCedarMetadataRecord):
    # TODO: implement this
    pass


@pytest.mark.django_db
class TestCedarMetadataRecordDetailPublicRegistrationDraftMetadata(TestCedarMetadataRecord):
    pass


@pytest.mark.django_db
class TestCedarMetadataRecordDetailPrivateFilePublishedMetadata(TestCedarMetadataRecord):
    # TODO: implement this
    pass


@pytest.mark.django_db
class TestCedarMetadataRecordDetailPrivateFileDraftMetadata(TestCedarMetadataRecord):
    # TODO: implement this
    pass


@pytest.mark.django_db
class TestCedarMetadataRecordDetailPublicFilePublishedMetadata(TestCedarMetadataRecord):
    # TODO: implement this
    pass


@pytest.mark.django_db
class TestCedarMetadataRecordDetailPublicFileDraftMetadata(TestCedarMetadataRecord):
    # TODO: implement this
    pass
