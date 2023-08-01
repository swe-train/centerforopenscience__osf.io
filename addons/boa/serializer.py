from addons.base.serializer import StorageAddonSerializer
from addons.boa.settings import DEFAULT_HOSTS, USE_SSL
from website.util import web_url_for

from boa import Client as BoaClient

class BoaSerializer(StorageAddonSerializer):

    addon_short_name = 'boa'

    def serialized_folder(self, node_settings):
        return {
            'name': node_settings.fetch_folder_name(),
            'path': node_settings.folder_id
        }

    def credentials_are_valid(self, user_settings, client=None):
        node = self.node_settings
        external_account = node.external_account
        provider = self.node_settings.oauth_provider(external_account)

        try:
            oc = BoaClient(provider.host, verify_certs=USE_SSL)
            oc.login(provider.username, provider.password)
            oc.logout()
            return True
        except Exception:
            return False

    @property
    def addon_serialized_urls(self):
        node = self.node_settings.owner
        user_settings = self.node_settings.user_settings or self.user_settings

        result = {
            'auth': node.api_url_for('boa_add_user_account'),
            'accounts': node.api_url_for('boa_account_list'),
            'importAuth': node.api_url_for('boa_import_auth'),
            'deauthorize': node.api_url_for('boa_deauthorize_node'),
            'folders': node.api_url_for('boa_folder_list'),
            'files': node.web_url_for('collect_file_trees'),
            'config': node.api_url_for('boa_set_config'),
        }
        if user_settings:
            result['owner'] = web_url_for('profile_view_id',
                uid=user_settings.owner._id)
        return result

    @property
    def serialized_node_settings(self):
        result = super(BoaSerializer, self).serialized_node_settings
        result['hosts'] = DEFAULT_HOSTS
        return result

    @property
    def serialized_user_settings(self):
        result = super(BoaSerializer, self).serialized_user_settings
        result['hosts'] = DEFAULT_HOSTS
        return result

    def serialize_settings(self, node_settings, current_user, client=None):
        ret = super(BoaSerializer, self).serialize_settings(node_settings, current_user, client)
        ret['hosts'] = DEFAULT_HOSTS
        return ret
