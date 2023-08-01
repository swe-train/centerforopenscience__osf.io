import mock
import pytest

from tests.base import OsfTestCase
from addons.base.tests.serializers import StorageAddonSerializerTestSuiteMixin
from addons.boa.tests.factories import BoaAccountFactory
from addons.boa.serializer import BoaSerializer

pytestmark = pytest.mark.django_db

class TestBoaSerializer(StorageAddonSerializerTestSuiteMixin, OsfTestCase):
    addon_short_name = 'boa'
    Serializer = BoaSerializer
    ExternalAccountFactory = BoaAccountFactory
    client = None

    def set_provider_id(self, pid):
        self.node_settings.folder_id = pid

    def setUp(self):
        self.mock_credentials = mock.patch('addons.boa.serializer.BoaSerializer.credentials_are_valid')
        self.mock_credentials.return_value = True
        self.mock_credentials.start()
        super(TestBoaSerializer, self).setUp()

    def tearDown(self):
        self.mock_credentials.stop()
        super(TestBoaSerializer, self).tearDown()
