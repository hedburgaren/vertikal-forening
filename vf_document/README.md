# VF Document - Document Management

## Overview

VF Document provides document management with version control, granular visibility, and linking capabilities to any association record.

## Features

### Document Storage
- Upload and store documents
- Multiple file formats supported
- Document categorization
- Metadata management

### Version Control
- Document versioning
- Approval workflows
- Change tracking
- Version comparison

### Visibility Control
- Individual access
- Group-level sharing
- Section-wide visibility
- Public documents

### Document Linking
- Link to members, groups, activities
- Bulk document operations
- Document relationships
- Cross-reference tracking

## Installation

Requires VF Base, VF Member, VF Group, and VF Role to be installed first.

## Configuration

1. Set up document categories
2. Configure visibility rules
3. Define approval workflows
4. Set up storage locations

## Data Models

- `vf.document` - Main document record
- `vf.document.version` - Version tracking
- `vf.document.access` - Access control

## Key Features

- Archive instead of delete
- Full audit trail
- GDPR compliant
- Integration with all VF modules

## Dependencies

- vf_base
- vf_member
- vf_group
- vf_role
- documents

## License

AGPL-3.0
