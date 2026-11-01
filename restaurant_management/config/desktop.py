# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _


def get_data():
    data = [
        {
            "module_name": "Restaurant Management",
            "category": "Modules",
            "label": _("Restaurant Management"),
            "color": "#3498db",
            "icon": "octicon octicon-repo",
            "type": "module",
            "description": "Restaurant Management."
        },
    ]

    return data