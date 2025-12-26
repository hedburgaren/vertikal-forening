# VF Base - Core Security & Configuration

## Overview

VF Base provides the foundation for the Vertical Association module suite, implementing core security groups, access controls, and configuration settings.

## Features

### Security Groups
- **Association User** - Basic member access
- **Group Leader** - Group-level permissions
- **Section Leader** - Section-level permissions
- **Board Member** - Board-level access
- **Administrator** - Full system access
- **Treasurer** - Financial reporting access

### Configuration
- Association settings and preferences
- Default security policies
- Base data for other modules

## Installation

Install VF Base before any other VF modules as they depend on its security groups and configuration.

## Configuration

1. After installation, configure association settings in Settings > Association
2. Assign users to appropriate security groups
3. Set up default policies for data retention and privacy

## Dependencies

- Odoo 18 CE
- base

## Data Models

- `vf.association.settings` - Association-wide configuration
- Security groups defined in `security/security.xml`

## License

AGPL-3.0
