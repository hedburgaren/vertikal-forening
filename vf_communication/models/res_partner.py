# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Communication relationships
    sent_message_ids = fields.One2many(
        'vf.message',
        'sender_id',
        string='Sent Messages'
    )
    received_message_ids = fields.Many2many(
        'vf.message',
        compute='_compute_received_messages',
        string='Received Messages'
    )
    contact_form_ids = fields.One2many(
        'vf.contact.form',
        compute='_compute_contact_forms',
        string='Contact Forms'
    )
    
    # Mailbox access
    mailbox_ids = fields.Many2many(
        'vf.mailbox',
        compute='_compute_mailbox_access',
        string='Accessible Mailboxes'
    )
    
    # Statistics
    message_count = fields.Integer(
        compute='_compute_message_count',
        string='Message Count'
    )
    unread_message_count = fields.Integer(
        compute='_compute_unread_message_count',
        string='Unread Messages'
    )

    def _compute_received_messages(self):
        """Compute messages received by this partner"""
        for partner in self:
            # This is a simplified computation - in practice, you'd need
            # to track message reads more carefully
            partner.received_message_ids = self.env['vf.message'].search([
                '|', ('recipient_ids', 'in', partner.id),
                ('recipient_group_ids.member_ids.partner_id', 'in', partner.id),
                ('recipient_section_ids.group_ids.member_ids.partner_id', 'in', partner.id),
            ])

    def _compute_contact_forms(self):
        """Compute contact forms from this partner"""
        for partner in self:
            partner.contact_form_ids = self.env['vf.contact.form'].search([
                '|', ('sender_email', '=', partner.email),
                     ('partner_id', '=', partner.id)
            ])

    def _compute_mailbox_access(self):
        """Compute mailboxes this partner can access"""
        for partner in self:
            mailboxes = self.env['vf.mailbox']
            
            # Access based on active mandates
            mandates = self.env['vf.mandate'].search([
                ('person_id', '=', partner.id),
                ('status', '=', 'active')
            ])
            
            for mandate in mandates:
                if mandate.position_id.mailbox_id:
                    mailboxes |= mandate.position_id.mailbox_id
            
            # Access based on group leadership
            groups = self.env['vf.group'].search([
                ('leader_id', '=', partner.id)
            ])
            for group in groups:
                mailboxes |= self.env['vf.mailbox'].search([
                    ('group_id', '=', group.id)
                ])
            
            # Access based on section management
            sections = self.env['vf.section'].search([
                ('manager_id', '=', partner.id)
            ])
            for section in sections:
                mailboxes |= self.env['vf.mailbox'].search([
                    ('section_id', '=', section.id)
                ])
            
            partner.mailbox_ids = mailboxes

    def _compute_message_count(self):
        """Compute total messages sent/received"""
        for partner in self:
            sent = len(partner.sent_message_ids)
            received = len(partner.received_message_ids)
            partner.message_count = sent + received

    def _compute_unread_message_count(self):
        """Compute unread messages - simplified implementation"""
        for partner in self:
            # In practice, you'd track read status per recipient
            partner.unread_message_count = 0

    def action_compose_message(self):
        """Open message composer"""
        self.ensure_one()
        return {
            'name': _('Compose Message'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.message',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_sender_id': self.id},
        }

    def action_view_messages(self):
        """View all messages for this partner"""
        self.ensure_one()
        action = self.env.ref('vf_communication.vf_message_action').read()[0]
        action['domain'] = [
            '|', ('sender_id', '=', self.id),
                 ('recipient_ids', 'in', self.id)
        ]
        return action

    def action_view_mailboxes(self):
        """View accessible mailboxes"""
        self.ensure_one()
        action = self.env.ref('vf_communication.vf_mailbox_action').read()[0]
        action['domain'] = [('id', 'in', self.mailbox_ids.ids)]
        return action
