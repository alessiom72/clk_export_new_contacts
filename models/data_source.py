from odoo import _, fields, models, api


class DataSource(models.Model):
    _inherit = 'data.source'

    remote_directory_export = fields.Char(_('Export directory'))
    partner_export_filename = fields.Char(_('Name of the exported file'))
