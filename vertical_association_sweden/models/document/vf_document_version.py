# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfDocumentVersion(models.Model):
    _name = 'vf.document.version'
    _description = 'Document Version'
    _order = 'version desc'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    document_id = fields.Many2one(
        'vf.document',
        string='Document',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='File',
        required=True,
        tracking=True
    )
    version = fields.Integer(
        string='Version Number',
        required=True,
        tracking=True
    )
    changelog = fields.Text(
        string='Changelog',
        tracking=True,
        help='Description of changes in this version'
    )
    
    # Metadata
    created_date = fields.Datetime(
        string='Created Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    created_by = fields.Many2one(
        'res.partner',
        string='Created By',
        required=True,
        default=lambda self: self.env.user.partner_id,
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    
    # Status
    is_current = fields.Boolean(
        string='Is Current Version',
        compute='_compute_is_current',
        store=True
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    file_size = fields.Integer(
        related='attachment_id.file_size',
        readonly=True
    )
    file_type = fields.Char(
        related='attachment_id.mimetype',
        readonly=True
    )

    @api.depends('document_id', 'version')
    def _compute_display_name(self):
        for version in self:
            version.display_name = f'{version.document_id.name} v{version.version}'

    @api.depends('document_id.current_version')
    def _compute_is_current(self):
        for version in self:
            version.is_current = version.version == version.document_id.current_version - 1

    @api.model
    def create(self, vals):
        version = super().create(vals)
        
        # Update document's current attachment if this is the latest version
        if version.version == version.document_id.current_version - 1:
            version.document_id.write({'attachment_id': version.attachment_id.id})
        
        return version

    def action_download(self):
        """Download the version file"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.attachment_id.id}?download=true',
            'target': 'new',
        }

    def action_view_file(self):
        """View the version file"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.attachment_id.id}',
            'target': 'new',
        }

    def action_restore(self):
        """Restore this version as current"""
        self.ensure_one()
        
        # Update document to use this version's attachment
        self.document_id.write({
            'attachment_id': self.attachment_id.id,
            'current_version': self.version + 1,
        })
        
        # Create a new version record for the restoration
        self.env['vf.document.version'].create({
            'document_id': self.document_id.id,
            'attachment_id': self.attachment_id.id,
            'version': self.document_id.current_version,
            'changelog': f'Restored from version {self.version}',
        })
        
        return True
