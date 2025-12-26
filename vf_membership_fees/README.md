# VF Membership Fees - Fee Management

## Overview

VF Membership Fees provides comprehensive fee management including membership periods, split payments, price tiers, and payment tracking.

## Features

### Fee Categories
- Define fee types and categories
- Period-based fee structure
- Automatic fee generation
- Fee history tracking

### Payment Plans
- Monthly, quarterly, semi-annual, annual
- Split payment support
- Payment reminders
- Late fee management

### Price Tiers
- Role-based pricing
- Age-based discounts
- Family discounts
- Group-specific rates

### Payment Tracking
- Payment history
- Outstanding balances
- Payment reminders
- Financial reporting

## Installation

Requires VF Base, VF Member, VF Group, and VF Role to be installed first.

## Configuration

1. Set up fee categories
2. Define payment schedules
3. Configure price tiers
4. Set up reminder templates

## Data Models

- `vf.fee.category` - Fee categorization
- `vf.fee` - Individual fee records
- `vf.fee.payment` - Payment tracking
- `vf.fee.waiver` - Fee waivers

## Key Features

- Automated fee generation
- Flexible payment schedules
- Comprehensive reporting
- Integration with accounting

## Dependencies

- vf_base
- vf_member
- vf_group
- vf_role
- account

## License

AGPL-3.0
