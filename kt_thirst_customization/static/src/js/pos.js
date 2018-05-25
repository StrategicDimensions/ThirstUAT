odoo.define('kt_thirst_customization', function(require) {
    "use strict";

    var models = require('point_of_sale.models');
    var Model = require('web.DataModel');
    var DB = require('point_of_sale.DB');
    var core = require('web.core');
    var screens = require('point_of_sale.screens');
    var utils = require('web.utils');
    var round_pr = utils.round_precision;


    var PaymentScreenWidget = screens.PaymentScreenWidget;

    
    var QWeb = core.qweb;
    var _t = core._t;
    models.load_fields("product.product", ['price_include_tax', 'qty_available']);
    models.load_fields("pos.session", ['project_id']);

    models.load_models({
        model: 'project.project',
        fields: ['budget_available_amount'],
        domain: function (self){ return [['id','=', self.pos_session.project_id[0]]]; },
        loaded: function (self, res){
            self.budget_available_amount = res[0]['budget_available_amount'];
        },
    }, {after: 'pos.session'});


    var _modelproto = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        load_server_data: function() {
            var self = this;
            var product_index = _.findIndex(this.models, function (model) {
                return model.model === "product.product";
            });
            var product_model = this.models[product_index];
            var fields = product_model.fields;
            var domain = product_model.domain;
            if (product_index !== -1) {
                this.models.splice(product_index, 1);
            }
            return _modelproto.load_server_data.call(this)
            .then(function(){
                var context = product_model.context(self, {});
                _.extend(context, {
                    'location': self.config.stock_location_id[0],
                })
                fields.push('type');
                var records = new Model('product.product').call("search_read",
                [domain=domain, fields=fields, 0, false, false, context=context], {}, {async: false})
                self.chrome.loading_message(_t('Loading') + ' product.product', 1);
                return records.then(function (product) {
                    self.db.add_products(product);
                });
            });
        },
        push_order: function (order, opts) {
            var self = this;
            var def = _modelproto.push_order.apply(this, arguments);
                return def.then(function () {
                    new Model('pos.order').call("fetch_available_budget", [self.pos_session.project_id[0]]
                ).then(function (amount){
                    self.budget_available_amount = amount;
                })
            });
        }
    });
    
    
    
    DB.include({
        add_products: function(products){
            var self = this;
            var new_products = [];
            products.map(function (product){
                if (product.type === 'product' && product.qty_available > 0){
                    new_products.push(product);
                }else if (product.type != 'product'){
                    new_products.push(product);
                }
            });
            this._super(new_products);
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_as_JSON: function () {
            var submitted_order = _super_order.export_as_JSON.call(this);
            var new_val = {
                ordered_type : this.get_paymentlines().length > 0 ? 'cash_bar' : 'event_budget', 
            }
            $.extend(submitted_order,new_val);
            return submitted_order;
        },
    });
    
    PaymentScreenWidget.include({
        validate_order: function (force_validation) {
            var self = this;
            var order = this.pos.get_order();
            this._super(force_validation);
            if (!order.is_paid() && !this.order_is_valid(force_validation) && this.pos.budget_available_amount) {
                var amount = order.get_total_with_tax();
                var budget = this.pos.budget_available_amount;
                amount = round_pr(Math.max(0, amount), this.pos.currency.rounding);
                var new_budget = budget - amount;
                this.pos.budget_available_amount =  round_pr(Math.max(0, new_budget), this.pos.currency.rounding);
                this.finalize_validation();
            }
        },
        finalize_validation: function() {
            var self = this;
            var order = this.pos.get_order();
            this._super();
             _.each(order.get_orderlines(), function (order_line) {
                console.log("order  line===",order_line)
                if(order_line.get_product().type == 'product'){
                    order_line.get_product().qty_available = order_line.get_product().qty_available - order_line.get_quantity();
                    self.pos.chrome.screens['products'].product_list_widget.product_cache.clear_node(order_line.get_product().id);
                }
             });
        },
    });
    
});