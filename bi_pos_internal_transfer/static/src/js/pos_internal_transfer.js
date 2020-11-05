odoo.define('pos_custom_discount.pos', function(require) {
	"use strict";

	var models = require('point_of_sale.models');
	var screens = require('point_of_sale.screens');
	var core = require('web.core');
	var gui = require('point_of_sale.gui');
	var popups = require('point_of_sale.popups');
	var rpc = require('web.rpc');

	var _t = core._t;

	models.load_models({
		model: 'stock.warehouse',
		fields: ['id','name','display_name','company_id'],
		domain: function(self){ return [['company_id','=',self.company && self.company.id]]; }, 
		loaded: function(self, stockwarehouse){
			self.stockwarehouse = stockwarehouse;
		},
	});

	models.load_models({
		model: 'stock.picking.type',
		fields: ['id','name','display_name'],
		domain: function(self){ return [['code', '=', 'internal'],['warehouse_id','=',self.stockwarehouse[0].id]]; }, 
		loaded: function(self, stockpickingtype){
			self.stockpickingtype = stockpickingtype;
		},
	});

	

	models.load_models({
		model: 'stock.location',
		fields: ['id','name','display_name'],
		domain: function(self){ return [['usage', '=', 'internal'],['company_id','=',self.company && self.company.id]]; },
		loaded: function(self, stocklocations){
			self.stocklocations = stocklocations;
		},
	});

	models.load_models({
		model: 'stock.picking',
		fields: ['id','name','state'],
		domain: null, 
		loaded: function(self, stockpicking){
			self.stockpicking = stockpicking;
		},
	});


	
	// Start PosNoteWidget
	
	var PosTransferWidget = screens.ActionButtonWidget.extend({
		template: 'PosTransferWidget',

		init: function(parent, args) {
			this._super(parent, args);
			this.options = {};
		},

		renderElement: function(){
			var self = this;
			this._super();
		}, 

		button_click: function() {
			var self = this;
			var order = self.pos.get('selectedOrder');
			var orderlines = order.orderlines;
			this.gui.show_popup('pos_Internal_stock_transfer_popup_widget', {});

		},
		
	});

	screens.define_action_button({
		'name': 'Pos Transfer Widget',
		'widget': PosTransferWidget,
		'condition': function() {
			return true;
		},
	});


	var PosInternalStockPopupWidget = popups.extend({
		template: 'PosInternalStockPopupWidget',
		init: function(parent, args) {
			this._super(parent, args);
			this.options = {};
		},
		
		renderElement: function() {
			var self = this;
			this._super();
			var order = this.pos.get_order();
			var orderlines = order.get_orderlines();

			this.$('#apply_transfer').click(function() {
				var picking_type = $('.drop-type').val();
				var src = $('.drop-src').val();
				var dest = $('.drop-dest').val();
				var state = $('.drop-state').val();
				if (self.pos.get_client()){
					var client = self.pos.get_client().id;
				}
				else{
					var client = false;
				}
				if(!picking_type || !src || !dest || !state){
					alert("Please select all options")
				}
				else if(parseInt(src) == parseInt(dest)){
					alert("You can not choose  same location as source location and destination location")
				}
				else{
					if(orderlines.length!=0){
						var product_ids = []
						for(var i=0;i<orderlines.length;i++){
							var prod_exist = $.grep(product_ids, function(v) {
								return v.product_id === orderlines[i].product.id;
							});
							if(prod_exist.length!=0){
								prod_exist[0]['quantity'] += orderlines[i].quantity
							}
							else{
								product_ids.push({
									'product_id': orderlines[i].product.id,
									'quantity': orderlines[i].quantity
								});
							}
						}
					
						rpc.query({
						model: 'pos.session',
						method: 'checking_product',
						args: [1,product_ids],
						}).then(function(output) {
							if(output[1].length!=0){
								var product;
								var name_product= '';
								for (var i = 0; i<output[1].length; i++)
								{
									product = self.pos.db.get_product_by_id(output[1][i])
									name_product += product.display_name+','
								}
								alert(name_product+"Product are serviceable so picking not generate for this products.")
							}
							if(output[0].length!=0){
									rpc.query({
										model: 'pos.session',
										method: 'generate_internal_picking',
										args: [1,client,picking_type,src,dest,state,product_ids],
									}).then(function(output) {
										if(output){
											alert("Your picking generated , Picking number is : "+output)
											product_ids = []
											self.pos.delete_current_order();
										}
									});
							}
						});
					}else{
						alert("Please Select Product first.")
					}
				}
			});
		}
	});
	gui.define_popup({
		name: 'pos_Internal_stock_transfer_popup_widget',
		widget: PosInternalStockPopupWidget
	});

	// End Popup start
	
});
