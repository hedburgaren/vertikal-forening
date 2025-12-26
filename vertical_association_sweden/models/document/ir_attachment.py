# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    # Document relationship
    document_ids = fields.One2many(
        'vf.document',
        'attachment_id',
        string='Documents'
    )
    document_version_ids = fields.One2many(
        'vf.document.version',
        'attachment_id',
        string='Document Versions'
    )
    
    # Computed fields
    is_vf_document = fields.Boolean(
        compute='_compute_is_vf_document',
        string='Is Association Document'
    )
    
    def _compute_is_vf_document(self):
        for attachment in self:
            attachment.is_vf_document = bool(attachment.document_ids or attachment.document_version_ids)

    def action_create_document(self):
        """Create a document from this attachment"""
        self.ensure_one()
        return {
            'name': _('Create Document'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.document',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_attachment_id': self.id},
        }
