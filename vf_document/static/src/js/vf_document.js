odoo.define('vf_document.document_manager', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var rpc = require('web.rpc');
    
    var QWeb = core.qweb;
    var _t = core._t;

    var DocumentManager = Widget.extend({
        template: 'vf_document.document_manager',
        
        events: {
            'click .o_vf_upload': '_onUpload',
            'click .o_vf_download': '_onDownload',
            'click .o_vf_create_version': '_onCreateVersion',
            'change .o_vf_file_input': '_onFileSelect',
        },
        
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.options = options || {};
            this.document = options.document || {};
        },
        
        start: function () {
            this._renderDocument();
            return this._super();
        },
        
        _renderDocument: function () {
            var $content = this.$('.o_vf_document_content');
            $content.html(QWeb.render('vf_document.document_info', {
                document: this.document
            }));
        },
        
        _onUpload: function () {
            this.$('.o_vf_file_input').click();
        },
        
        _onFileSelect: function (e) {
            var self = this;
            var file = e.target.files[0];
            
            if (!file) {
                return;
            }
            
            var reader = new FileReader();
            reader.onload = function (e) {
                self._uploadFile(file, e.target.result);
            };
            reader.readAsDataURL(file);
        },
        
        _uploadFile: function (file, data) {
            var self = this;
            
            this.$('.o_vf_upload').prop('disabled', true);
            
            rpc.query({
                model: 'ir.attachment',
                method: 'create',
                args: [{
                    name: file.name,
                    datas: data.split(',')[1],
                    res_model: 'vf.document',
                    res_field: 'attachment_id',
                    res_id: this.document.id,
                }]
            }).then(function (attachment_id) {
                return rpc.query({
                    model: 'vf.document',
                    method: 'write',
                    args: [[self.document.id], {
                        attachment_id: attachment_id,
                    }]
                });
            }).then(function () {
                self.do_notify(_t('Success'), _t('Document uploaded successfully'));
                self.trigger_up('reload');
            }).fail(function () {
                self.do_warn(_t('Error'), _t('Failed to upload document'));
            }).always(function () {
                self.$('.o_vf_upload').prop('disabled', false);
            });
        },
        
        _onDownload: function () {
            if (this.document.attachment_id) {
                window.open('/web/content/' + this.document.attachment_id + '?download=true');
            }
        },
        
        _onCreateVersion: function () {
            var self = this;
            
            this.$('.o_vf_file_input').click();
            
            // Override upload handler for version creation
            this.$('.o_vf_file_input').off('change').on('change', function (e) {
                var file = e.target.files[0];
                
                if (!file) {
                    return;
                }
                
                var reader = new FileReader();
                reader.onload = function (e) {
                    self._createVersion(file, e.target.result);
                };
                reader.readAsDataURL(file);
            });
        },
        
        _createVersion: function (file, data) {
            var self = this;
            
            rpc.query({
                model: 'ir.attachment',
                method: 'create',
                args: [{
                    name: file.name,
                    datas: data.split(',')[1],
                    res_model: 'vf.document',
                    res_field: 'attachment_id',
                    res_id: this.document.id,
                }]
            }).then(function (attachment_id) {
                return rpc.query({
                    model: 'vf.document.version',
                    method: 'create',
                    args: [{
                        document_id: self.document.id,
                        attachment_id: attachment_id,
                        version: self.document.current_version,
                        changelog: 'New version uploaded via web interface',
                    }]
                });
            }).then(function () {
                self.do_notify(_t('Success'), _t('New version created successfully'));
                self.trigger_up('reload');
            }).fail(function () {
                self.do_warn(_t('Error'), _t('Failed to create new version'));
            });
        },
    });

    return {
        DocumentManager: DocumentManager,
    };
});
