# -*- coding: utf-8 -*-
from openerp import SUPERUSER_ID
from openerp.osv import osv
from openerp.tools.translate import _
from openerp.exceptions import UserError


class sale_order(osv.Model):
    _inherit = "sale.order"

    def _cart_find_product_line(self, cr, uid, ids, product_id=None, line_id=None, context=None, **kwargs):
        line_ids = super(sale_order, self)._cart_find_product_line(cr, uid, ids, product_id, line_id, context=context)
        if line_id:
            return line_ids
        for so in self.browse(cr, uid, ids, context=context):
            domain = [('id', 'in', line_ids)]
            if context.get("event_ticket_id"):
                domain += [('event_ticket_id', '=', context.get("event_ticket_id"))]
            return self.pool.get('sale.order.line').search(cr, SUPERUSER_ID, domain, context=context)

    def _website_product_id_change(self, cr, uid, ids, order_id, product_id, qty=0, line_id=None, context=None):
        values = super(sale_order, self)._website_product_id_change(cr, uid, ids, order_id, product_id, qty=qty, line_id=line_id, context=None)

        event_ticket_id = None
        if context.get("event_ticket_id"):
            event_ticket_id = context.get("event_ticket_id")
        elif line_id:
            line = self.pool.get('sale.order.line').browse(cr, SUPERUSER_ID, line_id, context=context)
            if line.event_ticket_id:
                event_ticket_id = line.event_ticket_id.id
        else:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            if product.event_ticket_ids:
                event_ticket_id = product.event_ticket_ids[0].id

        if event_ticket_id:
            ticket = self.pool.get('event.event.ticket').browse(cr, uid, event_ticket_id, context=context)
            if product_id != ticket.product_id.id:
                raise UserError(_("The ticket doesn't match with this product."))

            values['product_id'] = ticket.product_id.id
            values['event_id'] = ticket.event_id.id
            values['event_ticket_id'] = ticket.id
            values['price_unit'] = ticket.price
            values['name'] = "%s: %s" % (ticket.event_id.name, ticket.name)

        return values

    def _cart_update(self, cr, uid, ids, product_id=None, line_id=None, add_qty=0, set_qty=0, context=None, **kwargs):
        OrderLine = self.pool['sale.order.line']
        Attendee = self.pool['event.registration']
        Ticket = self.pool['event.event.ticket']

        if line_id:
            line = OrderLine.browse(cr, uid, line_id, context=context)
            ticket = line.event_ticket_id
            old_qty = int(line.product_uom_qty)
        else:
            line, ticket = None, None
            ticket_ids = Ticket.search(cr, uid, [('product_id', '=', product_id)], limit=1, context=context)
            if ticket_ids:
                ticket = Ticket.browse(cr, uid, ticket_ids[0], context=context)
            old_qty = 0
        new_qty = set_qty if set_qty else (add_qty or 0 + old_qty)

        # case: buying tickets for a sold out ticket
        values = {}
        if ticket and ticket.seats_available <= 0:
            values['warning'] = _('Sorry, The %(ticket)s tickets for the %(event)s event are sold out.') % {
                'ticket': ticket.name,
                'event': ticket.event_id.name}
            new_qty, set_qty, add_qty = 0, 0, 0
        # case: buying tickets, too much attendees
        elif ticket and new_qty > ticket.seats_available:
            values['warning'] = _('Sorry, only %(remaining_seats)d seats are still available for the %(ticket)s ticket for the %(event)s event.') % {
                'remaining_seats': ticket.seats_available,
                'ticket': ticket.name,
                'event': ticket.event_id.name}
            new_qty, set_qty, add_qty = ticket.seats_available, ticket.seats_available, 0

        values.update(super(sale_order, self)._cart_update(
            cr, uid, ids, product_id, line_id, add_qty, set_qty, context, **kwargs))

        # removing attendees
        if ticket and new_qty < old_qty:
            attendees = Attendee.search(
                cr, uid, [
                    ('state', '!=', 'cancel'),
                    ('sale_order_id', '=', ids[0])
                    ('event_ticket_id', '=', ticket.id)
                ], offset=new_qty, limit=(old_qty-new_qty),
                order='create_date asc', context=context)
            Attendee.button_reg_cancel(cr, uid, attendees, context=context)
        # adding attendees
        elif ticket and new_qty > old_qty:
            line = OrderLine.browse(cr, uid, values['line_id'], context=context)
            line._update_registrations(confirm=False, registration_data=kwargs.get('registration_data', []))
        return values
