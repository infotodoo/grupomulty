odoo.define('l10n_co_pos_res_partner.partner', function(require) {
	"use strict";

	const { Component } = owl;
	const Registries = require('point_of_sale.Registries');
	const PaymentScreen = require('point_of_sale.PaymentScreen');

	const CustomPaymentScreen = (PaymentScreen) =>
		class extends PaymentScreen {
			constructor() {
				super(...arguments);
				//this.auto_invoice();
			}

			auto_invoice(){
				let self =this;
				let config = self.env.pos.config;
				let order = self.env.pos.get_order();
				const client = order.get_client();
                if(client){
                    if(client.partner_state == 'third_accountant'){
                        order.set_to_invoice(true);
                        self.render();
                    }
				}


			}
	};

	Registries.Component.extend(PaymentScreen, CustomPaymentScreen);
	return PaymentScreen;

});