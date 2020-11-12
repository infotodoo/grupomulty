// bi_pos_stock js
odoo.define('bi_pos_stock.pos', function(require) {
	"use strict";

	var models = require('point_of_sale.models');
	var screens = require('point_of_sale.screens');
	var core = require('web.core');
	var gui = require('point_of_sale.gui');
	var popups = require('point_of_sale.popups');
	//var Model = require('web.DataModel');
	var field_utils = require('web.field_utils');
	var rpc = require('web.rpc');
	var session = require('web.session');
	var time = require('web.time');
	var utils = require('web.utils');
	var chrome = require('point_of_sale.chrome');

	var QWeb = core.qweb;
	var _t = core._t;


	chrome.OrderSelectorWidget.include({
		events: {
			"click .pos-stock-sync": "do_pos_lock_screen",
		},

		init: function(parent, options) {
			this._super(parent, options);
			this.do_pos_lock_screen();
		},

		do_pos_lock_screen: function (e) {
			var self = this;
			this.pos.set('is_sync',true);
			this.product_list_widget = new screens.ProductListWidget(this,{
				click_product_action: function(product){ self.click_product(product); },
				product_list: this.pos.db.get_product_by_category(0)
			});
			this.product_list_widget.renderElement();
		},
	});

	models.load_models({
		model: 'stock.location',
		fields: [],
		//ids:    function(self){ return [self.config.stock_location_id[0]]; },
		loaded: function(self, locations){
			var i;
			self.locations = locations[0];
			if (self.config.show_stock_location == 'specific')
			{
				// associate the Locations with their quants.
				var ilen = locations.length;
				for(i = 0; i < ilen; i++){
					if(locations[i].id === self.config.stock_location_id[0]){
						self.locations =  locations[i];
					}
				}
			}
		},
	});
	


	var _super_posmodel = models.PosModel.prototype;
	models.PosModel = models.PosModel.extend({
		
		initialize: function (session, attributes) {
			var product_model = _.find(this.models, function(model){ return model.model === 'product.product'; });
			product_model.fields.push('virtual_available','available_quantity','qty_available','incoming_qty','outgoing_qty','type');
			return _super_posmodel.initialize.call(this, session, attributes);
		},
		
		//########################################################################################
		load_product_qty:function(product){
			var product_qty_final = $("[data-product-id='"+product.id+"'] #stockqty");
			product_qty_final.html(product['bi_on_hand'])

			var product_qty_avail = $("[data-product-id='"+product.id+"'] #availqty");
			product_qty_avail.html(product['bi_available']);
			
		},
		//#########################################################################################
		
		
		push_order: function(order, opts){
			var self = this;
			var pushed = _super_posmodel.push_order.call(this, order, opts);
			var client = order && order.get_client();
			
			if (order){
				//##############################
				if (this.config.pos_display_stock === true && this.config.pos_stock_type == 'onhand' || this.config.pos_stock_type == 'available'){
				order.orderlines.each(function(line){
					var product = line.get_product();
					product['bi_on_hand'] -= line.get_quantity();
					product['bi_available'] -= line.get_quantity();
					
					product.qty_available -= line.get_quantity();
					self.load_product_qty(product);
				})
				}
				//##############################
			}
			return pushed;
		}
	});

	screens.ProductListWidget.include({
		init: function(parent, options) {
			var self = this;
			this._super(parent,options);
			this.model = options.model;
			this.productwidgets = [];
			this.weight = options.weight || 0;
			this.show_scale = options.show_scale || false;
			this.next_screen = options.next_screen || false;

			this.click_product_handler = function(){
				var product = self.pos.db.get_product_by_id(this.dataset.productId);
				var allow_order = self.pos.config.pos_allow_order;
				var deny_order= self.pos.config.pos_deny_order;

				if(self.pos.config.show_stock_location == 'specific')
				{
					if (product.type == 'product')
					{
						var partner_id = self.pos.get_client();
						var location = self.pos.locations;
						rpc.query({
								model: 'stock.quant',
								method: 'get_single_product',
								args: [partner_id ? partner_id.id : 0,product.id, location],
							
							},{async : false}).then(function(output) {
								if (allow_order == false)
								{
									if (output[0][1] <= deny_order)
									{
										self.gui.show_popup('error',{
											'title': _t('Deny Order'),
											'body': _t("Deny Order" + "(" + product.display_name + ")" + " is Out of Stock.")
										});
									}
									else if (output[0][1] <= 0)
									{
										self.gui.show_popup('error',{
											'title': _t('Error: Out of Stock'),
											'body': _t("(" + product.display_name + ")" + " is Out of Stock."),
										});
									}
									else{
										options.click_product_action(product);
									}
								}
								else if(allow_order == true)
								{
									if (output[0][1] <= deny_order)
									{
										self.gui.show_popup('error',{
											'title': _t('Deny Order'),
											'body': _t("Deny Order" + "(" + product.display_name + ")" + " is Out of Stock.")
										});
									}
									else{
										options.click_product_action(product);
									}
								}
								else{
										options.click_product_action(product);		
								}
						});
					}
					else{
							options.click_product_action(product);
						}
				}
				else{
					if (product.type == 'product' && allow_order == false)
					{
						// Deny POS Order When Product is Out of Stock
						if (product.qty_available <= deny_order && allow_order == false)
						{
							self.gui.show_popup('error',{
								'title': _t('Deny Order'),
								'body': _t("Deny Order" + "(" + product.display_name + ")" + " is Out of Stock.")
							});
						}
						// Allow POS Order When Product is Out of Stock
						else if (product.qty_available <= 0 && allow_order == false)
						{
							self.gui.show_popup('error',{
								'title': _t('Error: Out of Stock'),
								'body': _t("(" + product.display_name + ")" + " is Out of Stock."),
							});
						} else {
							options.click_product_action(product);
						}
					}
					else if(product.type == 'product' && allow_order == true && product.qty_available <= deny_order){
					self.gui.show_popup('error',{
							'title': _t('Error: Out of Stock'),
							'body': _t("(" + product.display_name + ")" + " is Out of Stock."),
						});
					}	
					else if(product.type == 'product' && allow_order == true && product.qty_available >= deny_order){
						options.click_product_action(product);
					} 
					else {
						options.click_product_action(product);
					}
				}
				
			};

		},

		renderElement: function() {
			var self = this;
			var el_str  = QWeb.render(this.template, {widget: this});
			var el_node = document.createElement('div');
				el_node.innerHTML = el_str;
				el_node = el_node.childNodes[1];
			if(this.el && this.el.parentNode){
				this.el.parentNode.replaceChild(el_node,this.el);
			}
			this.el = el_node;

			var list_container = el_node.querySelector('.product-list');


			if (self.pos.config.show_stock_location == 'specific')
			{
				var x_sync = this.pos.get("is_sync")
				var location = self.pos.locations;
				if(x_sync == true){
					if (self.pos.config.pos_stock_type == 'onhand')
					{
						rpc.query({
								model: 'stock.quant',
								method: 'get_stock_location_qty',
								args: [1, location],
							
							},{async : false}).then(function(output) {
								self.pos.loc_onhand = output[0];
								for(var i = 0, len = self.product_list.length; i < len; i++){
									self.product_list[i]['bi_on_hand'] = self.product_list[i].qty_available;
									self.product_list[i]['bi_available'] = self.product_list[i].virtual_available;

									for(let key in self.pos.loc_onhand)
									{
										if(self.product_list[i].id == key)
										{
											self.product_list[i]['bi_on_hand'] = self.pos.loc_onhand[key];

											var product_qty_final = $("[data-product-id='"+self.product_list[i].id+"'] #stockqty");
											product_qty_final.html(self.pos.loc_onhand[key])
											var product_qty_avail = $("[data-product-id='"+self.product_list[i].id+"'] #availqty");
											product_qty_avail.html(self.product_list[i].virtual_available);
										}
									}
									var product_node = self.render_product(self.product_list[i]);
									product_node.addEventListener('click',self.click_product_handler);
									product_node.addEventListener('keypress',self.keypress_product_handler);
									list_container.appendChild(product_node);
								}
								self.pos.set("is_sync",false);
						});
					}

					if (self.pos.config.pos_stock_type == 'available')
					{
						rpc.query({
								model: 'product.product',
								method: 'get_stock_location_avail_qty',
								args: [1, location],
							
						},{async : false}).then(function(output) {
								
							self.pos.loc_available = output[0];
							for(var i = 0, len = self.product_list.length; i < len; i++){
								self.product_list[i]['bi_on_hand'] = self.product_list[i].qty_available;
								self.product_list[i]['bi_available'] = self.product_list[i].virtual_available;

								for(let key in self.pos.loc_available)
								{
									if(self.product_list[i].id == key)
									{
										self.product_list[i]['bi_available'] = self.pos.loc_available[key];
										var product_qty_final = $("[data-product-id='"+self.product_list[i].id+"'] #stockqty");
										product_qty_final.html(self.product_list[i].qty_available)
										var product_qty_avail = $("[data-product-id='"+self.product_list[i].id+"'] #availqty");
										product_qty_avail.html(self.pos.loc_available[key]);
									}
								}
								var product_node = self.render_product(self.product_list[i]);
								product_node.addEventListener('click',self.click_product_handler);
								product_node.addEventListener('keypress',self.keypress_product_handler);
								list_container.appendChild(product_node);
							}
							self.pos.set("is_sync",false);
						});
					}
				}else{
					for(var i = 0, len = this.product_list.length; i < len; i++){
						var product_node = this.render_product(this.product_list[i]);
						product_node.addEventListener('click',this.click_product_handler);
						product_node.addEventListener('keypress',this.keypress_product_handler);
						list_container.appendChild(product_node);
					}
				}
			}
			else{
				for(var i = 0, len = this.product_list.length; i < len; i++){
					this.product_list[i]['bi_on_hand'] = this.product_list[i].qty_available;
					this.product_list[i]['bi_available'] = this.product_list[i].virtual_available;
					var product_node = this.render_product(this.product_list[i]);
					product_node.addEventListener('click',this.click_product_handler);
					product_node.addEventListener('keypress',this.keypress_product_handler);
					list_container.appendChild(product_node);
				}
			}
		},
		

	});
	// End GiftPopupWidget start

	// Popup start

	var ValidQtyPopupWidget = popups.extend({
		template: 'ValidQtyPopupWidget',
		init: function(parent, args) {
			this._super(parent, args);
			this.options = {};
		},
		//
		show: function(options) {
			var self = this;
			this._super(options);
		},
		//
		renderElement: function() {
			var self = this;
			this._super();
			this.$('#back_to_products').click(function() {
				self.gui.show_screen('products');
			});            	
		},

	});
	gui.define_popup({
		name: 'valid_qty_popup_widget',
		widget: ValidQtyPopupWidget
	});

	// End Popup start
	
	// ActionpadWidget start
	screens.ActionpadWidget.include({
		renderElement: function() {
			var self = this;
			this._super();
			this.$('.pay').click(function(){
				var order = self.pos.get_order();

				var has_valid_product_lot = _.every(order.orderlines.models, function(line){
					return line.has_valid_product_lot();
				});
				if(!has_valid_product_lot){
					self.gui.show_popup('error',{
						'title': _t('Empty Serial/Lot Number'),
						'body':  _t('One or more product(s) required serial/lot number.'),
						confirm: function(){
							self.gui.show_screen('payment');
						},
					});
				}else{
					self.gui.show_screen('payment');
				}

				if (self.pos.config.show_stock_location == 'specific')
				{
					var partner_id = self.pos.get_client();
					var location = self.pos.locations;
					var lines = order.get_orderlines();
					var prods = [];

					for (var i = 0; i < lines.length; i++) {
						if (lines[i].product.type == 'product'){
							prods.push(lines[i].product.id)
						}
					}
					rpc.query({
							model: 'stock.quant',
							method: 'get_products_stock_location_qty',
							args: [partner_id ? partner_id.id : 0, location,prods],
						
						},{async : false}).then(function(output) {
							var flag = 0;
							for (var i = 0; i < lines.length; i++) {
								for (var j = 0; j < output.length; j++) {
									var values = $.map(output[0], function(value, key) { 
										var keys = $.map(output[0], function(value, key) {
											if (lines[i].product.type == 'product' && self.pos.config.pos_allow_order == false && lines[i].product['id'] == key && lines[i].quantity > value){
												flag = flag + 1;
											}
										});
																	
									});
								}
							}
							if(flag > 0){
								self.gui.show_popup('valid_qty_popup_widget', {});
							}
							else{
								self.gui.show_screen('payment');
							}
											   
					});
				
				} else {
				
				
					// When Ordered Qty it More than Available Qty, Raise Error popup

					var lines = order.get_orderlines();

					for (var i = 0; i < lines.length; i++) {
						
						if (lines[i].product.type == 'product' && self.pos.config.pos_allow_order == false && lines[i].quantity > lines[i].product['qty_available']){
							//if (lines[i].quantity > lines[i].product['qty_available']) {
								self.gui.show_popup('valid_qty_popup_widget', {});
								break;
							//}
							
						}
						else { 
							 self.gui.show_screen('payment');   
						}
					
					}
					
				}	
								
			});
			this.$('.set-customer').click(function(){
				self.gui.show_screen('clientlist');
			});
			
		},
	});  
	// End ActionpadWidget start
		

});
