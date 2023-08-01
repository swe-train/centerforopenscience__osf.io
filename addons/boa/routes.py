# -*- coding: utf-8 -*-
from framework.routing import Rule, json_renderer

from addons.boa import views

# JSON endpoints
api_routes = {
    'rules': [
        Rule(
            [
                '/project/<pid>/boa/user-auth/',
                '/project/<pid>/node/<nid>/boa/user-auth/',
            ],
            'delete',
            views.boa_deauthorize_node,
            json_renderer,
        ),
        Rule(
            '/settings/boa/accounts/',
            'get',
            views.boa_account_list,
            json_renderer,
        ),
        Rule(
            ['/project/<pid>/boa/settings/',
             '/project/<pid>/node/<nid>/boa/settings/'],
            'put',
            views.boa_set_config,
            json_renderer
        ),
        Rule(
            ['/project/<pid>/boa/settings/',
             '/project/<pid>/node/<nid>/boa/settings/'],
            'get',
            views.boa_get_config,
            json_renderer
        ),
        Rule(
            ['/settings/boa/accounts/'],
            'post',
            views.boa_add_user_account,
            json_renderer
        ),
        Rule(
            [
                '/project/<pid>/boa/user-auth/',
                '/project/<pid>/node/<nid>/boa/user-auth/',
            ],
            'put',
            views.boa_import_auth,
            json_renderer
        ),
        Rule(
            ['/project/<pid>/boa/folders/',
             '/project/<pid>/node/<nid>/boa/folders/'],
            'get',
            views.boa_folder_list,
            json_renderer
        ),
    ],
    'prefix': '/api/v1'
}
