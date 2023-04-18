odoo.define('l10n_co_pos_res_partner', function (require) {
"use strict";

    var PaymentScreen = require('point_of_sale.PaymentScreen');
    var models = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

    const PaymentScreen2 = (PaymentScreen) => {
        class PaymentScreen2 extends PaymentScreen {
            async validateOrder(isForceValidate) {
                var self = this;
                if(this.env.pos.config.cash_rounding) {
                    if(!this.env.pos.get_order().check_paymentlines_rounding()) {
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Rounding error in payment lines'),
                            body: this.env._t("The amount of your payment lines must be rounded to validate the transaction."),
                        });
                        return;
                    }
                }
                if (await this._isOrderValid(isForceValidate)) {
                    // remove pending payments before finalizing the validation
                    for (let line of this.paymentLines) {
                        if (!line.is_done()) this.currentOrder.remove_paymentline(line);
                    }
                if (this.env.pos.config.customized_sequence_id) {
                    self.rpc({
                          model: 'pos.order',
                          method: 'pos_customized_sequence_data',
                         args: [self.env.pos.config.customized_sequence_id[0]],
                      }).then(function (data) {
                            var currentOrder = self.env.pos.get('selectedOrder');
                            currentOrder.set_new_name(data.secuencia);
                            currentOrder.set_secuencia_dian(data);
                        self._finalizeValidation();
                      }, function (type, err) { self._finalizeValidation()});

                } else {
                    await this._finalizeValidation();
                }

                }
            }

        }
        return PaymentScreen2;
    };
    Registries.Component.extend(PaymentScreen, PaymentScreen2);

    var OrderSuper = models.Order;
    models.Order = models.Order.extend({
        set_new_name: function(name) {
            this.new_name = name;
        },
        export_as_JSON: function(){
            var data = OrderSuper.prototype.export_as_JSON.apply(this, arguments);
            data.new_name = this.new_name || this.name;
            return data;
        }
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        set_secuencia_dian: function(name) {
            console.log('secuencia')
            this.secuencia = name.secuencia;
            this.number_to = name.number_to;
            this.number_from = name.number_from;
            this.date_to = name.date_to;
            this.date_from = name.date_from;
            this.resolution_number = name.resolution_number;
        },
        export_for_printing: function () {
                var result = _super_order.export_for_printing.apply(this, arguments);
                result.secuencia = this.secuencia
                result.number_to = this.number_to
                result.number_from = this.number_from
                result.date_from = this.date_from
                result.date_to = this.date_to
                result.resolution_number = this.resolution_number
                return result;
        },
    });




});