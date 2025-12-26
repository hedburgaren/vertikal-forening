odoo.define('vf_communication.frontend', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var rpc = require('web.rpc');
    
    var QWeb = core.qweb;
    var _t = core._t;

    publicWidget.registry.ContactForm = publicWidget.Widget.extend({
        selector: '.o_vf_contact_form',
        xmlDependencies: ['/vf_communication/static/src/xml/vf_communication.xml'],
        
        events: {
            'submit form': '_onSubmit',
            'change .o_vf_mailbox_select': '_onMailboxChange',
        },
        
        init: function () {
            this._super.apply(this, arguments);
            this.submitting = false;
        },
        
        _onMailboxChange: function (e) {
            var mailboxId = $(e.currentTarget).val();
            var $description = this.$('.o_vf_mailbox_description');
            
            if (mailboxId) {
                rpc.query({
                    model: 'vf.mailbox',
                    method: 'read',
                    args: [parseInt(mailboxId), ['display_name', 'current_holders']],
                }).then(function (mailbox) {
                    if (mailbox.length > 0) {
                        $description.html(
                            '<strong>' + mailbox[0].display_name + '</strong><br/>' +
                            'Current holders: ' + mailbox[0].current_holders
                        );
                    }
                });
            } else {
                $description.empty();
            }
        },
        
        _onSubmit: function (e) {
            e.preventDefault();
            
            if (this.submitting) {
                return;
            }
            
            var self = this;
            var $form = this.$('form');
            var data = {
                subject: this.$('input[name="subject"]').val(),
                message: this.$('textarea[name="message"]').val(),
                name: this.$('input[name="name"]').val(),
                email: this.$('input[name="email"]').val(),
                phone: this.$('input[name="phone"]').val(),
                mailbox_id: this.$('select[name="mailbox_id"]').val(),
            };
            
            // Basic validation
            if (!data.subject || !data.message || !data.name || !data.email || !data.mailbox_id) {
                this.$('.o_vf_error').text(_t('Please fill in all required fields')).show();
                return;
            }
            
            this.submitting = true;
            this.$('.o_vf_submit').prop('disabled', true);
            
            rpc.query({
                route: '/association/contact/submit',
                params: data,
            }).then(function (result) {
                if (result.success !== false) {
                    self.$('.o_vf_form_container').hide();
                    self.$('.o_vf_success').show();
                } else {
                    self.$('.o_vf_error').text(result.error || _t('An error occurred')).show();
                    self.$('.o_vf_submit').prop('disabled', false);
                    self.submitting = false;
                }
            }).fail(function () {
                self.$('.o_vf_error').text(_t('Connection error. Please try again.')).show();
                self.$('.o_vf_submit').prop('disabled', false);
                self.submitting = false;
            });
        },
    });
    
    publicWidget.registry.MailboxInfo = publicWidget.Widget.extend({
        selector: '.o_vf_mailbox_info',
        
        init: function () {
            this._super.apply(this, arguments);
        },
        
        start: function () {
            var self = this;
            var code = this.$el.data('mailbox-code');
            
            if (code) {
                rpc.query({
                    route: '/association/api/mailboxes',
                    params: {code: code},
                }).then(function (result) {
                    if (result.mailboxes && result.mailboxes.length > 0) {
                        var mailbox = result.mailboxes[0];
                        self.$('.o_vf_mailbox_name').text(mailbox.name);
                        self.$('.o_vf_mailbox_email').text(mailbox.email);
                        self.$('.o_vf_mailbox_holders').text(mailbox.current_holders);
                    }
                });
            }
            
            return this._super();
        },
    });
    
    publicWidget.registry.MessageInbox = publicWidget.Widget.extend({
        selector: '.o_vf_message_inbox',
        
        events: {
            'click .o_vf_refresh': '_onRefresh',
            'click .o_vf_message': '_onMessageClick',
        },
        
        init: function () {
            this._super.apply(this, arguments);
            this.loading = false;
        },
        
        start: function () {
            this._loadMessages();
            return this._super();
        },
        
        _onRefresh: function () {
            this._loadMessages();
        },
        
        _onMessageClick: function (e) {
            var messageId = $(e.currentTarget).data('message-id');
            this.$('.o_vf_message').removeClass('active');
            $(e.currentTarget).addClass('active');
            this._loadMessage(messageId);
        },
        
        _loadMessages: function () {
            var self = this;
            
            if (this.loading) {
                return;
            }
            
            this.loading = true;
            this.$('.o_vf_refresh').addClass('fa-spin');
            
            rpc.query({
                route: '/association/api/messages',
            }).then(function (result) {
                self.$('.o_vf_message_list').html(
                    QWeb.render('vf_communication.message_list', {messages: result.messages})
                );
                self.loading = false;
                self.$('.o_vf_refresh').removeClass('fa-spin');
                
                // Load first message if any
                if (result.messages.length > 0) {
                    self._loadMessage(result.messages[0].id);
                }
            });
        },
        
        _loadMessage: function (messageId) {
            var self = this;
            
            rpc.query({
                model: 'vf.message',
                method: 'read',
                args: [messageId, ['subject', 'body', 'date', 'sender_id']],
            }).then(function (messages) {
                if (messages.length > 0) {
                    self.$('.o_vf_message_content').html(
                        QWeb.render('vf_communication.message_detail', {message: messages[0]})
                    );
                }
            });
        },
    });
    
    return {
        ContactForm: publicWidget.registry.ContactForm,
        MailboxInfo: publicWidget.registry.MailboxInfo,
        MessageInbox: publicWidget.registry.MessageInbox,
    };
});
