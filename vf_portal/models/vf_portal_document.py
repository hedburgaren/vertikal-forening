# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class VfPortalDocument(models.Model):
    _name = 'vf.portal.document'
    _description = 'Portal Document Access'
    _inherit = ['vf.document']

    # Portal specific fields
    show_on_portal = fields.Boolean(
        string='Show on Portal',
        default=False,
        help='Make this document available on the member portal'
    )
    portal_access_level = fields.Selection([
        ('public', 'Public'),
        ('members', 'All Members'),
        ('active_members', 'Active Members Only'),
        ('leadership', 'Leadership Only'),
        ('custom', 'Custom'),
    ], string='Portal Access Level', default='members')
    
    # Download tracking
    download_count = fields.Integer(
        string='Download Count',
        default=0,
        readonly=True
    )
    last_downloaded = fields.Datetime(
        string='Last Downloaded',
        readonly=True
    )
    
    # Member access
    member_access_ids = fields.One2many(
        'vf.portal.document.access',
        'document_id',
        string='Member Access'
    )
    
    # Categories for portal
    portal_category_ids = fields.Many2many(
        'vf.portal.document.category',
        string='Portal Categories',
        help='Categories for organizing documents on the portal'
    )

    @api.model
    def get_portal_documents(self, member_id):
        """Get documents available to member on portal"""
        member = self.env['vf.member'].browse(member_id)
        
        domain = [
            ('show_on_portal', '=', True),
            ('state', '=', 'published'),
        ]
        
        documents = self.search(domain)
        
        # Filter by access level
        allowed_docs = self.env['vf.document']
        
        for doc in documents:
            if doc.portal_access_level == 'public':
                allowed_docs |= doc
            elif doc.portal_access_level == 'members' and member:
                allowed_docs |= doc
            elif doc.portal_access_level == 'active_members' and member and member.status == 'active':
                allowed_docs |= doc
            elif doc.portal_access_level == 'leadership' and member:
                # Check if member has leadership role
                if member.mandate_ids.filtered(lambda m: m.position_id.is_leadership and m.state == 'active'):
                    allowed_docs |= doc
            elif doc.portal_access_level == 'custom':
                # Check custom access rules
                if doc._check_custom_access(member):
                    allowed_docs |= doc
        
        return allowed_docs

    def _check_custom_access(self, member):
        """Check if member has custom access to this document"""
        if not member:
            return False
        
        # Check explicit access
        access = self.env['vf.portal.document.access'].search([
            ('document_id', '=', self.id),
            ('member_id', '=', member.id),
            ('access_granted', '=', True)
        ])
        if access:
            return True
        
        # Check section access
        if self.section_ids:
            member_sections = member.group_membership_ids.mapped('group_id.section_id')
            if any(section in member_sections for section in self.section_ids):
                return True
        
        # Check group access
        if self.group_ids:
            member_groups = member.group_membership_ids.mapped('group_id')
            if any(group in member_groups for group in self.group_ids):
                return True
        
        # Check role access
        if self.role_ids:
            member_roles = member.mandate_ids.filtered(lambda m: m.state == 'active').mapped('position_id')
            if any(role in member_roles for role in self.role_ids):
                return True
        
        return False

    def action_download_via_portal(self, member_id):
        """Download document via portal"""
        self.ensure_one()
        
        # Check access
        documents = self.get_portal_documents(member_id)
        if self not in documents:
            raise UserError(_('You do not have access to this document.'))
        
        # Update download tracking
        self.write({
            'download_count': self.download_count + 1,
            'last_downloaded': fields.Datetime.now(),
        })
        
        # Create access log
        self.env['vf.portal.document.log'].create({
            'document_id': self.id,
            'member_id': member_id,
            'action': 'download',
            'date': fields.Datetime.now(),
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.attachment_id.id}?download=true',
            'target': 'self',
        }

    def action_view_via_portal(self, member_id):
        """View document via portal"""
        self.ensure_one()
        
        # Check access
        documents = self.get_portal_documents(member_id)
        if self not in documents:
            raise UserError(_('You do not have access to this document.'))
        
        # Create access log
        self.env['vf.portal.document.log'].create({
            'document_id': self.id,
            'member_id': member_id,
            'action': 'view',
            'date': fields.Datetime.now(),
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Document',
            'res_model': 'ir.attachment',
            'res_id': self.attachment_id.id,
            'view_mode': 'form',
            'target': 'new',
        }


class VfPortalDocumentAccess(models.Model):
    _name = 'vf.portal.document.access'
    _description = 'Portal Document Access'
    _order = 'member_id, document_id'

    document_id = fields.Many2one(
        'vf.document',
        string='Document',
        required=True,
        ondelete='cascade'
    )
    member_id = fields.Many2one(
        'vf.member',
        string='Member',
        required=True,
        ondelete='cascade'
    )
    access_granted = fields.Boolean(
        string='Access Granted',
        default=True
    )
    granted_by = fields.Many2one(
        'res.users',
        string='Granted By',
        default=lambda self: self.env.user
    )
    date_granted = fields.Datetime(
        string='Date Granted',
        default=fields.Datetime.now
    )
    expires_on = fields.Date(
        string='Expires On'
    )
    notes = fields.Text(
        string='Notes'
    )
    
    _sql_constraints = [
        ('unique_document_member', 'unique(document_id, member_id)', 
         'Access record already exists for this document and member!'),
    ]


class VfPortalDocumentCategory(models.Model):
    _name = 'vf.portal.document.category'
    _description = 'Portal Document Category'
    _order = 'sequence, name'

    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    description = fields.Text(
        string='Description',
        translate=True
    )
    parent_id = fields.Many2one(
        'vf.portal.document.category',
        string='Parent Category'
    )
    child_ids = fields.One2many(
        'vf.portal.document.category',
        'parent_id',
        string='Child Categories'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    document_count = fields.Integer(
        compute='_compute_document_count',
        string='Documents'
    )

    @api.depends('name')
    def _compute_document_count(self):
        for category in self:
            category.document_count = self.env['vf.document'].search_count([
                ('portal_category_ids', 'in', [category.id]),
                ('show_on_portal', '=', True),
                ('state', '=', 'published'),
            ])


class VfPortalDocumentLog(models.Model):
    _name = 'vf.portal.document.log'
    _description = 'Portal Document Access Log'
    _order = 'date desc'

    document_id = fields.Many2one(
        'vf.document',
        string='Document',
        required=True,
        ondelete='cascade'
    )
    member_id = fields.Many2one(
        'vf.member',
        string='Member',
        required=True,
        ondelete='cascade'
    )
    action = fields.Selection([
        ('view', 'Viewed'),
        ('download', 'Downloaded'),
    ], string='Action', required=True)
    date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now
    )
    ip_address = fields.Char(
        string='IP Address'
    )
