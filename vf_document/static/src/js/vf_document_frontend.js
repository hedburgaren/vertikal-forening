odoo.define('vf_document.frontend', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var rpc = require('web.rpc');
    
    var QWeb = core.qweb;
    var _t = core._t;

    publicWidget.registry.DocumentLibrary = publicWidget.Widget.extend({
        selector: '.o_vf_document_library',
        xmlDependencies: ['/vf_document/static/src/xml/vf_document.xml'],
        
        events: {
            'click .o_vf_document_item': '_onDocumentClick',
            'click .o_vf_download': '_onDownload',
            'click .o_vf_search': '_onSearch',
            'change .o_vf_category_filter': '_onCategoryFilter',
            'change .o_vf_search_input': '_onSearchInput',
        },
        
        init: function () {
            this._super.apply(this, arguments);
            this.documents = [];
            this.filtered_documents = [];
            this.current_category = null;
            this.search_term = '';
        },
        
        start: function () {
            var self = this;
            this._loadDocuments().then(function () {
                self._renderDocuments();
            });
            return this._super();
        },
        
        _loadDocuments: function () {
            var self = this;
            
            return rpc.query({
                route: '/association/api/documents',
                params: {
                    public_only: true,
                },
            }).then(function (result) {
                self.documents = result.documents || [];
                self.filtered_documents = self.documents.slice();
            });
        },
        
        _onSearch: function (e) {
            e.preventDefault();
            this._filterDocuments();
        },
        
        _onSearchInput: function () {
            this.search_term = this.$('.o_vf_search_input').val().toLowerCase();
            this._filterDocuments();
        },
        
        _onCategoryFilter: function (e) {
            var categoryId = $(e.currentTarget).val();
            this.current_category = categoryId !== '' ? parseInt(categoryId) : null;
            this._filterDocuments();
        },
        
        _filterDocuments: function () {
            var self = this;
            
            this.filtered_documents = this.documents.filter(function (doc) {
                // Category filter
                if (self.current_category && doc.category_id[0] !== self.current_category) {
                    return false;
                }
                
                // Search filter
                if (self.search_term) {
                    var searchMatch = (
                        doc.name.toLowerCase().indexOf(self.search_term) !== -1 ||
                        (doc.description && doc.description.toLowerCase().indexOf(self.search_term) !== -1)
                    );
                    if (!searchMatch) {
                        return false;
                    }
                }
                
                return true;
            });
            
            this._renderDocuments();
        },
        
        _onDocumentClick: function (e) {
            e.preventDefault();
            var documentId = $(e.currentTarget).data('document-id');
            this._showDocumentDetails(documentId);
        },
        
        _onDownload: function (e) {
            e.stopPropagation();
            var attachmentId = $(e.currentTarget).data('attachment-id');
            if (attachmentId) {
                window.open('/web/content/' + attachmentId + '?download=true');
            }
        },
        
        _renderDocuments: function () {
            var self = this;
            var $container = this.$('.o_vf_document_list');
            
            if (this.filtered_documents.length === 0) {
                $container.html('<div class="alert alert-info">No documents found</div>');
                return;
            }
            
            $container.html(
                QWeb.render('vf_document.document_list', {
                    documents: this.filtered_documents,
                })
            );
        },
        
        _showDocumentDetails: function (documentId) {
            var self = this;
            var document = _.find(this.documents, {id: documentId});
            
            if (!document) {
                return;
            }
            
            var $modal = $(QWeb.render('vf_document.document_modal', {
                document: document,
            }));
            
            $('body').append($modal);
            $modal.modal('show');
            
            $modal.on('hidden.bs.modal', function () {
                $modal.remove();
            });
        },
    });
    
    publicWidget.registry.DocumentViewer = publicWidget.Widget.extend({
        selector: '.o_vf_document_viewer',
        xmlDependencies: ['/vf_document/static/src/xml/vf_document.xml'],
        
        events: {
            'click .o_vf_download': '_onDownload',
            'click .o_vf_share': '_onShare',
        },
        
        init: function () {
            this._super.apply(this, arguments);
            this.documentId = this.$el.data('document-id');
            this.document = null;
        },
        
        start: function () {
            var self = this;
            this._loadDocument().then(function () {
                self._renderDocument();
            });
            return this._super();
        },
        
        _loadDocument: function () {
            var self = this;
            
            return rpc.query({
                route: '/association/api/document/' + this.documentId,
            }).then(function (result) {
                self.document = result.document;
            });
        },
        
        _onDownload: function (e) {
            e.preventDefault();
            if (this.document && this.document.attachment_id) {
                window.open('/web/content/' + this.document.attachment_id + '?download=true');
            }
        },
        
        _onShare: function (e) {
            e.preventDefault();
            var url = window.location.href;
            
            if (navigator.share) {
                navigator.share({
                    title: this.document.name,
                    text: this.document.description,
                    url: url,
                });
            } else {
                // Fallback: copy to clipboard
                var $temp = $('<input>');
                $('body').append($temp);
                $temp.val(url).select();
                document.execCommand('copy');
                $temp.remove();
                
                this.do_notify(_t('Link copied'), _t('Document link copied to clipboard'));
            }
        },
        
        _renderDocument: function () {
            if (!this.document) {
                return;
            }
            
            this.$('.o_vf_document_title').text(this.document.name);
            this.$('.o_vf_document_description').html(this.document.description || '');
            this.$('.o_vf_document_date').text(this.document.date);
            this.$('.o_vf_document_category').text(this.document.category_id[1]);
            this.$('.o_vf_download').attr('data-attachment-id', this.document.attachment_id);
        },
    });
    
    return {
        DocumentLibrary: publicWidget.registry.DocumentLibrary,
        DocumentViewer: publicWidget.registry.DocumentViewer,
    };
});
