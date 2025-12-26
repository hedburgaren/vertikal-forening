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
    allowed_group_ids = fields.Many2many(
        'vf.group',
        'vf_document_group_rel',
        'document_id',
        'group_id',
        string='Allowed Groups',
        tracking=True
    )
    allowed_section_ids = fields.Many2many(
        'vf.section',
        'vf_document_section_rel',
        'document_id',
        'section_id',
        string='Allowed Sections',
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
    
    # Status and lifecycle
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ], string='State', default='draft', required=True, tracking=True)
    
    # Version control
    current_version = fields.Integer(
        string='Current Version',
        default=1,
        readonly=True
    )
    version_ids = fields.One2many(
        'vf.document.version',
        'document_id',
        string='Versions'
    )
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Latest File',
        tracking=True
    )
    
    # Links to other entities
    member_ids = fields.Many2many(
        'vf.member',
        'vf_document_linked_member_rel',
        'document_id',
        'member_id',
        string='Related Members'
    )
    group_ids = fields.Many2many(
        'vf.group',
        'vf_document_linked_group_rel',
        'document_id',
        'group_id',
        string='Related Groups'
    )
    section_ids = fields.Many2many(
        'vf.section',
        'vf_document_linked_section_rel',
        'document_id',
        'section_id',
        string='Related Sections'
    )
    
    # Template
    is_template = fields.Boolean(
        string='Is Template',
        tracking=True
    )
    template_document_ids = fields.One2many(
        'vf.document',
        'template_id',
        string='Documents from Template'
    )
    template_id = fields.Many2one(
        'vf.document',
        string='Created from Template',
        ondelete='set null',
        domain="[('is_template', '=', True)]"
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    file_size = fields.Integer(
        compute='_compute_file_size',
        string='File Size'
    )
    file_type = fields.Char(
        compute='_compute_file_type',
        string='File Type'
    )
    
    _sql_constraints = [
        ('check_visibility_custom', 
         'CHECK(visibility != \'custom\' OR '
         '(allowed_member_ids IS NOT NULL OR allowed_group_ids IS NOT NULL OR '
         'allowed_section_ids IS NOT NULL OR allowed_role_ids IS NOT NULL))', 
         'Custom visibility requires at least one allowed entity!'),
    ]

    @api.depends('name', 'category_id', 'current_version')
    def _compute_display_name(self):
        for document in self:
            parts = [document.name]
            if document.category_id:
                parts.append(f'[{document.category_id.name}]')
            if document.current_version > 1:
                parts.append(f'v{document.current_version}')
            document.display_name = ' '.join(parts)

    @api.depends('attachment_id.file_size')
    def _compute_file_size(self):
        for document in self:
            document.file_size = document.attachment_id.file_size

    @api.depends('attachment_id.mimetype')
    def _compute_file_type(self):
        for document in self:
            if document.attachment_id.mimetype:
                document.file_type = document.attachment_id.mimetype.split('/')[-1].upper()
            else:
                document.file_type = ''

    @api.model
    def create(self, vals):
        # Set default visibility from category if not specified
        if 'category_id' in vals and not vals.get('visibility'):
            category = self.env['vf.document.category'].browse(vals['category_id'])
            vals['visibility'] = category.default_visibility
        
        document = super().create(vals)
        
        # Create initial version if attachment provided
        if vals.get('attachment_id'):
            document._create_version(vals['attachment_id'], 'Initial version')
        
        return document

    def write(self, vals):
        # Create new version if attachment changed
        for document in self:
            if 'attachment_id' in vals and vals['attachment_id'] != document.attachment_id.id:
                if vals['attachment_id']:
                    document._create_version(vals['attachment_id'], 'Updated version')
        
        return super().write(vals)

    def _create_version(self, attachment_id, changelog):
        """Create a new document version"""
        self.ensure_one()
        
        self.env['vf.document.version'].create({
            'document_id': self.id,
            'attachment_id': attachment_id,
            'version': self.current_version,
            'changelog': changelog,
        })
        
        self.current_version += 1

    def action_publish(self):
        """Publish the document"""
        self.write({'state': 'published'})
        return True

    def action_archive(self):
        """Archive the document"""
        self.write({'state': 'archived'})
        return True

    def action_set_to_draft(self):
        """Reset document to draft"""
        self.write({'state': 'draft'})
        return True

    def action_create_from_template(self):
        """Create a new document from this template"""
        self.ensure_one()
        if not self.is_template:
            raise ValidationError(_('Only templates can be used to create new documents'))
        
        return {
            'name': _('Create Document from Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.document',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_template_id': self.id,
                'default_name': _('New: %s') % self.name,
                'default_category_id': self.category_id.id,
                'default_visibility': self.visibility,
            },
        }

    def action_view_versions(self):
        """View document versions"""
        self.ensure_one()
        return {
            'name': _('Document Versions'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.document.version',
            'view_mode': 'tree,form',
            'domain': [('document_id', '=', self.id)],
            'context': {'default_document_id': self.id},
        }

    def check_access(self, partner):
        """Check if partner can access this document"""
        if self.visibility == 'public':
            return True
        
        if not partner.member_id and not partner.has_active_mandates:
            return False
        
        if self.visibility == 'members':
            return partner.member_id is not None or partner.has_active_mandates
        
        if self.visibility == 'leadership':
            return partner.is_leader or partner.is_manager
        
        if self.visibility == 'custom':
            # Check if partner is in allowed lists
            if partner.member_id and partner.member_id in self.allowed_member_ids:
                return True
            
            # Check group membership
            for group in self.allowed_group_ids:
                if partner in group.member_ids.mapped('partner_id'):
                    return True
            
            # Check section membership
            for section in self.allowed_section_ids:
                if partner in section.group_ids.mapped('member_ids').mapped('partner_id'):
                    return True
            
            # Check roles
            if partner.has_active_mandates:
                mandates = self.env['vf.mandate'].search([
                    ('person_id', '=', partner.id),
                    ('status', '=', 'active'),
                    ('position_id.role_id', 'in', self.allowed_role_ids.ids)
                ])
                if mandates:
                    return True
        
        return False
