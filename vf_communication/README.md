# VF Communication - Messaging System

## Overview

VF Communication provides internal messaging with role-based targeting, email forwarding, and public contact forms for association communication.

## Features

### Internal Messaging
- Role-based message targeting
- Group and section filtering
- Message history retention
- Delivery tracking

### Email Integration
- Automatic email forwarding
- Message templates
- Attachment support
- Bounce handling

### Contact Forms
- Public-facing contact forms
- Role-based routing
- Spam protection
- Auto-responders

### Message Management
- Draft and send messages
- Message archiving
- Read receipts
- Bulk messaging

## Installation

Requires VF Base, VF Member, VF Group, and VF Role to be installed first.

## Configuration

1. Set up email servers
2. Configure message templates
3. Define routing rules
4. Set up contact forms

## Data Models

- `vf.message` - Internal messages
- `vf.message.recipient` - Message delivery tracking
- `vf.contact.form` - Public contact submissions

## Key Features

- No dependency on personal email
- Full message history
- Role-based permissions
- GDPR compliant

## Dependencies

- vf_base
- vf_member
- vf_group
- vf_role
- mail

## License

AGPL-3.0
