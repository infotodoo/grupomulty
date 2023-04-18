odoo.define('l10n_co_pos_res_partner.main', function(require) {
"use strict";

var ajax = require('web.ajax');
var BarcodeParser = require('barcodes.BarcodeParser');
var BarcodeReader = require('point_of_sale.BarcodeReader');
var PosDB = require('point_of_sale.DB');
var devices = require('point_of_sale.devices');
var concurrency = require('web.concurrency');
var config = require('web.config');
var core = require('web.core');
var field_utils = require('web.field_utils');
var rpc = require('web.rpc');
var session = require('web.session');
var time = require('web.time');
var utils = require('web.utils');
var exports = {};





var module = require('point_of_sale.models');
//var Model = require('web.DataModel');
var gui = require('point_of_sale.Gui');
//var screens = require('point_of_sale.screens');
var screens = require('point_of_sale.ProductScreen');
var _t = core._t;

var models = module.PosModel.prototype.models;
module.load_fields("res.partner", ['firstname','othernames','lastname','lastname2','name','is_company','person_type','identification_document','zip_id','property_account_position_id','document_type_id','partner_state']);
var _super_order = module.Order.prototype;
    module.Order = module.Order.extend({
        initialize: function() {
            _super_order.initialize.apply(this, arguments);
            if (this.pos.config.default_partner_id) {
            	this.set_client(this.pos.db.get_partner_by_id(this.pos.config.default_partner_id[0]));
            }
        },

    });

var partner_fields = ['firstname',
                      'othernames',
                      'lastname',
                      'lastname2',
                      'is_company',
                      'person_type',
                      'document_type_id',
                      'identification_document',
                      'city_id',
                      'zip_id',
                      'property_account_position_id',
                     ];
exports.PosModel = Backbone.Model.extend({

    models: [
    {
        model:  'res.city.zip',
        fields: ['name desc', 'dian_code','city_id'],
        loaded: function(self,ciudades){
            self.ciudades = ciudades;
        },
    },


    ],
    load_server_data: function(){
        var self = this;
        var progress = 0;
        var progress_step = 1.0 / self.models.length;
        var tmp = {}; // this is used to share a temporary state between models loaders

        var loaded = new Promise(function (resolve, reject) {
            function load_model(index) {
                if (index >= self.models.length) {
                    resolve();
                } else {
                    var model = self.models[index];
                    self.chrome.loading_message(_t('Loading')+' '+(model.label || model.model || ''), progress);

                    var cond = typeof model.condition === 'function'  ? model.condition(self,tmp) : true;
                    if (!cond) {
                        load_model(index+1);
                        return;
                    }

                    var fields =  typeof model.fields === 'function'  ? model.fields(self,tmp)  : model.fields;
                    var domain =  typeof model.domain === 'function'  ? model.domain(self,tmp)  : model.domain;
                    var context = typeof model.context === 'function' ? model.context(self,tmp) : model.context || {};
                    var ids     = typeof model.ids === 'function'     ? model.ids(self,tmp) : model.ids;
                    var order   = typeof model.order === 'function'   ? model.order(self,tmp):    model.order;
                    progress += progress_step;

                    if( model.model ){
                        var params = {
                            model: model.model,
                            context: _.extend(context, session.user_context || {}),
                        };

                        if (model.ids) {
                            params.method = 'read';
                            params.args = [ids, fields];
                        } else {
                            params.method = 'search_read';
                            params.domain = domain;
                            params.fields = fields;
                            params.orderBy = order;
                        }

                        rpc.query(params).then(function (result) {
                            try { // catching exceptions in model.loaded(...)
                                Promise.resolve(model.loaded(self, result, tmp))
                                    .then(function () { load_model(index + 1); },
                                        function (err) { reject(err); });
                            } catch (err) {
                                console.error(err.message, err.stack);
                                reject(err);
                            }
                        }, function (err) {
                            reject(err);
                        });
                    } else if (model.loaded) {
                        try { // catching exceptions in model.loaded(...)
                            Promise.resolve(model.loaded(self, tmp))
                                .then(function () { load_model(index +1); },
                                    function (err) { reject(err); });
                        } catch (err) {
                            reject(err);
                        }
                    } else {
                        load_model(index + 1);
                    }
                }
            }

            try {
                return load_model(0);
            } catch (err) {
                return Promise.reject(err);
            }
        });

        return loaded;
    },


});

models.push(
    {
        model:  'res.country.state',
        fields: ['name', 'country_id'],
        loaded: function(self, departments) {
            console.log('departments');
            console.log(departments);
            self.departments = departments;
        }
    },
    {
        model:  'res.city.zip',
        fields: ['id','name', 'city_id','dian_code'],
        loaded: function(self, cities) {
            self.cities = cities;
        }
    },
    {
        model:  'res.partner.document.type',
        fields: ['id','name'],
        loaded: function(self, documentos) {
        console.log('documentos');
            console.log(documentos);
            self.documentos = documentos;
        }
    },
    {
        model:  'account.fiscal.position',
        fields: ['id','name'],
        loaded: function(self, fiscal) {
        console.log('fiscal');
            console.log(fiscal);
            self.fiscal = fiscal;
        }
    },
    {
        loaded: function(self) {
           console.log('cargando');
           rpc.query({
                        model: 'res.partner',
                        method: 'get_person_type',
                        args: [{
                                'get_person_type': [0],
                        }]
                        }).then(function (persontypes) {
                        console.log('person type');
                        console.log(persontypes);
                        self.persontypes = persontypes;
           });
           rpc.query({
                        model: 'res.partner',
                        method: 'get_document_type_id',
                        args: [{
                                'get_document_type_id.code': [0],
                        }]
                        }).then(function (doctypes) {
                        console.log(doctypes);
                        self.get_document_type_id = doctypes;
            });


        }
    }
);






});
