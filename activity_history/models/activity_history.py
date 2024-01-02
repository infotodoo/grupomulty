# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ActivityHistory(models.Model):
    _name = 'activity.history'
    _inherit = 'mail.activity'

    activity_id = fields.Many2one('mail.activity', 'Actividad Programada')


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def _create_activity_history(self, activity):
        self.env['mail.activity.history'].create({
            'activity_id': activity.id,
            'create_date': activity.create_date,
            'res_model': activity.res_model,
            'create_uid': activity.create_uid,
            'activity_type_id': activity.activity_type_id,
            'note': activity.note,
            'date_deadline': activity.date_deadline,
            'state': activity.state,
            'summary': activity.summary,
        })

    @api.model_create_multi
    def create(self, vals_list):
        activities = super(MailActivity, self).create(vals_list)
        for activity in activities:
            self._create_activity_history(activity)
        return activities
