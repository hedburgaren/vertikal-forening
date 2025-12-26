odoo.define('vf_communication.messaging', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var rpc = require('web.rpc');
    
    var QWeb = core.qweb;
    var _t = core._t;

    var MessageComposer = Widget.extend({
        template: 'vf_communication.message_composer',
        
        events: {
            'click .o_vf_send': '_onSend',
            'click .o_vf_add_recipient': '_onAddRecipient',
            'change .o_vf_recipient_type': '_onRecipientTypeChange',
        },
        
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.options = options || {};
            this.message = {
                recipient_ids: [],
                recipient_group_ids: [],
                recipient_section_ids: [],
                recipient_role_ids: [],
                recipient_position_ids: [],
            };
        },
        
        start: function () {
            var self = this;
            this._loadData().then(function () {
                self._renderRecipients();
            });
            return this._super();
        },
        
        _loadData: function () {
            var self = this;
            return $.when(
                rpc.query({
                    model: 'res.partner',
                    method: 'search_read',
                    fields: ['id', 'name', 'email'],
                    domain: [['is_company', '=', false]],
                }),
                rpc.query({
                    model: 'vf.group',
                    method: 'search_read',
                    fields: ['id', 'name'],
                }),
                rpc.query({
                    model: 'vf.section',
                    method: 'search_read',
                    fields: ['id', 'name'],
                }),
                rpc.query({
                    model: 'vf.role',
                    method: 'search_read',
                    fields: ['id', 'name'],
                }),
                rpc.query({
                    model: 'vf.position',
                    method: 'search_read',
                    fields: ['id', 'display_name'],
                })
            ).then(function (partners, groups, sections, roles, positions) {
                self.partners = partners;
                self.groups = groups;
                self.sections = sections;
                self.roles = roles;
                self.positions = positions;
            });
        },
        
        _onRecipientTypeChange: function (e) {
            var type = $(e.currentTarget).val();
            this.$('.o_vf_recipient_select').hide();
            this.$('.o_vf_recipient_select.' + type).show();
        },
        
        _onAddRecipient: function (e) {
            e.preventDefault();
            var type = this.$('.o_vf_recipient_type').val();
            var select = this.$('.o_vf_recipient_select.' + type);
            var id = parseInt(select.val());
            
            if (!id) {
                return;
            }
            
            var field = 'recipient_' + type + '_ids';
            if (this.message[field].indexOf(id) === -1) {
                this.message[field].push(id);
                this._renderRecipients();
            }
        },
        
        _renderRecipients: function () {
            var self = this;
            var $container = this.$('.o_vf_recipients');
            $container.empty();
            
            ['partner', 'group', 'section', 'role', 'position'].forEach(function (type) {
                var field = 'recipient_' + type + '_ids';
                var data = self[type + 's'];
                var label = type.charAt(0).toUpperCase() + type.slice(1) + 's';
                
                self.message[field].forEach(function (id) {
                    var item = _.find(data, {id: id});
                    if (item) {
                        var $badge = $('<span class="badge badge-primary o_vf_recipient_badge"/>')
                            .text(item.name || item.display_name)
                            .append($('<a/>', {
                                href: '#',
                                text: '×',
                                click: function () {
                                    self._removeRecipient(field, id);
                                }
                            }));
                        $container.append($('<div/>').html(label + ': ').append($badge));
                    }
                });
            });
        },
        
        _removeRecipient: function (field, id) {
            var index = this.message[field].indexOf(id);
            if (index > -1) {
                this.message[field].splice(index, 1);
                this._renderRecipients();
            }
        },
        
        _onSend: function () {
            var self = this;
            var subject = this.$('.o_vf_subject').val();
            var body = this.$('.o_vf_body').val();
            
            if (!subject || !body) {
                this.do_warn(_t('Error'), _t('Subject and message are required'));
                return;
            }
            
            if (_.every(this.message, function (val) { return val.length === 0; })) {
                this.do_warn(_t('Error'), _t('At least one recipient must be specified'));
                return;
            }
            
            this.$('.o_vf_send').prop('disabled', true);
            
            rpc.query({
                route: '/association/api/send_message',
                params: _.extend({
                    subject: subject,
                    body: body,
                    send_email: this.$('.o_vf_send_email').prop('checked'),
                }, this.message)
            }).then(function (result) {
                if (result.success) {
                    self.do_notify(_t('Success'), _t('Message sent successfully'));
                    self.trigger_up('close_dialog');
                } else {
                    self.do_warn(_t('Error'), result.error);
                }
                self.$('.o_vf_send').prop('disabled', false);
            });
        },
    });

    return {
        MessageComposer: MessageComposer,
    };
});
