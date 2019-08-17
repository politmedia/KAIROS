from datetime import datetime
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from menus.base import Menu
from menus.base import Modifier
from menus.base import NavigationNode
from menus.menu_pool import menu_pool


class CoreMenu(Menu):

    def get_nodes(self, request):
        nodes = []
        compare = NavigationNode(_('compare'), reverse(
            'compare'), 1, attr={'priority': 1002})
        candidates = NavigationNode(_('candidates'), reverse(
            'candidates'), 2, attr={'priority': 1001})

        if not settings.CANDIDATE_LIST_SHOW_AFTER or settings.CANDIDATE_LIST_SHOW_AFTER <= datetime.now():
            nodes.append(candidates)
            nodes.append(compare)
        return nodes


class CoreModifier(Modifier):

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        return sorted(
            nodes,
            key=lambda n: n.attr.get('priority', 1000)
        )


menu_pool.register_menu(CoreMenu)
menu_pool.register_modifier(CoreModifier)
