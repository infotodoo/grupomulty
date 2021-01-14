# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class Posinherit(models.Model):
	_inherit='pos.order'

	subtotal=fields.Float("subtotal",compute="_compue_subtotal")

	def _compue_subtotal(self):
		for rec in self:
			rec.subtotal=rec.amount_total-rec.amount_tax

	def action_mail_possend(self):
		self.ensure_one()
		ir_model_data = self.env['ir.model.data']
		try:
			template_id = ir_model_data.get_object_reference('pos_backend_receipt_report_app', 'email_template_view')[1]
		except ValueError:
			template_id = False
		try:
			compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
		except ValueError:
			compose_form_id = False
		lang = self.env.context.get('lang')
		template = template_id and self.env['mail.template'].browse(template_id)
		if template and template.lang:
			lang = template._render_template(template.lang, 'pos.order', self.ids[0])
		ctx = {
			'default_model': 'pos.order',
			'default_res_id': self.ids[0],
			'default_use_template': bool(template_id),
			'default_template_id': template_id,
			'default_composition_mode': 'comment',
			'mark_so_as_sent': True,
            'proforma': self.env.context.get('proforma', False),
			'force_email': True
		}
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'mail.compose.message',
			'views': [(compose_form_id, 'form')],
			'view_id': compose_form_id,
			'target': 'new',
			'context': ctx,
		}

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    discount_val = fields.Float(compute='_compute_discount_val')#, store=True)

    @api.depends('qty','price_unit', 'price_subtotal_incl')
    def _compute_discount_val(self):
        for rec in self:
            rec.discount_val = round(rec.qty * rec.price_unit * rec.discount / 100, 2)