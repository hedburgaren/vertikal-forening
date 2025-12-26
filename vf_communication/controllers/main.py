# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from odoo import http, _
from odoo.http import request, JsonRequest
from odoo.exceptions import ValidationError


class VfCommunicationController(http.Controller):
    
    @http.route('/association/contact', type='http', auth='public', website=True)
    def contact_form(self, **kwargs):
        """Display contact form page"""
        mailboxes = request.env['vf.mailbox'].search([
            ('active', '=', True)
        ])
        
        return request.render('vf_communication.contact_form_page', {
            'mailboxes': mailboxes,
        })
    
    @http.route('/association/contact/submit', type='http', auth='public', methods=['POST'], website=True)
    def contact_form_submit(self, **post):
        """Process contact form submission"""
        try:
            # Create contact form record
            contact_form = request.env['vf.contact.form'].create({
                'subject': post.get('subject'),
                'message': post.get('message'),
                'sender_name': post.get('name'),
                'sender_email': post.get('email'),
                'sender_phone': post.get('phone'),
                'mailbox_id': int(post.get('mailbox_id')),
            })
            
            # Send confirmation email
            template = request.env.ref('vf_communication.email_template_contact_confirmation')
            if template:
                template.send_mail(contact_form.id)
            
            return request.render('vf_communication.contact_form_success', {
                'contact_form': contact_form,
            })
            
        except Exception as e:
            return request.render('vf_communication.contact_form_error', {
                'error': str(e),
            })
    
    @http.route('/association/mailbox/<string:code>', type='http', auth='public', website=True)
    def mailbox_view(self, code, **kwargs):
        """Display mailbox information page"""
        mailbox = request.env['vf.mailbox'].get_mailbox_by_email(code)
        
        if not mailbox:
            raise request.not_found()
        
        return request.render('vf_communication.mailbox_page', {
            'mailbox': mailbox,
        })
    
    @http.route('/association/api/messages', type='json', auth='user')
    def api_messages(self, **kwargs):
        """API endpoint for user messages"""
        partner = request.env.user.partner_id
        
        # Get messages
        messages = request.env['vf.message'].search([
            '|', ('sender_id', '=', partner.id),
                 ('recipient_ids', 'in', partner.id)
        ], limit=50, order='date desc')
        
        return {
            'messages': [{
                'id': msg.id,
                'subject': msg.subject,
                'date': msg.date,
                'state': msg.state,
                'sender': msg.sender_id.name,
                'recipient_count': msg.recipient_count,
            } for msg in messages]
        }
    
    @http.route('/association/api/mailboxes', type='json', auth='user')
    def api_mailboxes(self, **kwargs):
        """API endpoint for accessible mailboxes"""
        partner = request.env.user.partner_id
        mailboxes = partner.mailbox_ids
        
        return {
            'mailboxes': [{
                'id': mb.id,
                'name': mb.display_name,
                'email': mb.email,
                'code': mb.code,
                'current_holders': mb.current_holders,
            } for mb in mailboxes]
        }
    
    @http.route('/association/api/send_message', type='json', auth='user')
    def api_send_message(self, **kwargs):
        """API endpoint to send a message"""
        try:
            # Validate required fields
            if not kwargs.get('subject') or not kwargs.get('body'):
                raise ValidationError(_('Subject and message are required'))
            
            # Create message
            message = request.env['vf.message'].create({
                'subject': kwargs['subject'],
                'body': kwargs['body'],
                'sender_id': request.env.user.partner_id.id,
                'recipient_ids': kwargs.get('recipient_ids', []),
                'recipient_group_ids': kwargs.get('recipient_group_ids', []),
                'recipient_section_ids': kwargs.get('recipient_section_ids', []),
                'recipient_role_ids': kwargs.get('recipient_role_ids', []),
                'recipient_position_ids': kwargs.get('recipient_position_ids', []),
                'send_email': kwargs.get('send_email', False),
            })
            
            # Send message
            message.action_send()
            
            return {
                'success': True,
                'message_id': message.id,
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    @http.route('/association/api/contact_forms', type='json', auth='user')
    def api_contact_forms(self, **kwargs):
        """API endpoint for contact forms (for leaders/admins)"""
        if not request.env.user.has_group('vf_base.group_vf_leader'):
            return {'error': _('Access denied')}
        
        partner = request.env.user.partner_id
        contact_forms = request.env['vf.contact.form'].search([
            ('mailbox_id', 'in', partner.mailbox_ids.ids)
        ], limit=50, order='date desc')
        
        return {
            'contact_forms': [{
                'id': cf.id,
                'subject': cf.subject,
                'sender_name': cf.sender_name,
                'sender_email': cf.sender_email,
                'date': cf.date,
                'state': cf.state,
                'mailbox': cf.mailbox_id.display_name,
            } for cf in contact_forms]
        }
