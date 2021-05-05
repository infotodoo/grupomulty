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
var gui = require('point_of_sale.gui');
var screens = require('point_of_sale.screens');
var _t = core._t;

var models = module.PosModel.prototype.models;
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


var load_fields = function(model_name, fields) {
    if (!(fields instanceof Array)) {
        fields = [fields];
    }

    var models = exports.PosModel.prototype.models;
    for (var i = 0; i < models.length; i++) {
        var model = models[i];
        if (model.model === model_name) {
            // if 'fields' is empty all fields are loaded, so we do not need
            // to modify the array
            if ((model.fields instanceof Array) && model.fields.length > 0) {
                model.fields = model.fields.concat(fields || []);
            }
        }
    }
};


var set_fields_to_model = function(fields, models) {
    for(var i = 0; i < models.length; i++) {

        if(models[i].model == 'res.partner') {
            var model = models[i];
            for(var j = 0; j < fields.length; j++){

                model.fields.push(fields[j]);
            }


            var old_loaded = model.loaded;
            model.loaded = function(self, partners) {
                for(var i = 0; i < partners.length; i++) {
                    if(partners[i].id == self.company.partner_id[0]) {
                        var company_partner = partners.splice(i, 1);
                        self.company_partner = company_partner;
                    }
                }
                old_loaded(self, partners);
            }
        }
    }
}
set_fields_to_model(partner_fields, models);


// extending client screen behavior
screens.ClientListScreenWidget.include({

    is_company_click_handler: function($el, partner_exist) {

        var is_company = $(".client-is-company").is(":checked");
        var name = $(".client-name");

        if(name.val() === "" && is_company) {
            name.attr("placeholder", _t("Company name"));
        } else {
            name.attr("placeholder", _t("Name"));
        }

        if(is_company) {
            name.removeAttr("disabled");
            $(".client-name").css("visibility", "visible");
            name.change(function(event) {
                $(".client-companyname").val($(event.target).val());
            });
            if(!partner_exist) {
                $(".client-doctype").val("31").trigger("change");
            }
            $('.partner-names').hide();
            $(".client-persontype").removeAttr("disabled").val('2').parent().css("visibility", "visible");
            $(".client-first-name").val("");
            $(".client-second-name").val("");
            $(".client-first-lastname").val("");
            $(".client-second-lastname").val("");
        } else {
            name.attr("disabled", "disabled");
            name.unbind("change");
            if(!partner_exist) {
                $(".client-doctype").val("1").trigger("change");
            }
            $(".client-name").css("visibility", "hidden");
            $(".client-persontype").attr("disabled", "disabled").val('1').parent().css("visibility", "hidden");;
            $(".client-companyname").val("");
            $('.partner-names').show();
        }

    },

    _concat_names: function($el) {
        var names = [
            $el.find(".client-first-name").val(),
            $el.find(".client-second-name").val(),
            $el.find(".client-first-lastname").val(),
            $el.find(".client-second-lastname").val()
         ];

        var concatenated_name = $.grep(names, Boolean).join(" ");

       if(concatenated_name.length > 0) {
           $el.find(".client-name").val(concatenated_name);
           $el.find(".client-name").css("visibility", "visible");
       } else {
           $el.find(".client-name").css("visibility", "hidden");
       }
    },

    setup_res_partner_logic: function() {

        var self = this;

        var names = [".client-first-name",
                     ".client-second-name",
                     ".client-first-lastname",
                     ".client-second-lastname"];

        $(names.join(", ")).keyup(function() {
              self._concat_names($(".client-details"));
        });
        this.$('.client-is-company').click(function(event){
            self.is_company_click_handler($(this));
        });




        $('.client-doctype').on('change', function(event) {
            self.doctype_event_handler(event.target);
        });
        $('.client-ubicacion-city').on('change', function(event) {
            var ubicacion_select = $('.client-ubicacion-city');
            var state = $('.client-address-state');
            var ciudad = $('.client-address-city');
            var id_ciudad;

            console.log('ubicacion');
            console.log(ubicacion_select.val());
            console.log(event.target.val);
            rpc.query({
                        model: 'res.city.zip',
                        method: 'search_read',
                        domain: [['id', '=', ubicacion_select.val()]],
                        fields: ['name','city_id'],
                        }).then(function (data) {
                        console.log('rescityzip');
                        console.log(data);
                        ciudad.val(data[0]['city_id'][1])
                        id_ciudad = data[0]['city_id'][0]
                        rpc.query({
                        model: 'res.city',
                        method: 'search_read',
                        domain: [['id', '=', id_ciudad]],
                        fields: ['name','state_id'],
                        }).then(function (data1) {
                        state.val(data1[0]['state_id'][0])
                        console.log('ciudad');
                        console.log(data1);

           });
           });
           console.log('idiiiii')
           console.log(id_ciudad)




            //self.doctype_event_handler(event.target);
        });

        $('.identification-number').css("visibility", "hidden")
                                   .attr("disabled", "disabled");

       $('.formated-nit').css("visibility", "hidden")
                         .attr("disabled", "disabled");



        $('.client-identification-number').on('focusout', function(event) {
            var xidentification = $(event.target).val();
            var doctype = $('.client-doctype').val();
            var nit_field = $('.client-formatednit');

            if(doctype == 31) {
                var have_min = self._check_ident(event);
                var have_letter = self._check_ident_num(event);

                if(!have_letter && have_min) {
                    var dv = self._check_dv(xidentification);
                    var formatedNit = self.formated_nit(xidentification);
                    nit_field.val(formatedNit + "-" + dv);
                } else {
                    nit_field.val("");
                }
            }
            if(this.not_save) {
                this.not_save = false;
            }
        });

        // Asignando a Colombia como país por defecto
        var country_select = $('.client-address-country');
        var state_select = $('.client-address-state');
        var city_select = $('.client-address-city');

        country_select.val("49")
        country_select.change(function(event) {
            $.each(state_select.find('option'), function() {
                if($(this).attr("country_id") !== country_select.val())
                {
                    $(this).hide();
                } else {
                    $(this).show();
                }
            });
            if(country_select.val()) {
                state_select.removeAttr("disabled");
            } else {
                state_select.attr("disabled", "disabled");
                city_select.attr("disabled", "disabled");
                state_select.val("");
                city_select.val("");
            }

        }).trigger("change");

        state_select.change(function(event) {
            $.each(city_select.find('option'), function() {
                if($(this).attr("state_id") !== state_select.val()) {
                    $(this).hide();
                } else {
                    $(this).show();
                }
            });
            city_select.removeAttr("disabled");
        }).trigger("change");
    },

    formated_nit: function(nit) {
        nit = nit.toString();
        var pattern = /(-?\d+)(\d{3})/;
        while (pattern.test(nit))
          nit = nit.replace(pattern, "$1.$2");
        return nit;
    },

    _check_dv: function(nit) {
        while (nit.length < 15) nit = "0" + nit;
        var vl = nit.split("");
        var result = (
            parseInt(vl[0])*71 +
            parseInt(vl[1])*67 +
            parseInt(vl[2])*59 +
            parseInt(vl[3])*53 +
            parseInt(vl[4])*47 +
            parseInt(vl[5])*43 +
            parseInt(vl[6])*41 +
            parseInt(vl[7])*37 +
            parseInt(vl[8])*29 +
            parseInt(vl[9])*23 +
            parseInt(vl[10])*19 +
            parseInt(vl[11])*17 +
            parseInt(vl[12])*13 +
            parseInt(vl[13])*7 +
            parseInt(vl[14])*3
        ) % 11;

        if($.inArray(result, [0,1]) !== -1) {
            return result;
        } else {
            return (11 - result);
        }
    },

    _check_ident: function(event) {
        var xidentification = $(event.target).val();

        if(xidentification.length < 2 || xidentification.length > 12) {
            this.gui.show_popup('error', _t('Error! Number of digits in Identification number must be between 2 and 12'));
            this.not_save = true;
            return false;
        }
        this.not_save = false;
        return true;
    },

    _check_ident_num: function(event) {
        var doctype = $(".client-doctype").val();
        var xidentification = $(event.target).val();

        if(doctype != 1) {
            if(xidentification && doctype != 21 && doctype != 41) {
                if(xidentification.search(/^[\d]+$/) != 0) {
                    this.gui.show_popup('error', _t('¡Error! Identification number can only have numbers'));
                    this.not_save = true;
                    return true;
                } else {
                    this.not_save = false;
                }
            }
        }
        return false;
    },

    doctype_event_handler: function(target) {
        var target = $(target);
        var id_field = $('.identification-number');
        var nit_field = $('.formated-nit');
        console.log(target.val());
        if(target.val() == 1 || target.val() == 43) {
            id_field.css("visibility", "hidden")
                    .attr("disabled", "disabled");
            this.not_save = false;
        } else {
            id_field.css("visibility", "visible")
                    .removeAttr("disabled", "disabled");
        }

        if(target.val() == 31) {
            nit_field.css("visibility", "visible")
                     .removeAttr("disabled", "disabled");
        } else {
            nit_field.css("visibility", "hidden")
                     .removeAttr("disabled", "disabled");
        }
        id_field.val("");
    },

    display_client_details: function(visibility,partner,clickpos) {
        this._super(visibility,partner,clickpos);
        this.not_save = false;
        var client_name = $(".client-name");
        var client_doctype = $(".client-doctype");
        var partner_exist = false;

        this.setup_res_partner_logic();
        if (visibility === 'show') {
            client_name.css("visibility", "visible");
        } else if (visibility === 'edit') {
            if(partner.id) {
                partner_exist = true;
            }
            this.is_company_click_handler($(this), partner_exist);

            if(client_doctype.val() != 1) {
                client_doctype.trigger("change");
            }
            if(client_name.val()) {
                client_name.css("visibility", "visible");
            }
        }
    },

    _partner_search_string: function(partner) {
        var str = this._super(partner);
        return str;
    },

    save_client_details: function(partner) {
        var self = this;
        var first_name = $(".client-first-name").val();
        var first_lastname = $(".client-first-lastname").val();
        var is_company = $(".client-is-company").is(":checked");
        var zip_id = $(".client-ubicacion-city").val();
        var property_account_position_id = $(".client-fiscal").val();

        if(!is_company) {
            if(!first_name || !first_lastname) {
                this.gui.show_popup('error',_t('First name and Lastname are required'));
                return;
            }
            $(".client-is-company").removeClass("detail");
        }

        if($(".client-doctype").val() === '1' || $(".client-doctype").val() === '43') {
            $(".client-identification-number").removeClass("detail");
        }

        if(this.not_save) {
            this.gui.show_popup('error', _t('Error! You have pending errors, please fix them before you save the client'));
            return;
        }



        console.log('Guardando', partner);
        //this._super(partner);


        var fields = {};
        this.$('.client-details-contents .detail').each(function(idx,el){
            fields[el.name] = el.value;
        });

        if (!fields.name) {
            this.gui.show_popup('error',_t('A Customer Name Is Required'));
            return;
        }

        if (this.uploaded_picture) {
            fields.image = this.uploaded_picture;
        }

        fields.id           = partner.id || false;
        fields.country_id   = parseInt(fields.country_id) || false;
        fields.zip_id   = parseInt(zip_id) || false;
        fields.property_account_position_id   = parseInt(property_account_position_id) || false;
        fields.barcode      = fields.barcode || '';
        console.log('createui ssssssssssssssssssssssssss');
        console.log(fields);

        rpc.query({
                        model: 'res.partner',
                        method: 'create_from_ui',
                        args: [fields]
                        }).then(function(partner_id){
            console.log('createui ssssssssssssssssssssssssss');
            self.saved_client_details(partner_id);
        },function(err,event){

            //event.preventDefault();

            console.log('testtt el error', err);

            if(err.code == 200){
                self.gui.show_popup('error',{
                    'title': _t('Identification number must be unique!'),
                    'body': _t('Identification number must be unique!'),
                });

            } else {
                self.gui.show_popup('error',{
                    'title': _t('Error: Could not Save Changes'),
                    'body': _t('Your Internet connection is probably down.'),
                });
            }
        });


        $(".client-identification-number").addClass("detail");
        $(".client-is-company").addClass("detail");
    },

});





});
