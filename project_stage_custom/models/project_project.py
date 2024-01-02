# -- coding: utf-8 --

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
import json
import os
import sys

class ProjectProject(models.Model):
    _inherit = 'project.project'

    def _default_stage_id(self):
        return self.env['project.project.stage'].search([], limit=1)
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return self.env['project.project.stage'].search([], order=order)
    
    stage_id = fields.Many2one('project.project.stage', string='Stage', ondelete='restrict', groups="project_stage_custom.group_project_stages", tracking=True, index=True, copy=False, default=_default_stage_id, group_expand='_read_group_stage_ids')