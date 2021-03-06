# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
import re
from openerp.report.render.rml2pdf import customfonts

class base_config_settings(osv.osv_memory):
    _name = 'base.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
        'module_multi_company': fields.boolean('Manage multiple companies',
            help='Work in multi-company environments, with appropriate security access between companies.\n'
                 '-This installs the module multi_company.'),
        'module_share': fields.boolean('Allow documents sharing',
            help="""Share or embbed any screen of Odoo."""),
        'module_portal': fields.boolean('Activate the customer portal',
            help="""Give your customers access to their documents."""),
        'module_auth_oauth': fields.boolean('Use external authentication providers, sign in with google, facebook, ...'),
        'module_base_import': fields.boolean("Allow users to import data from CSV files"),
        'module_google_drive': fields.boolean('Attach Google documents to any record',
                                              help="""This installs the module google_docs."""),
        'module_google_calendar': fields.boolean('Allow the users to synchronize their calendar  with Google Calendar',
                                              help="""This installs the module google_calendar."""),
        'font': fields.many2one('res.font', string="Report Font", domain=[('mode', 'in', ('Normal', 'Regular', 'all', 'Book'))],
            help="Set the font into the report header, it will be used as default font in the RML reports of the user company"),
        'module_inter_company_rules': fields.boolean('Manage Inter Company',
            help="""This installs the module inter_company_rules.\n Configure company rules to automatically create SO/PO when one of your company sells/buys to another of your company."""),
        'company_share_partner': fields.boolean('Share partners to all companies',
            help="Share your partners to all companies defined in your instance.\n"
                 " * Checked : Partners are visible for every companies, even if a company is defined on the partner.\n"
                 " * Unchecked : Each company can see only its partner (partners where company is defined). Partners not related to a company are visible for all companies."),
    }

    _defaults= {
        'font': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.font.id,
    }

    def open_company(self, cr, uid, ids, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Your Company',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.company',
            'res_id': user.company_id.id,
            'target': 'current',
        }

    def _change_header(self, header,font):
        """ Replace default fontname use in header and setfont tag """

        default_para = re.sub('fontName.?=.?".*"', 'fontName="%s"'% font,header)
        return re.sub('(<setFont.?name.?=.?)(".*?")(.)', '\g<1>"%s"\g<3>'% font,default_para)

    def set_base_defaults(self, cr, uid, ids, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        wizard = self.browse(cr, uid, ids, context)[0]
        if wizard.font:
            user = self.pool.get('res.users').browse(cr, uid, uid, context)
            font_name = wizard.font.name
            user.company_id.write({'font': wizard.font.id,'rml_header': self._change_header(user.company_id.rml_header,font_name), 'rml_header2': self._change_header(user.company_id.rml_header2, font_name), 'rml_header3': self._change_header(user.company_id.rml_header3, font_name)})
        return {}

    def act_discover_fonts(self, cr, uid, ids, context=None):
        return self.pool.get("res.font").font_scan(cr, uid, context=context)


    def get_default_company_share_partner(self, cr, uid, ids, fields, context=None):
        partner_rule = self.pool['ir.model.data'].xmlid_to_object(cr, uid, 'base.res_partner_rule', context=context)
        return {
            'company_share_partner': not bool(partner_rule.active)
        }

    def set_default_company_share_partner(self, cr, uid, ids, context=None):
        partner_rule = self.pool['ir.model.data'].xmlid_to_object(cr, uid, 'base.res_partner_rule', context=context)
        for wizard in self.browse(cr, uid, ids, context=context):
            self.pool['ir.rule'].write(cr, uid, [partner_rule.id], {'active': not bool(wizard.company_share_partner)}, context=context)


# Preferences wizard for Sales & CRM.
# It is defined here because it is inherited independently in modules sale, crm.
class sale_config_settings(osv.osv_memory):
    _name = 'sale.config.settings'
    _inherit = 'res.config.settings'
    _columns = {
        'module_web_linkedin': fields.boolean('Get contacts automatically from linkedIn',
            help="""When you create a new contact (person or company), you will be able to load all the data from LinkedIn (photos, address, etc)."""),
        'module_crm': fields.boolean('CRM'),
        'module_sale' : fields.boolean('SALE'),
    }
