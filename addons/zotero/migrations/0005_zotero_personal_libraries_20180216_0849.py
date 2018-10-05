# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-16 14:49
from __future__ import unicode_literals

from bulk_update.helper import bulk_update
from django.db import migrations

def reverse_func(state, schema):
    modify_node_settings(state, None)
    modify_user_settings(state, False, None)

def modify_node_settings(state, library_name):
    """
    Updates the library_id for all ZoteroNodeSettings
    """
    ZoteroNodeSettings = state.get_model('addons_zotero', 'NodeSettings')
    ZoteroNodeSettings.objects.all().update(library_id=library_name)

def modify_user_settings(state, add, library_name):
    """
    For all zotero user settings,
    :params state: app_state
    :params library_name: library name to add or remove from user settings oauth metadata
    :params add: True for adding library, False for removing it.
    """
    ZoteroUserSettings = state.get_model('addons_zotero', 'UserSettings')
    user_settings_pending_save = []

    for user_setting in ZoteroUserSettings.objects.all():
        for node, ext_accounts in user_setting.oauth_grants.items():
            for ext_account in list(ext_accounts.keys()):
                if add:
                    user_setting.oauth_grants[node][ext_account]['library'] = library_name
                else:
                    user_setting.oauth_grants[node][ext_account].pop('library', None)
        user_settings_pending_save.append(user_setting)
    bulk_update(user_settings_pending_save)

def migrate_zotero_libraries(state, schema):
    """
    1) For all zotero NodeSettings, mark library_id as 'personal', which has been the only
    option prior to zotero group libraries being added
    2) For all zotero usersettings, add 'personal' library value to the nodes that have been given permission
    to use zotero external accounts.
    """
    modify_node_settings(state, 'personal')
    modify_user_settings(state, True, 'personal')


class Migration(migrations.Migration):

    dependencies = [
        ('addons_zotero', '0004_merge_20180112_0836'),
    ]

    operations = [
        migrations.RunPython(migrate_zotero_libraries, reverse_func)
    ]
