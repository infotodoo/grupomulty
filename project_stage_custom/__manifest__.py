# -*- coding: utf-8 -*-
{
    "name" : "Ajustes Proyectos",

    "author" : "Coondev",

    "version":"14.0.1",

    "depends" : [

        "base",
        "project",
        "account",
    ],

    "data": [

        'security/ir.model.access.csv',
        'security/groups.xml',
        'views/project_project_stage.xml',
        'views/project_project.xml',
        'views/project_task.xml',

    ],
    "images": ["static/description/icon.png",],

    "application": True,

    "auto_install":False,

    "installable" : True,

    "currency": "COP"
}
