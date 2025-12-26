# Vertical Association (Odoo 18 CE)

**Vertical Association** is a complete, open and long-term sustainable association management solution for **Odoo 18 Community Edition**.

The project is built on top of **OCA vertical-association** and extended to support the operational needs of modern associations, clubs and non-profit organizations.

The focus is not on sales or CRM pipelines, but on:
- people
- relationships
- responsibility
- continuity
- safety

This repository aims to provide a shared, open foundation for association management within the Odoo ecosystem.

---

## Purpose

Associations often rely on fragmented tools, personal email accounts and undocumented processes.  
Vertical Association exists to replace that with a structured, role-based and transparent system that can be maintained over time - even when people change.

The system is designed to be:
- safe for children and families
- resilient to board and role changes
- compliant with data protection regulations
- understandable for non-technical users

---

## Target Organizations

- Sports clubs
- Youth organizations
- Cultural associations
- Non-profit organizations
- Membership-based communities

Primarily aimed at Sweden and the Nordics, but will hopefully be internationally usable.

---

## Core Capabilities (When Complete)

### Members & Families
- Members can be adults or minors
- Mandatory guardian relationships for minors
- Voluntary emergency and contact relationships
- Family support (siblings, households, guardians)
- Members can belong to multiple groups simultaneously

### Groups & Sections
- Groups (teams, committees, working groups)
- Sections as a higher-level organizational layer
- Members can hold multiple roles across groups and sections
- Clear separation between membership and responsibility

### Roles, Mandates & Access
- Role-based access control
- Time-limited mandates with reminders and grace periods
- Automatic continuity protection to prevent loss of access
- Access always scoped to group, section or organization level

### Communication
- Role- and group-based messaging
- No dependency on personal email addresses
- Frontend contact forms targeting roles or groups
- Full message history retained even when roles change

### Documents & Sharing
- Built on OCA Document Management System (DMS)
- Documents can be linked to:
  - members
  - groups
  - sections
  - events
- Visibility levels:
  - individual
  - group
  - section
  - public (frontend)
- Versioning and access control

### Templates
- Pre-built document and e-mail templates
  - document templates (PDF, reports, confirmations)
  - email templates (notifications, reminders, confirmations)
  - communication layouts
  - export formats

- Templates are:
  - neutral and reusable
  - fully translatable
  - designed to be customized per association
  - independent from business-specific branding

### Activities & Events
- Trainings, courses, camps, competitions
- Individual and group participation
- Attendance tracking
- Guardian-reported absence
- Support for complex participation scenarios

### Attendance & Reporting
- Digital attendance lists
- Aggregated reports for treasurers
- Exportable PDF and XLS reports
- Designed to support activity-based funding models

### Membership & Fees
- Membership periods and history
- Split payments (monthly, quarterly, semi-annual, annual)
- Price tiers and role-based reductions
- Integration with Odoo payment methods

### Economy Support
- Treasurer-focused reports
- Filterable member and payment views
- Export-only access (no raw data dumps)

### Sponsorship & Sales
- Sponsorship packages with validity periods
- Targeted communication to sponsors
- Optional merchandise and association sales
- Donations and sponsorship handled separately from membership

### Member & Guardian Portal
- Self-service frontend portal
- Schedule and event registration
- Document access
- Contact and consent management
- Reduced administrative workload

---

## Design Principles

- Built for Odoo 18 Community Edition only
- OCA-compatible architecture and standards
- Modular design — no monoliths
- Role-based access everywhere
- Security and privacy by default
- Archiving instead of deletion
- Long-term maintainability over short-term shortcuts

---

## Attribution

This project builds on the work of the **Odoo Community Association (OCA)** and the `vertical-association` project.

Further development and coordination have been contributed by **ARC Gruppen AB** and Chrille Hedberg, as part of an effort to strengthen association support within the Odoo ecosystem.

---

## License

AGPL-3.0  
See `LICENSE` for details.
