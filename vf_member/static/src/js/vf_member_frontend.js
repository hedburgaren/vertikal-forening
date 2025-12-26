odoo.define('vf_member.frontend', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var ajax = require('web.ajax');
    
    var _t = core._t;
    
    // Member Dashboard Widget
    publicWidget.registry.MemberDashboard = publicWidget.Widget.extend({
        selector: '.vf_member_dashboard',
        
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self.loadDashboard();
            });
        },
        
        loadDashboard: function () {
            var self = this;
            ajax.jsonRpc('/member/profile', 'call', {}).then(function (data) {
                if (data.error) {
                    self.$('.dashboard-content').html(
                        '<div class="alert alert-warning">' + data.error + '</div>'
                    );
                } else {
                    self.renderDashboard(data);
                }
            });
        },
        
        renderDashboard: function (data) {
            var $content = $(QWeb.render('vf_member.dashboard', {
                member: data.member,
                partner: data.partner,
            }));
            this.$('.dashboard-content').html($content);
        },
    });
    
    // Emergency Contact Widget
    publicWidget.registry.EmergencyContact = publicWidget.Widget.extend({
        selector: '.vf_emergency_contact',
        
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self.memberId = self.$el.data('member-id');
                self.loadEmergencyContacts();
            });
        },
        
        loadEmergencyContacts: function () {
            var self = this;
            ajax.jsonRpc('/member/guardians/' + this.memberId, 'call', {}).then(function (data) {
                var emergencyContacts = data.guardians.filter(function(g) {
                    return g.is_emergency;
                });
                
                var $content = $(QWeb.render('vf_member.emergency_contacts', {
                    contacts: emergencyContacts,
                }));
                self.$el.html($content);
            });
        },
    });
});
