from website.app import setup_django
setup_django()

import logging
import sys
from django.db import transaction
from osf.models import Node, ExternalAccount, OSFUser
from scripts import utils

logger = logging.getLogger(__name__)


# copied from BaseOAuthUserSettings.remove_oauth_access
def deauthorize_nodes(user_settings, external_account):
    for node in user_settings.get_nodes_with_oauth_grants(external_account):
        try:
            node.get_addon(external_account.provider, deleted=True).deauthorize(auth=None,
                                                                                add_log=False)
        except AttributeError:
            # No associated addon settings despite oauth grant
            pass

    for key in user_settings.oauth_grants:
        user_settings.oauth_grants[key].pop(external_account._id, None)
    user_settings.save()

def main(guids, dry=False):
    with transaction.atomic():
        user_external_accounts = {}
        for guid in set(guids):
            logger.info("Affected node: {}".format(guid))
            node = Node.load(guid)
            node_settings = node.get_addon('figshare')
            external_account = node_settings.external_account
            user_settings = node_settings.user_settings
            if not user_settings:
                logger.warn("Figshare has been deauthorized from node {}".format(guid))
                logger.warn("Getting user settings from user who deauthorized...")
                log = node.logs.order_by('-date').filter(action='figshare_node_deauthorized').first()
                assert log is not None
                user = log.user
                user_settings = user.get_addon('figshare')
                try:
                    external_account = user_settings.external_accounts.get()
                except ExternalAccount.DoesNotExist:
                    logger.warn('No external account for {}. It has already been revoked.'.format(user.username))
                    continue
            else:
                user = user_settings.owner

            user_external_accounts[user._id] = external_account


        for user_id, external_account in user_external_accounts.items():
            user = OSFUser.load(user_id)
            user_settings = user.get_addon('figshare')

            logger.info("Affected user: {}".format(user.username))
            # Revoke user's access to the external account
            logger.debug("Deauthorizing nodes associated with {}".format(user_settings))
            deauthorize_nodes(user_settings, external_account)
            logger.debug("Removing {} from user".format(user_settings))
            user.external_accounts.remove(external_account)
            user.save()

            logger.debug("Clearing data from ExternalAccount")
            # Clear out creds from external account
            external_account.oauth_key = None
            external_account.oauth_secret = None
            external_account.refresh_token = None
            external_account.display_name = None
            external_account.profile_url = None
            external_account.save()
        if dry:
            raise Exception('Dry Run -- Transaction aborted.')


if __name__ == '__main__':
    if '--dry' in sys.argv:
        guids = [each for each in sys.argv[1:] if each != '--dry']
    else:
        guids = sys.argv[1:]
    dry = '--dry' in sys.argv
    if not dry:
        utils.add_file_logger(logger, __file__)
    if not guids:
        print('ERROR: Must pass guids as positional arguments')
        sys.exit(1)
    main(guids, dry=dry)
