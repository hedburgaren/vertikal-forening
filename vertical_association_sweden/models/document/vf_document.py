# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfDocument(models.Model):
    _name = 'vf.document'
    _description = 'Association Document'
    _order = 'date desc, name'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    name = fields.Char(
        string='Document Name',
        required=True,
        tracking=True
    )
    description = fields.Text(
        string='Description',
        tracking=True
    )
    
    # Organization
    category_id = fields.Many2one(
        'vf.document.category',
        string='Category',
        required=True,
        tracking=True
    )
    
    # Visibility and access
    visibility = fields.Selection([
        ('public', 'Public'),
        ('members', 'Members Only'),
        ('leadership', 'Leadership Only'),
        ('custom', 'Custom'),
    ], string='Visibility', required=True, default='members', tracking=True)
    
    # Custom visibility settings
    allowed_member_ids = fields.Many2many(
        'vf.member',
        'vf_document_member_rel',
        'document_id',
        'member_id',
        string='Allowed Members',
        tracking=True
    )
    allowed_role_ids = fields.Many2many(
        'vf.role',
        'vf_document_role_rel',
        'document_id',
        'role_id',
        string='Allowed Roles',
        tracking=True
    )
    
    # Document content
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='File',
        required=True,
        tracking=True,
        domain=[('res_model', '=', 'vf.document')]
    )
    
    # Version control
    version_ids = fields.One2many(
        'vf.document.version',
        'document_id',
        string='Versions'
    )
    current_version = fields.Integer(
        string='Current Version',
        default=1,
        readonly=True
    )
    
    # Metadata
    date = fields.Date(
        string='Document Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    author_id = fields.Many2one(
        'res.partner',
        string='Author',
        required=True,
        default=lambda self: self.env.user.partner_id,
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Tags
    tag_ids = fields.Many2many(
        'vf.document.tag',
        'vf_document_tag_rel',
        'document_id',
        'tag_id',
        string='Tags'
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    file_size = fields.Integer(
        string='File Size',
        compute='_compute_file_size',
        store=True
    )
    download_count = fields.Integer(
        string='Downloads',
        default=0,
        readonly=True
    )
    
    # Constraints
    _sql_constraints = [
        ('name_category_unique', 'unique(name, category_id)', 
         'Document name must be unique within category!'),
    ]

    @api.depends('name', 'current_version')
    def _compute_display_name(self):
        for document in self:
            if document.current_version > 1:
                document.display_name = f'{document.name} v{document.current_version}'
            else:
                document.display_name = document.name

    @api.depends('attachment_id.file_size')
    def _compute_file_size(self):
        for document in self:
            document.file_size = document.attachment_id.file_size or 0

    @api.constrains('attachment_id')
    def _check_attachment_unique(self):
        for document in self:
            if document.attachment_id:
                # Check if attachment is used by another document
                other = self.search([
                    ('attachment_id', '=', document.attachment_id.id),
                    ('id', '!=', document.id)
                ])
                if other:
                    raise ValidationError(_('This file is already used by another document.'))

    def action_publish(self):
        """Publish the document"""
        self.write({'state': 'published'})
        return True

    def action_archive(self):
        """Archive the document"""
        self.write({'state': 'archived'})
        return True

    def action_draft(self):
        """Return to draft"""
        self.write({'state': 'draft'})
        return True

    def action_download(self):
        """Download the document and increment counter"""
        self.ensure_one()
        self.download_count += 1
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.attachment_id.id}?download=true',
            'target': 'self',
        }

    def action_new_version(self):
        """Create a new version of the document"""
        self.ensure_one()
        return {
            'name': _('New Document Version'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.document.version',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_document_id': self.id,
                'default_version': self.current_version + 1,
            },
        }

    def action_view_versions(self):
        """View all versions of this document"""
        self.ensure_one()
        action = self.env.ref('vertical_association_sweden.vf_document_version_action').read()[0]
        action['domain'] = [('document_id', '=', self.id)]
        return action

    def check_access(self, member_id):
        """Check if a member has access to this document"""
        document = self.browse(self.id)
        
        if document.visibility == 'public':
            return True
        
        if document.visibility == 'members' and member_id:
            return True
        
        if document.visibility == 'leadership' and member_id:
            member = self.env['vf.member'].browse(member_id)
            return member.has_active_mandates
        
        if document.visibility == 'custom':
            if member_id in document.allowed_member_ids.ids:
                return True
            # Check role-based access
            member = self.env['vf.member'].browse(member_id)
            for mandate in member.active_mandate_ids:
                if mandate.position_id.role_id in document.allowed_role_ids:
                    return True
        
        return False

    @api.model
    def get_accessible_documents(self, member_id):
        """Get all documents accessible to a member"""
        documents = self.search([('state', '=', 'published')])
        accessible = self.env['vf.document']
        
        for document in documents:
            if document.check_access(member_id):
                accessible |= document
        
        return accessible
