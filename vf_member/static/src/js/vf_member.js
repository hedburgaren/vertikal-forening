odoo.define('vf_member.member', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    
    publicWidget.registry.MemberProfile = publicWidget.Widget.extend({
        selector: '.vf_member_profile',
        init: function () {
            this._super.apply(this, arguments);
            this.memberData = null;
        },
        
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self.loadMemberProfile();
            });
        },
        
        loadMemberProfile: function () {
            var self = this;
            ajax.jsonRpc('/member/profile', 'call', {}).then(function (data) {
                if (data.error) {
                    self.$el.html('<div class="alert alert-warning">' + data.error + '</div>');
                } else {
                    self.memberData = data;
                    self.renderProfile();
                }
            });
        },
        
        renderProfile: function () {
            var $content = $(QWeb.render('vf_member.profile', {
                member: this.memberData.member,
                partner: this.memberData.partner,
            }));
            this.$el.html($content);
        },
    });
    
    publicWidget.registry.MemberGuardians = publicWidget.Widget.extend({
        selector: '.vf_member_guardians',
        
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self.memberId = self.$el.data('member-id');
                self.loadGuardians();
            });
        },
        
        loadGuardians: function () {
            var self = this;
            ajax.jsonRpc('/member/guardians/' + this.memberId, 'call', {}).then(function (data) {
                var $content = $(QWeb.render('vf_member.guardians', {
                    guardians: data.guardians,
                }));
                self.$el.html($content);
            });
        },
    });
    
    publicWidget.registry.MemberHousehold = publicWidget.Widget.extend({
        selector: '.vf_member_household',
        
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self.memberId = self.$el.data('member-id');
                self.loadHousehold();
            });
        },
        
        loadHousehold: function () {
            var self = this;
            ajax.jsonRpc('/member/household/' + this.memberId, 'call', {}).then(function (data) {
                var $content = $(QWeb.render('vf_member.household', {
                    household: data.household,
                    members: data.members,
                }));
                self.$el.html($content);
            });
        },
    });
});
