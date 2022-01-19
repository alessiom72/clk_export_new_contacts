import datetime
import tempfile
import shutil
import os

from odoo import _, api, fields, models
import xlwt
import logging
_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    last_export_date = fields.Datetime(string=_('Last export'), default=fields.Datetime.now)

    @api.model_create_multi
    def create(self, values):
        for v in values:
            v['last_export_date'] = None

        return super(Partner, self).create(values)

    def export_modified_new_partners(self):
        filename = ''
        tmp_file, tmp_filename = tempfile.mkstemp()
        wb = xlwt.Workbook()
        ws = wb.add_sheet(_('Contacts'))

        # Get records modified after the last export
        modified = []
        for record in self.search([]):
            if record.commercial_partner_id.id == \
                    record.id and (not record.last_export_date or record.write_date > record.last_export_date):
                modified.append(record)
                record.write({
                    'last_export_date': fields.Datetime.now()
                })

        if modified:
            headers = [
                'ID',
                'Codice',
                'RagioneSociale',
                'indirizzo',
                'c a p',
                'localita',
                'provincia',
                'partita iva',
                'codice fiscale',
                'telefono',
                'telefono cellulare',
                'fax',
                'Nazione',
                'email',
                'email p e c',
                'altre email'
            ]

            row = 0
            column = 0
            for header in headers:
                ws.write(row, column, header)
                column += 1

            for record in modified:
                row += 1
                column = 0

                ws.write(row, column, record.id)
                column += 1

                ws.write(row, column, record.x_code if record.x_code else '')
                column += 1

                ws.write(row, column, record.display_name if record.display_name else '')
                column += 1

                ws.write(row, column, (record.street if record.street else '' + ' ' + record.street2 if record.street2 else '').strip())
                column += 1

                ws.write(row, column, record.zip if record.zip else '')
                column += 1

                ws.write(row, column, record.city if record.city else '')
                column += 1

                ws.write(row, column, record.state_id.code if record.state_id.code else '')
                column += 1

                ws.write(row, column, record.vat if record.vat else '')
                column += 1

                ws.write(row, column, record.fiscalcode if record.fiscalcode else '')
                column += 1

                ws.write(row, column, record.phone if record.phone else '')
                column += 1

                ws.write(row, column, record.mobile if record.mobile else '')
                column += 1

                ws.write(row, column, record.x_fax if record.x_fax else '')
                column += 1

                ws.write(row, column, record.country_id.code if record.country_id.code else '')
                column += 1

                ws.write(row, column, record.email if record.email else '')
                column += 1

                ws.write(row, column, record.pec_mail if record.pec_mail else '')
                column += 1

                other_email = []
                if record.child_ids:
                    for child in record.child_ids:
                        if child.email:
                            other_email.append(child.email)

                if other_email:
                    ws.write(row,column, ','.join(other_email))
                    column += 1

        wb.save(tmp_filename)

        # Copy file to FTP server
        ftp_connections = self.env['data.source'].search([('partner_export_filename', '!=', '')])
        if ftp_connections:
            backup_filename, backup_extension = os.path.splitext(ftp_connections.partner_export_filename)

            for ftp_connection in ftp_connections:
                if ftp_connection.method == 'ftp':
                    xls_file_handle = open(tmp_filename, 'rb')
                    conn = ftp_connection.ftp_connection()
                    destination = ftp_connection.partner_export_filename
                    if ftp_connection.remote_directory_export:
                        destination = ftp_connection.remote_directory_export + '/' + destination

                    conn.storbinary('STOR %s' % destination, xls_file_handle)
                    conn.close()
                elif ftp_connection.method == 'sftp':
                    conn = ftp_connections.sftp_connection()
                    if ftp_connection.remote_directory_export:
                        conn.cd(ftp_connection.remote_directory_export)

                    conn.put(tmp_filename)

            backup_directory = os.path.dirname(os.path.realpath(__file__)) + '/../export_backup'
            if not os.path.isdir(backup_directory):
                os.mkdir(backup_directory)

            shutil.copy(tmp_filename, backup_directory + '/' + backup_filename + '_' + datetime.date.today().strftime('%Y%m%d_%H%M') + '.' + backup_extension)
