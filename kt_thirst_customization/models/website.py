from odoo import api, models, fields, tools, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError

class Website(models.Model):
    _inherit = 'website'



    def get_current_pricelist(self):
        """
        :returns: The current pricelist record
        """
        # The list of available pricelists for this user.
        # If the user is signed in, and has a pricelist set different than the public user pricelist
        # then this pricelist will always be considered as available
        available_pricelists = self.get_pricelist_available()
        pl = None
        partner = self.env.user.partner_id
        #Jagadeesh added
        if self.env.user.name == 'Public user':
	    if request.session.get('quotation_partner_id'):
                partner_id = request.session['quotation_partner_id']
                partner = self.env['res.partner'].sudo().browse(partner_id)
        #Jagadeesh end
        if request.session.get('website_sale_current_pl'):
            # `website_sale_current_pl` is set only if the user specifically chose it:
            #  - Either, he chose it from the pricelist selection
            #  - Either, he entered a coupon code
            pl = self.env['product.pricelist'].browse(request.session['website_sale_current_pl'])
            if pl not in available_pricelists:
                pl = None
                request.session.pop('website_sale_current_pl')

        if not pl:
            # If the user has a saved cart, it take the pricelist of this cart, except if
            # the order is no longer draft (It has already been confirmed, or cancelled, ...)
            pl = partner.last_website_so_id.state == 'draft' and partner.last_website_so_id.pricelist_id
            if not pl:
                # The pricelist of the user set on its partner form.
                # If the user is not signed in, it's the public user pricelist
                pl = partner.property_product_pricelist
            if available_pricelists and pl not in available_pricelists:
                # If there is at least one pricelist in the available pricelists
                # and the chosen pricelist is not within them
                # it then choose the first available pricelist.
                # This can only happen when the pricelist is the public user pricelist and this pricelist is not in the available pricelist for this localization
                # If the user is signed in, and has a special pricelist (different than the public user pricelist),
                # then this special pricelist is amongs these available pricelists, and therefore it won't fall in this case.
                pl = available_pricelists[0]

        if not pl:
            _logger.error('Fail to find pricelist for partner "%s" (id %s)', partner.name, partner.id)
        return pl


    @api.multi
    def sale_get_order(self, force_create=False, code=None, update_pricelist=False, force_pricelist=False):
        """ Return the current sale order after mofications specified by params.
        :param bool force_create: Create sale order if not already existing
        :param str code: Code to force a pricelist (promo code)
                         If empty, it's a special case to reset the pricelist with the first available else the default.
        :param bool update_pricelist: Force to recompute all the lines from sale order to adapt the price with the current pricelist.
        :param int force_pricelist: pricelist_id - if set,  we change the pricelist with this one
        :returns: browse record for the current sale order
        """
        self.ensure_one()
        partner = self.env.user.partner_id
        #Jagadeesh added
        if self.env.user.name == 'Public user':
	    if request.session.get('quotation_partner_id'):
                partner_id = request.session['quotation_partner_id']
                partner = self.env['res.partner'].sudo().browse(partner_id)
        #Jagadeesh end 
        sale_order_id = request.session.get('sale_order_id')
        if not sale_order_id:
            last_order = partner.last_website_so_id
            available_pricelists = self.get_pricelist_available()
            # Do not reload the cart of this user last visit if the cart is no longer draft or uses a pricelist no longer available.
            sale_order_id = last_order.state == 'draft' and last_order.pricelist_id in available_pricelists and last_order.id

        pricelist_id = request.session.get('website_sale_current_pl') or self.get_current_pricelist().id

        if self.env['product.pricelist'].browse(force_pricelist).exists():
            pricelist_id = force_pricelist
            request.session['website_sale_current_pl'] = pricelist_id
            update_pricelist = True

        if not self._context.get('pricelist'):
            self = self.with_context(pricelist=pricelist_id)

        # Test validity of the sale_order_id
        sale_order = self.env['sale.order'].sudo().browse(sale_order_id).exists() if sale_order_id else None
        #Jagadeesh added
        payment_term_id = self.sale_get_payment_term(partner)
        if self.env.user.name == 'Public user':
            payment_term_id = partner.property_payment_term_id.id
        #Jagadeesh end

        # create so if needed
        if not sale_order and (force_create or code):
            # TODO cache partner_id session
            affiliate_id = request.session.get('affiliate_id')
            if self.env['res.users'].sudo().browse(affiliate_id).exists():
                salesperson_id = affiliate_id
            else:
                salesperson_id = request.website.salesperson_id.id
            addr = partner.address_get(['delivery', 'invoice'])
            sale_order = self.env['sale.order'].sudo().create({
                'partner_id': partner.id,
                'pricelist_id': pricelist_id,
                'payment_term_id': payment_term_id, #self.sale_get_payment_term(partner), #Jagadeesh
                'team_id': self.salesteam_id.id,
                'partner_invoice_id': addr['invoice'],
                'partner_shipping_id': addr['delivery'],
                'user_id': salesperson_id or self.salesperson_id.id,
            })

            # set fiscal position
            if request.website.partner_id.id != partner.id:
                sale_order.onchange_partner_shipping_id()
            else: # For public user, fiscal position based on geolocation
                country_code = request.session['geoip'].get('country_code')
                if country_code:
                    country_id = request.env['res.country'].search([('code', '=', country_code)], limit=1).id
                    fp_id = request.env['account.fiscal.position'].sudo()._get_fpos_by_region(country_id)
                    sale_order.fiscal_position_id = fp_id
                else:
                    # if no geolocation, use the public user fp
                    sale_order.onchange_partner_shipping_id()

            request.session['sale_order_id'] = sale_order.id

            if request.website.partner_id.id != partner.id:
                partner.write({'last_website_so_id': sale_order_id})

        if sale_order:

            # check for change of pricelist with a coupon
            pricelist_id = pricelist_id or partner.property_product_pricelist.id

            # check for change of partner_id ie after signup
            if sale_order.partner_id.id != partner.id and request.website.partner_id.id != partner.id:
                flag_pricelist = False
                if pricelist_id != sale_order.pricelist_id.id:
                    flag_pricelist = True
                fiscal_position = sale_order.fiscal_position_id.id

                # change the partner, and trigger the onchange
                sale_order.write({'partner_id': partner.id})
                sale_order.onchange_partner_id()
                sale_order.onchange_partner_shipping_id() # fiscal position
                sale_order['payment_term_id'] = self.sale_get_payment_term(partner)

                # check the pricelist : update it if the pricelist is not the 'forced' one
                values = {}
                if sale_order.pricelist_id:
                    if sale_order.pricelist_id.id != pricelist_id:
                        values['pricelist_id'] = pricelist_id
                        update_pricelist = True

                # if fiscal position, update the order lines taxes
                if sale_order.fiscal_position_id:
                    sale_order._compute_tax_id()

                # if values, then make the SO update
                if values:
                    sale_order.write(values)

                # check if the fiscal position has changed with the partner_id update
                recent_fiscal_position = sale_order.fiscal_position_id.id
                if flag_pricelist or recent_fiscal_position != fiscal_position:
                    update_pricelist = True

            if code and code != sale_order.pricelist_id.code:
                code_pricelist = self.env['product.pricelist'].search([('code', '=', code)], limit=1)
                if code_pricelist:
                    pricelist_id = code_pricelist.id
                    update_pricelist = True
            elif code is not None and sale_order.pricelist_id.code:
                # code is not None when user removes code and click on "Apply"
                pricelist_id = partner.property_product_pricelist.id
                update_pricelist = True

            # update the pricelist
            if update_pricelist:
                request.session['website_sale_current_pl'] = pricelist_id
                values = {'pricelist_id': pricelist_id}
                sale_order.write(values)
                for line in sale_order.order_line:
                    if line.exists():
                        sale_order._cart_update(product_id=line.product_id.id, line_id=line.id, add_qty=0)
            #Jagadeesh
            '''if sale_order.state == 'sale' and sale_order.invoice_ids:
                paid = True
                for inv in sale_order.invoice_ids:
                    if inv.state != 'paid':
                        paid = False
                        break;
                if paid:
                    request.session['quotation_partner_id'] = False'''
	    if sale_order.state == 'sale':
                payment_obj = self.env['account.payment'].sudo().search([('communication','=',sale_order.name),('amount','=',sale_order.amount_total)],limit=1)
                if payment_obj and payment_obj.state == 'posted':
                    request.session['quotation_partner_id'] = False
            #Jagadeesh end
        else:
            request.session['sale_order_id'] = None
            return None

        #Jagadeesh 
        if request.session.get('from_quote'):
            if request.session['from_quote']:
                request.session['from_quote'] = False
        #Jagadeesh end

        return sale_order

