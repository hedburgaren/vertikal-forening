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
    
    # Featured status
    featured_document = fields.Boolean(
        string='Featured Document',
        default=False,
        help='Show this document prominently on the portal'
    )
    featured_until = fields.Date(
        string='Featured Until',
        help='Date until which this document should remain featured'
    )

    def action_download_via_portal(self, member_id):
        """Download document via portal with tracking"""
        self.ensure_one()
        
        # Check access
        if not self._check_portal_access(member_id):
            raise UserError(_('You do not have permission to access this document.'))
        
        # Update download stats
        self.write({
            'download_count': self.download_count + 1,
            'last_downloaded': fields.Datetime.now(),
        })
        
        # Log access
        self.env['vf.portal.document.access'].create({
            'document_id': self.id,
            'member_id': member_id,
            'access_date': fields.Datetime.now(),
            'access_type': 'download',
        })
        
        # Return download URL
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.attachment_id.id}?download=true',
            'target': 'new',
        }

    def _check_portal_access(self, member_id):
        """Check if member can access this document"""
        if not self.show_on_portal:
            return False
        
        if self.portal_access_level == 'public':
            return True
        
        member = self.env['vf.member'].browse(member_id)
        if not member.exists():
            return False
        
        if self.portal_access_level == 'members':
            return True
        
        if self.portal_access_level == 'active_members':
            return member.state == 'active'
        
        if self.portal_access_level == 'leadership':
            # Check if member has any leadership roles
            return bool(member.mandate_ids.filtered(
                lambda m: m.position_id.role_id.is_managerial
            ))
        
        if self.portal_access_level == 'custom':
            # Check custom access rules
            access = self.member_access_ids.filtered(
                lambda a: a.member_id.id == member_id
            )
            return access and access.allowed
        
        return False

    @api.model
    def get_portal_documents(self, member_id, category_id=None):
        """Get documents available on portal for member"""
        member = self.env['vf.member'].browse(member_id)
        
        domain = [('show_on_portal', '=', True)]
        
        # Filter by category if specified
        if category_id:
            domain.append(('portal_category_ids', '=', category_id))
        
        documents = self.search(domain)
        
        # Filter by access
        accessible_docs = []
        for doc in documents:
            if doc._check_portal_access(member_id):
                accessible_docs.append({
                    'id': doc.id,
                    'name': doc.name,
                    'description': doc.description,
                    'category': doc.category_id.name,
                    'date_uploaded': doc.create_date,
                    'file_size': doc.file_size,
                    'featured': doc.featured_document,
                })
        
        return accessible_docs

    @api.model
    def get_featured_documents(self, member_id, limit=5):
        """Get featured documents for member"""
        today = fields.Date.today()
        
        domain = [
            ('show_on_portal', '=', True),
            ('featured_document', '=', True),
        ]
        
        documents = self.search(domain, limit=limit)
        
        featured_docs = []
        for doc in documents:
            if doc._check_portal_access(member_id):
                if not doc.featured_until or doc.featured_until >= today:
                    featured_docs.append({
                        'id': doc.id,
                        'name': doc.name,
                        'description': doc.description,
                        'date_uploaded': doc.create_date,
                    })
        
        return featured_docs


class VfPortalDocumentAccess(models.Model):
    _name = 'vf.portal.document.access'
    _description = 'Portal Document Access Log'
    _order = 'access_date desc'

    document_id = fields.Many2one(
        'vf.portal.document',
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
    access_date = fields.Datetime(
        string='Access Date',
        required=True,
        default=fields.Datetime.now
    )
    access_type = fields.Selection([
        ('view', 'View'),
        ('download', 'Download'),
    ], string='Access Type', required=True)
    ip_address = fields.Char(
        string='IP Address'
    )


class VfPortalDocumentCategory(models.Model):
    _name = 'vf.portal.document.category'
    _description = 'Portal Document Category'
    _order = 'sequence, name'

    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True
    )
    description = fields.Text(
        string='Description',
        translate=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count'
    )

    @api.depends('name')
    def _compute_document_count(self):
        for category in self:
            category.document_count = self.env['vf.portal.document'].search_count([
                ('portal_category_ids', '=', category.id),
                ('show_on_portal', '=', True)
            ])
