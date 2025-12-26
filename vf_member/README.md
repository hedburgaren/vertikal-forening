# VF Member - Member Management

## Overview

VF Member provides comprehensive member management for associations, including registration, guardians, families, and multi-group membership.

## Features

### Member Registration
- Automatic membership number generation
- Age-based classification (child, youth, adult, senior)
- Member status management (active, inactive, honorary)
- Membership periods with history tracking

### Guardian Relationships
- Mandatory guardians for minor members
- Emergency contacts
- Family support relationships
- Multiple guardians per member

### Family Management
- Household grouping
- Sibling relationships
- Family-based discounts and communications
- Guardian permissions

### Multi-Group Membership
- Members can belong to multiple groups
- Different roles in different groups
- Group-specific membership fees
- Activity participation tracking

## Installation

Requires VF Base to be installed first.

## Configuration

1. Set up membership number sequence
2. Configure age classifications
3. Define membership periods
4. Set up default member types

## Data Models

- `vf.member` - Main member record
- `vf.member.relationship` - Family and guardian relationships
- `vf.member.group.membership` - Group membership tracking

## Key Features

- Automatic age updates based on birth date
- GDPR compliance with data retention
- Archive instead of delete for history
- Full audit trail of changes

## Dependencies

- vf_base
- base

## License

AGPL-3.0
