# LLM-INSTRUCTION.md — Vertikal Förening (Odoo 18 CE)

> **This document is the single source of truth for all code contributions.**
> Every LLM, AI coding assistant, or human developer contributing to this
> repository MUST read and follow these rules without exception.

**Project:** Vertikal Förening — Association Management for Odoo 18 CE
**License:** AGPL-3.0
**Author:** ARC Gruppen AB — info@arcgruppen.se — https://arcgruppen.se
**Architect:** Chrille Hedberg — info@chrille.nu — https://chrille.nu

---

## Table of Contents

1. [Mission](#1-mission)
2. [Hard Rules — Platform & API](#2-hard-rules--platform--api)
3. [Hard Rules — LLM Behavior](#3-hard-rules--llm-behavior)
4. [Architecture](#4-architecture)
5. [Module Structure](#5-module-structure)
6. [Domain Model](#6-domain-model)
7. [Security, Privacy & GDPR](#7-security-privacy--gdpr)
8. [Portal & Frontend](#8-portal--frontend)
9. [Communication Hub](#9-communication-hub)
10. [Economy, Payments & Sponsorship](#10-economy-payments--sponsorship)
11. [Onboarding & Configuration](#11-onboarding--configuration)
12. [Templates, Reports & Documents](#12-templates-reports--documents)
13. [Calendar & Scheduling](#13-calendar--scheduling)
14. [Dashboard](#14-dashboard)
15. [Internationalization](#15-internationalization)
16. [Testing](#16-testing)
17. [Documentation](#17-documentation)
18. [Open Questions](#18-open-questions)

---

## 1. Mission

Vertikal Förening is the definitive association management solution for Odoo 18 CE.
It replaces fragmented tools, personal email accounts, and undocumented processes
with a structured, role-based, transparent system that any association can use.

**The goal is simple:** Build the app that every association — regardless of type,
size, or focus — wished they had. Sports clubs, cultural societies, pensioners'
associations, scout groups, choirs, humanitarian organizations. All of them.

This is IdrottOnline — but actually good.

### Design Philosophy

- **One app, not thirteen.** Users install "Förening" and configure what they need.
- **The treasurer's best friend.** Who has paid, who hasn't, reminders, renewals,
  LOK-stöd reports, export — all in one place.
- **Safe for children.** Protected personal data, mandatory guardians for minors,
  medical information visible only to those who need it.
- **Resilient to change.** Board members come and go. The system survives.
- **Beautiful.** The portal and frontend must look professional. UX and UI matter.

---

## 2. Hard Rules — Platform & API

### 2.1 — Target Platform

- **ONLY Odoo 18 Community Edition**
- Code targeting Odoo 17 or earlier is **forbidden**
- Code requiring Odoo Enterprise is **forbidden**
- Follow OCA (Odoo Community Association) conventions

### 2.2 — Odoo 18 Breaking Changes

These APIs **DO NOT EXIST** in Odoo 18. Never use them.

| ❌ FORBIDDEN | ✅ CORRECT IN ODOO 18 |
|---|---|
| `name_get()` | Set `_rec_name` or write `_compute_display_name` |
| `"qweb": [...]` in `__manifest__.py` | Register QWeb via `"assets"` key |
| `<tree string="...">` in XML views | `<list string="...">` |
| `fields.Char(track_visibility=...)` | `fields.Char(tracking=True)` |
| `multi="..."` on fields | Removed — write separate compute methods |
| `@api.multi` | Removed since Odoo 13 |
| `@api.one` | Removed since Odoo 13 |
| `@api.returns` | Removed |
| `_columns` / `_defaults` | Use `fields.*` and `default=` |
| `osv.osv` / `osv.TransientModel` | `models.Model` / `models.TransientModel` |
| `openerp` in imports | `odoo` |
| `report_xlsx` (external OCA module) | Use built-in QWeb PDF reports or native XLS export |

### 2.3 — Frontend: OWL 2

- Odoo 18 uses **OWL 2**, not OWL 1
- Legacy widgets (`Widget`, `AbstractAction`) are removed
- All frontend components must be OWL 2 components
- Register via `web.assets_backend` / `web.assets_frontend` in `__manifest__.py`

### 2.4 — Manifest Rules

Every file listed in `__manifest__.py` under `data`, `demo`, or `assets`
**MUST physically exist** on disk. A missing file = installation crash.

Never list Python files under `data`. Controllers and models are loaded via
`__init__.py` imports.

Verify before every commit:
```bash
# Every file in manifest must exist
for f in $(grep -oP "'[^']+\.(xml|js|scss|css|csv)'" __manifest__.py); do
    [ ! -f "${f//\'/}" ] && echo "MISSING: $f"
done
```

---

## 3. Hard Rules — LLM Behavior

### 3.1 — Autonomous Execution

The LLM works **autonomously**. Functionality must be fully implemented.
Partial solutions, sketches, stubs, or MVP reasoning are not permitted.
A feature either works completely, or it does not exist.

### 3.2 — When to Interrupt

The LLM **MUST NOT** ask for:
- Naming decisions
- Minimum scope or MVP definitions
- Confirmation to continue
- Permission to implement what is described in this document

The LLM **MAY ONLY** interrupt the user for:
- Questions that directly affect functional correctness
- Legal or security-critical ambiguity
- Contradictions within this document

All other open questions MUST be:
- Written to `OPEN-QUESTIONS.md`
- Clearly described with context
- NOT block execution

### 3.3 — Code Quality

- Docstrings on all public methods
- No `# TODO` without a matching GitHub Issue reference
- No commented-out code
- No print statements (use `_logger`)
- `pre-commit` compliance: `ruff`, `pylint-odoo`, `eslint`

---

## 4. Architecture

### 4.1 — Module Consolidation

The previous 13 `vf_*` modules are consolidated into **three modules**:

| Module | Purpose | Heavy Dependencies |
|---|---|---|
| `vf_association` | Everything. Members, groups, roles, communication, documents, activities, fees, economy, dashboard. | `base`, `contacts`, `mail`, `account` |
| `vf_association_portal` | Member/guardian self-service portal, public pages, mobile-friendly attendance | `website`, `portal` |
| `vf_association_sponsorship` | Sponsor packages, sponsor communication, merchandise sales with customization | `sale_management`, `website_sale` |

**Why three, not one?**

A small scout group with 40 members should not be forced to install the entire
website stack or e-commerce module. Portal and sponsorship have heavy dependencies
that most associations don't need.

**Why three, not thirteen?**

A normal association admin should never need to know what `vf_attendance_reporting`
is. They install "Förening" and toggle features on/off in Settings.

### 4.2 — Feature Toggles

Under **Settings > Förening** (via `res.config.settings`):

| Toggle | Controls | Default |
|---|---|---|
| Dokument & mallar | Document management and template system | Off |
| Kommunikationshubb | Internal messaging, contact forms, whistleblower | Off |
| Avgifter & betalningar | Fee management, installments, price tiers | Off |
| Kassörfunktioner | Reports, payment views, export control, LOK-stöd | Off |
| Närvarorapportering | Detailed attendance with reports and subsidy data | Off |
| Aktiviteter & evenemang | Activity management with scheduling | On |
| Skyddade personuppgifter | Protected identity support with enhanced access control | Off |
| Tävlingsverksamhet | Competitions, matches, cups, results, standings | Off |
| Säsongshantering | Season-based grouping of teams, fees, and activities | Off |

Toggles control `ir.ui.menu` visibility and `ir.model.access` rules via
`implied_group` on `res.groups`.

---

## 5. Module Structure

```
vf_association/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── res_config_settings.py          # Feature toggles
│   ├── vf_association_config.py        # Singleton: association type, season config
│   │
│   ├── member/
│   │   ├── __init__.py
│   │   ├── vf_member.py                # Core member record
│   │   ├── vf_guardian_relationship.py # Guardian ↔ minor
│   │   ├── vf_family_relationship.py   # Sibling, spouse, other
│   │   ├── vf_household.py            # Address grouping (supports shared custody)
│   │   └── res_partner.py             # Extensions to res.partner
│   │
│   ├── group/
│   │   ├── __init__.py
│   │   ├── vf_section.py              # Top-level org structure
│   │   ├── vf_group.py                # Teams, committees, working groups
│   │   ├── vf_group_type.py           # Type classification
│   │   └── vf_group_membership.py     # Member ↔ group link
│   │
│   ├── role/
│   │   ├── __init__.py
│   │   ├── vf_role.py                 # Role definitions
│   │   ├── vf_position.py             # Concrete positions in groups/sections
│   │   ├── vf_mandate.py              # Time-bound person → position assignment
│   │   └── vf_mandate_extension.py    # Renewals and extensions
│   │
│   ├── communication/
│   │   ├── __init__.py
│   │   ├── vf_message.py              # Internal messaging
│   │   ├── vf_mailbox.py              # Role-based mailbox
│   │   ├── vf_contact_form.py         # Configurable contact forms
│   │   └── vf_whistleblower.py        # Anonymous reporting channel
│   │
│   ├── document/
│   │   ├── __init__.py
│   │   ├── vf_document.py             # Documents with visibility levels
│   │   ├── vf_document_version.py     # Version control
│   │   └── vf_document_category.py    # Categorization
│   │
│   ├── activity/
│   │   ├── __init__.py
│   │   ├── vf_activity_type.py        # Training, match, cup, camp, meeting...
│   │   ├── vf_activity.py             # The activity itself
│   │   ├── vf_activity_schedule.py    # Recurring schedule instances
│   │   ├── vf_activity_registration.py # Individual or group sign-up
│   │   ├── vf_activity_attendance.py  # Attendance records
│   │   ├── vf_competition.py          # Cup/league wrapper
│   │   ├── vf_resource.py             # Venues, equipment, facilities
│   │   └── vf_season.py               # Season periods
│   │
│   ├── fees/
│   │   ├── __init__.py
│   │   ├── vf_fee_category.py         # Fee types
│   │   ├── vf_fee.py                  # Fee definitions with price tiers
│   │   ├── vf_fee_price_tier.py       # Age-based, family, early-bird pricing
│   │   ├── vf_fee_payment.py          # Payments and installments
│   │   ├── vf_fee_period.py           # Membership periods
│   │   └── vf_fee_waiver.py           # Discounts and exemptions
│   │
│   ├── economy/
│   │   ├── __init__.py
│   │   ├── vf_economy_report.py       # Treasurer reports
│   │   ├── vf_payment_view.py         # Filterable payment views
│   │   ├── vf_export_access.py        # Controlled exports (no raw data dumps)
│   │   └── vf_subsidy_report.py       # LOK-stöd / activity subsidy reports
│   │
│   ├── template/
│   │   ├── __init__.py
│   │   ├── vf_document_template.py    # PDF, certificate, form templates
│   │   ├── vf_email_template.py       # Email templates
│   │   └── vf_communication_layout.py # Layout customization
│   │
│   └── dashboard/
│       ├── __init__.py
│       └── vf_dashboard.py            # Role-based KPI dashboard
│
├── wizard/
│   ├── __init__.py
│   ├── vf_onboarding_wizard.py        # Post-install configuration guide
│   ├── vf_payment_reminder_wizard.py  # Bulk payment reminders
│   └── vf_import_wizard.py            # CSV import with validation
│
├── security/
│   ├── security.xml                    # Groups, categories, record rules
│   └── ir.model.access.csv            # Model access rights
│
├── data/
│   ├── ir_module_category_data.xml    # Module category "Association"
│   ├── ir_sequence_data.xml           # Member number sequence
│   ├── ir_config_parameter.xml        # Default config parameters
│   ├── menu.xml                       # Menu structure
│   ├── role_data.xml                  # Default roles
│   ├── group_type_data.xml            # Default group types
│   ├── activity_type_data.xml         # Default activity types
│   ├── relationship_type_data.xml     # Guardian relationship types
│   ├── fee_category_data.xml          # Default fee categories
│   ├── document_category_data.xml     # Default document categories
│   ├── template_category_data.xml     # Default template categories
│   └── email_template_data.xml        # Default email templates
│
├── views/
│   ├── res_config_settings_views.xml  # Settings page
│   ├── member/                        # Member views (form, list, search)
│   ├── group/                         # Group/section views
│   ├── role/                          # Role/mandate views
│   ├── communication/                 # Message/mailbox views
│   ├── document/                      # Document views
│   ├── activity/                      # Activity/attendance views
│   ├── fees/                          # Fee/payment views
│   ├── economy/                       # Treasurer views
│   ├── template/                      # Template views
│   └── dashboard/                     # Dashboard views
│
├── report/
│   ├── report_templates.xml           # QWeb report definitions
│   ├── report_member_list.xml
│   ├── report_attendance.xml
│   ├── report_subsidy.xml             # LOK-stöd format
│   └── report_treasurer.xml
│
├── static/
│   ├── description/
│   │   └── icon.png
│   └── src/
│       ├── js/                        # OWL 2 components
│       ├── scss/
│       └── xml/                       # QWeb templates
│
├── demo/
│   ├── demo_members.xml
│   ├── demo_groups.xml
│   ├── demo_activities.xml
│   └── demo_fees.xml
│
├── tests/
│   ├── __init__.py
│   ├── test_member.py
│   ├── test_guardian.py
│   ├── test_group.py
│   ├── test_mandate.py
│   ├── test_activity.py
│   ├── test_fees.py
│   ├── test_security.py
│   └── test_protected_data.py
│
├── i18n/
│   └── sv.po                          # Swedish primary translation
│
└── README.md
```

---

## 6. Domain Model

### 6.1 — Member Management

#### vf.member
The core record. Represents a person's membership in the association.

- `partner_id` → res.partner (required, unique, `ondelete='restrict'`)
- `membership_number` — auto-generated via ir.sequence (defined in XML data, not code)
- `membership_date` — when they joined
- `status` — selection: active, inactive, suspended, archived
- `is_minor` — computed from birth date (< 18 years)
- `age` — computed, with proper `_search_age` using date arithmetic (NOT loop-based)
- `birth_date` — related to partner, `store=False`
- **Privacy fields:**
  - `is_protected` — boolean (sekretessmarkerad person)
  - `protection_level` — selection: standard, protected_identity, hidden_address
  - `protected_note` — text, `groups='vf_association.group_vf_admin'`
- **Medical/safety (visible to leaders + guardians of this member):**
  - `medical_note` — text (allergies, conditions, medications leaders must know)
  - `emergency_info` — text (emergency contact beyond guardians)
- **Sport/license:**
  - `license_number` — char (federation license, sports card)
  - `license_expiry` — date
- `season_ids` — many2many to vf.season (active seasons)
- `guardian_ids` — one2many to vf.guardian.relationship
- `family_relationship_ids` — one2many
- `household_ids` — **many2many** to vf.household (supports shared custody)
- `group_membership_ids` — one2many to vf.group.membership

SQL constraints: unique partner_id, unique membership_number.

**A member may simultaneously:**
- Be "just a member" with no group and no role
- Belong to one or more groups/teams
- Hold one or more positions (coach, board member, treasurer, section chair)
- Be registered for activities individually OR as part of a team
- Any combination of the above

#### vf.guardian.relationship
Links a minor to their guardian(s).

- `member_id` → vf.member (the minor, required)
- `guardian_id` → res.partner (the adult, required)
- `relationship_type_id` → vf.relationship.type
- `start_date`, `end_date`
- `is_active` — computed from dates
- `legal_custody` — boolean (has legal custody)
- `emergency_phone`, `emergency_email` — override contact for this specific guardian
- `receives_communication` — boolean, default True
  (BOTH separated parents receive messages by default)
- `is_payer` — boolean (responsible for this child's fees)
- `priority` — integer (primary contact = 1, secondary = 2, emergency = 3)

**Constraints:**
- A minor member (is_minor = True) MUST have at least one active guardian
- At least one guardian must have `legal_custody = True`
- At least one guardian must have `is_payer = True`
- Creating a minor member without a guardian must be blocked at model level

#### vf.household
Address grouping. Supports shared custody: a child belongs to multiple households.

- `name` — optional label ("Familjen Svensson")
- `address_id` → res.partner (the address record)
- `member_ids` — **many2many** to vf.member (via link table with `is_primary` flag)
- `is_active`

The many2many link table `vf_household_member_rel` includes:
- `household_id`, `member_id`, `is_primary` (boolean — folkbokföringsadress)

#### vf.family.relationship
Optional family connections between members.

- `member_id` → vf.member
- `related_member_id` → vf.member
- `relationship_type` — selection: sibling, parent_adult_child, spouse, other

### 6.2 — Groups & Sections

#### vf.section
Highest organizational level within the association.

- `name`, `description`
- `parent_id` → self (nested sections allowed)
- `manager_id` → res.partner (section chair)
- `is_active`

#### vf.group
Teams, committees, working groups, boards.

- `name`, `code`, `description`
- `section_id` → vf.section (optional)
- `group_type_id` → vf.group.type (team, committee, working_group, board, other)
- `parent_group_id` → self (for sub-groups/sub-teams)
- `max_members`, `min_age`, `max_age`
- `leader_id` → res.partner
- **Team-specific fields** (shown when `is_team = True`):
  - `is_team` — boolean
  - `sport_type` — char
  - `season_id` → vf.season
  - `age_group` — char ("P12", "F15", "Senior", "Veteran")
  - `jersey_color` — char
  - `home_venue` — char
- `is_active`

**Organization tree:** Members of a group can see other members in the same group.
An interactive tree view must be available showing hierarchy:
- Association → Sections → Groups → Members
- Board → Section chairs → Coaches → Team members
- Must be navigable with expand/collapse in both backend and portal

#### vf.group.type
Classification of groups.

- `name` — "Lag", "Kommitté", "Arbetsgrupp", "Styrelse"
- `is_team` — boolean (team-like groups get extra fields)
- `icon` — char (for display)

#### vf.group.membership
Links members to groups. Separate model from roles/mandates.

- `member_id` → vf.member
- `group_id` → vf.group
- `join_date`, `leave_date`
- `is_active` — computed from dates
- `note` — char

### 6.3 — Roles, Positions & Mandates

#### vf.role
Defines a role type with permission implications.

- `name` — "Ordförande", "Kassör", "Huvudtränare", "Lagledare", "Funktionär"
- `description`
- `access_level` — selection: organization, section, group
- `is_managerial` — can assign other roles
- `requires_approval` — needs board approval/vote
- `communication_level` — defines messaging reach (see §9)

#### vf.position
A concrete slot within a group or section.

- `name`
- `role_id` → vf.role
- `group_id` → vf.group (optional — position within a group)
- `section_id` → vf.section (optional — position within a section)
- `max_holders` — integer (how many can hold simultaneously, default 1)
- `is_critical` — boolean (system warns if position becomes vacant)
- `is_active`

#### vf.mandate
Time-bound assignment of a person to a position.

- `person_id` → res.partner (required)
- `position_id` → vf.position (required)
- `start_date`, `end_date` — both REQUIRED
- `status` — selection: pending, active, expired, revoked
- `appointed_by` → res.partner
- `appointment_date` — date
- `appointment_method` — selection: election, appointment, volunteer
- `grace_period_days` — integer, default 30
- `reminder_days_before` — integer, default 30

**Continuity protection (CRITICAL):**
- System MUST detect when the last holder of a `is_critical` position is about to
  expire with no successor assigned
- Automatic reminders to board: 60, 30, 14, and 7 days before expiry
- Grace period: mandate holders retain system access for N days after expiry
- Calendar year transitions must NEVER leave the association without admin access
- Emergency access: if all admin mandates expire, the association's primary contact
  on res.company retains full access
- Expired mandates are clearly labeled but NOT immediately revoked — grace period
  ensures continuity

#### vf.mandate.extension
Tracks renewals.

- `mandate_id` → vf.mandate
- `extended_by` → res.partner
- `new_end_date`
- `reason`

### 6.4 — Activities & Events

#### vf.activity.type
Configurable activity types. Created by onboarding wizard, editable by admin.

- `name` — "Träning", "Match", "Tävling", "Cup", "Läger", "Möte", "Social"
- `category` — selection: training, match, competition, cup, camp, meeting, social, other
- `allow_registration` — boolean
- `registration_type` — selection: individual, group, both
  (dance competitions need individual + group; football needs group)
- `require_approval` — boolean
- `track_attendance` — boolean
- `default_duration` — float (hours)
- `max_participants` — integer (0 = unlimited)
- `has_opponent` — boolean (match-specific fields)
- `has_result` — boolean (competition-specific fields)
- `is_recurring` — boolean (training schedules)
- `subsidy_eligible` — boolean (counts for LOK-stöd)
- `color` — integer (for calendar display)

#### vf.activity
The activity/event itself.

- `name`, `description`
- `activity_type_id` → vf.activity.type (required)
- `start_date`, `end_date`, `all_day` — boolean
- `location` — char
- `resource_ids` → many2many vf.resource
- `organizer_id` → res.partner
- `section_id` → vf.section
- `group_id` → vf.group
- `season_id` → vf.season
- **Registration:**
  - `allow_registration`, `require_approval`, `max_participants`
  - `registration_deadline` — date
  - `registration_type` — inherited from type, overridable
  - `registration_ids` → one2many vf.activity.registration
- **Competition-specific** (visible when type has `has_opponent` or `has_result`):
  - `opponent` — char
  - `is_home` — boolean
  - `result_home`, `result_away` — integer
  - `result_note` — text (walkover, cancelled, etc.)
  - `competition_id` → vf.competition
- **Visibility:** selection: public, members_only, participants_only, group_only
- `state` — selection: draft, planned, confirmed, in_progress, completed, cancelled
- `attendance_ids` → one2many vf.activity.attendance

**Registration model (vf.activity.registration):**
- `activity_id` → vf.activity
- `member_id` → vf.member (individual registration)
- `group_id` → vf.group (team/group registration)
- `registration_date`
- `state` — pending, confirmed, waitlisted, cancelled

Both individual members AND entire groups/teams can register for the same activity.
This is essential for: dance competitions (solo + group), swim meets (individual
events within a team entry), football tournaments (team registration).

#### vf.competition (NEW)
Wraps a series of related activities into a league, cup, or tournament.

- `name` — "Division 4 Höst 2025", "DM i dans 2026"
- `competition_type` — selection: league, cup, tournament
- `season_id` → vf.season
- `group_id` → vf.group (which team/group participates)
- `activity_ids` → one2many vf.activity (the individual events/matches)
- `external_url` — char (link to external league system)
- `notes` — text

#### vf.season (NEW)
Binds teams, fees, activities, and members into a time period.

- `name` — "Säsongen 2025/2026"
- `start_date`, `end_date`
- `is_current` — computed
- `is_active`

#### vf.resource
Venues, equipment, facilities that can be booked for activities.

- `name`, `description`
- `resource_type` — selection: venue, equipment, facility, other
- `capacity` — integer
- `location` — char
- `is_active`

### 6.5 — Fees & Economy

#### vf.fee.category
Fee types: membership, activity, license, equipment, material, other.

#### vf.fee
Fee definition with fully flexible pricing. **Nothing is hardcoded.** Every
association configures its own pricing model.

- `name`, `category_id` → vf.fee.category
- `amount` — monetary, the base price
- `currency_id`
- `season_id` → vf.season (optional — season-bound fees)
- `group_id` → vf.group (optional — team-specific fees)
- **Price tiers:**
  - `age_based_pricing` — boolean
  - `family_discount` — boolean
  - `family_discount_percentage` — float
  - `early_bird_discount` — boolean
  - `early_bird_deadline` — date
  - `early_bird_percentage` — float
  - `price_tier_ids` → one2many vf.fee.price.tier
- **Payment options:**
  - `allow_installments` — boolean
  - `installment_count` — integer (e.g. 12 for monthly)
  - `installment_type` — selection: monthly, quarterly, semi_annual, custom
  - `due_date` — date
  - `grace_period_days` — integer
- `is_active`

#### vf.fee.price.tier
Price variations per fee.

- `fee_id` → vf.fee
- `name` — "Barn 0-6", "Junior 7-15", "Senior", "Pensionär"
- `min_age`, `max_age` — integer (0 = no limit)
- `amount` — monetary
- `condition_type` — selection: age, family_position, custom
- `family_position` — integer (1st child full price, 2nd child 75%, etc.)

#### vf.fee.payment
Individual payment records with installment support.

- `member_id` → vf.member
- `fee_id` → vf.fee
- `amount_due`, `amount_paid`
- `payment_date`, `due_date`
- `state` — selection: draft, pending, paid, partial, overdue, cancelled, refunded
- `installment_number` — integer (1 of N)
- `installment_total` — integer (N)
- `payment_reference` — char (OCR number, transaction ID)
- `payment_method` — char (Mollie, bank transfer, cash, Swish)
- `invoice_id` → account.move (optional link to Odoo invoice)
- `payer_id` → res.partner (the person who paid — may differ from member for minors)

#### vf.subsidy.report (NEW — LOK-stöd)
Generates reports in the format required by RF (Riksidrottsförbundet) and
municipalities for activity-based subsidies.

- Based on attendance data:
  - Which activities (only those marked `subsidy_eligible`)
  - How many participants aged 7-25 per activity
  - Leader information per activity
  - Number of activity occasions per period
- `period_start`, `period_end` — date range for the report
- `report_type` — selection: lok_stod, municipal, custom
- Configurable per municipality (different local rules apply)
- Export to PDF in required format
- Summary statistics for board presentations

---

## 7. Security, Privacy & GDPR

**GDPR and security are not afterthoughts. They are foundational requirements
that must be visible and explicit throughout the codebase and documentation.**

### 7.1 — Access Groups

| Group | XML ID | Purpose |
|---|---|---|
| Medlem | `group_vf_member` | Own data, own children, own group members (limited) |
| Ledare | `group_vf_leader` | Their group(s) data, attendance, contact parents |
| Funktionär | `group_vf_functionary` | Cross-group coordination, section-level access |
| Kassör | `group_vf_treasurer` | Financial data, reports, payment status |
| Styrelse | `group_vf_board` | Organization-wide, mandate management |
| Administratör | `group_vf_admin` | Full access, protected data, system config |

Hierarchy: member < leader < functionary < board < admin.
Treasurer is a **separate branch** — financial access without personal/medical data.

### 7.2 — Record Rules (ir.rule)

- Members see their OWN data and their minor children's data
- Leaders see data ONLY for their assigned group(s)
- Guardians see their linked minor children's data
- Protected members are INVISIBLE to everyone except admin
- Treasurer sees financial records but NOT medical/personal notes
- Board sees organization-wide data except protected personal details
- ALL access to protected records is logged

### 7.3 — Protected Personal Data (Sekretessmarkering)

~18,000 people in Sweden have protected identity (sekretessmarkering). This is
not rare — any association with children will encounter it.

Three levels:

1. **Standard** (`protection_level = 'standard'`) — all data visible per role
2. **Protected identity** (`protection_level = 'protected_identity'`) — name and age
   visible; address, phone, email, personnummer HIDDEN from all except admin.
   Guardian contact info also hidden.
3. **Hidden address** (`protection_level = 'hidden_address'`) — as above, PLUS
   household connections and family relationships are hidden.

**Implementation requirements:**
- Computed fields that return empty/masked values based on accessing user's group
- Record rules filtering protected members from search results and list views
- Export functions AUTOMATICALLY exclude protected data (cannot be overridden
  except by admin with explicit confirmation)
- Portal member lists NEVER display protected members' personal details
- Audit trail: who accessed a protected record, when (use mail.tracking)
- Protected status visible only to admin — other users simply see redacted data
  without knowing why

### 7.4 — GDPR Compliance

| Requirement | Implementation |
|---|---|
| **Consent management** | Track consents given: photo, name publication, register sharing, newsletter. Per member, per purpose, with dates. |
| **Right to erasure** | Anonymize — never delete. Replace personal data with "[Raderad]". Preserve aggregate statistics. |
| **Data portability** | "My data" export via portal: PDF or JSON of all personal data held. |
| **Retention policy** | Configurable rules: "anonymize inactive members after N months". Cron job. |
| **Processing register** | Document what data is collected, why, legal basis, retention period. Stored as a system document. |
| **Cookie consent** | Portal/website compliance via standard Odoo mechanisms. |
| **Breach notification** | Template and procedure document available in system. |

### 7.5 — Sensitive Field Groups

All sensitive fields MUST have explicit `groups=` attribute:

| Field | Accessible to |
|---|---|
| `medical_note` | Leader (own group), admin, member's own guardians |
| `emergency_info` | Leader (own group), admin |
| `protected_note` | Admin only |
| `license_number` | Leader (own group), admin |
| `fee_payment` records | Treasurer, admin, the member themselves, the paying guardian |
| Administrative notes | Admin only |

### 7.6 — Delete vs Archive

- **NEVER delete** member records, mandate records, payment records, messages
- Use `active` field for soft-archiving
- `ondelete='restrict'` on all relationships where deletion would be destructive
  (member → partner, mandate → position, payment → fee)
- Exception: GDPR erasure request → anonymize, do not delete

### 7.7 — Import/Export Control

- Raw CSV/Excel import restricted to admin group
- Raw export restricted to admin group
- Treasurer has access to **predefined report formats only** — no arbitrary data dumps
- All exports automatically strip protected personal data unless admin + explicit
  confirmation
- Import wizard includes validation: orphan minors check, duplicate detection,
  required guardian for minors

---

## 8. Portal & Frontend

### 8.1 — Design Requirements

The portal is the face of the system. Parents, coaches, and volunteers will use
it daily. It must not look like a default Odoo backend with a different color.

- Clean, modern, professional design
- **Mobile-first** responsive layout (coaches take attendance on phones on the field)
- Accessible: WCAG 2.1 AA minimum
- Fast: no unnecessary page loads for common actions
- Swedish as primary language, fully translatable
- Consistent visual language between backend and portal

### 8.2 — Portal Views by Role

**Member / Parent (Medlem / Målsman):**
- My profile (edit own data within defined limits)
- My children (for guardians: see and manage linked minors)
- My teams / groups (see roster, see other members in same group)
- Upcoming activities and weekly schedule
- Register for activities (self or child)
- My payments and invoices (payment history, outstanding, pay online)
- My documents (personal documents, group documents)
- Contact form — send message to coach, board, treasurer by ROLE (see §9.2)
- Calendar export (ICS subscription)

**Leader / Coach (Ledare / Tränare):**
- My team(s) roster with member details (respecting privacy levels)
- **Quick attendance** — mobile-optimized: tap names on a list, done
  (this is the #1 use case for mobile — a coach on the field)
- Send message to team / parents of team members
- Upcoming activities for my team(s)
- Attendance statistics (last 4 weeks, trend indicators)
- Register team for competitions

**Treasurer (Kassör):**
- Payment status overview (who paid, who hasn't, filterable)
- One-click send payment reminders
- Generate LOK-stöd reports
- Financial summary reports
- Export controlled reports (PDF, predefined formats)

**Admin / Board (Administratör / Styrelse):**
- Everything above
- Full member management
- Mandate management with expiry warnings
- System configuration
- GDPR compliance tools (anonymization, data export)

### 8.3 — Organization Tree View

Interactive visualization of the association structure:
- Association → Sections → Groups/Teams → Members
- Board → Section chairs → Coaches → Team members
- Click to navigate, expand/collapse nodes
- Available in BOTH backend and portal
- Shows current mandate holders for each position
- Filterable by section, active/inactive

### 8.4 — Document Embedding

Documents must be easy to display in frontend pages:
- Widget/component that renders a document inline (PDF viewer, image display)
- Configurable per document: "show on group page", "show on public page"
- Version-aware: always shows latest version unless pinned
- Respects access control: document visibility levels apply

---

## 9. Communication Hub

### 9.1 — Messaging Hierarchy

Messages flow **downward** through the organization. Each role level can
communicate to levels below:

| Sender Role | Can Send To |
|---|---|
| Styrelse (Board) | Everyone: all members, all leaders, all functionaries, all groups |
| Funktionär | Leaders in their section, members in their section |
| Ledare (Coach) | Their team/group members, parents/guardians of minors in their team |
| Medlem (Member) | Their coach, responsible functionary above coach, team/group mates |

All messaging uses **role-based addressing**, not personal email. When a coach
is replaced, the new coach inherits the communication channel.

### 9.2 — Contact Form (Role-Based Routing)

Available from member dashboard. The user selects a **recipient by role**:

- "Kontakta styrelsen" → routes to current board
- "Kontakta kassören" → routes to current treasurer
- "Kontakta min tränare" → routes to the coach of the member's group
- "Kontakta sektionsansvarig" → routes to section manager

The system resolves which person currently holds the position. When people
change, messages automatically route correctly. **No private email addresses
are ever exposed.**

This contact form must be:
1. Available in the member portal (authenticated)
2. Available as a **reusable frontend widget** for the public website
   (for external visitors to reach the association — via `vf_association_portal`)
3. Configurable: admin can choose which recipient roles are available
4. Include subject, message body, optional attachment

### 9.3 — Whistleblower System

Anonymous reporting channel. Required by Swedish whistleblower protection law
(visselblåsarlagen) for organizations above 50 employees, but good practice
for all associations.

- Accessible from portal and optionally from public website
- Sender identity is **NEVER stored, logged, or visible**
- Messages go to a designated handler (configurable: board chair, external party,
  or a specific position)
- **No reply capability** (preserves anonymity)
- Reports are logged with timestamp and content only — no sender metadata
- Handler can add internal notes but cannot identify the reporter
- Separate from the regular messaging system entirely

### 9.4 — Message History & Continuity

- Full message history is retained even when role holders change
- Messages are linked to the **position**, not the individual person
- When a coach leaves and a new one takes over, the new coach can see team
  communication history relevant to their role
- Personal messages (member → specific person) remain private

### 9.5 — Automated Notifications & Reminders

All automated via cron jobs, configurable:

| Notification | Timing | Recipient |
|---|---|---|
| Mandate expiry | 60, 30, 14, 7 days before | Board + the person |
| Fee payment due | Configurable (e.g., 14 days before, on date, 14 days after) | Member / paying guardian |
| Activity reminder | Day before, morning of | Participants + guardians of minors |
| License expiry | 30, 14 days before | Member + admin |
| Attendance no-show | After activity ends | Guardian of minor (configurable) |
| Welcome message | On member creation | New member |
| Season opening | At season start | All members in season |

---

## 10. Economy, Payments & Sponsorship

### 10.1 — Payment Provider: Mollie

Primary payment integration: **Mollie** (https://www.mollie.com/)

Mollie provides a single integration covering:
- Card payments (Visa, Mastercard)
- Invoice
- Klarna (pay later, installments)
- Swish (Sweden)
- Bank transfer
- And more per market

Implementation via Odoo's `payment.provider` framework. The Mollie connector
should be a thin layer in `vf_association` that registers as a payment provider.

Affiliate link integration for ARC Gruppen AB (to be configured).

### 10.2 — Fee Management

See §6.5 for model details. Key operational features:

- **Flexible pricing**: per season, per group, per age bracket, family discounts,
  early bird discounts — all configurable, nothing hardcoded
- **Installment plans**: split any fee into N payments (monthly, quarterly, custom)
- **Automatic invoice generation** via account.move
- **Payment matching**: OCR numbers on invoices for bank transfer reconciliation
- **Overdue tracking**: automatic status transition, reminder scheduling
- **Multi-payer support**: separated parents can split fees (both marked as `is_payer`
  on guardian relationship — system generates two invoices for half amount each,
  or one invoice to primary payer, configurable)

### 10.3 — Treasurer's Toolkit

The treasurer should feel like this system was built specifically for them:

- **Who has paid / who hasn't** — real-time, filterable by group, season, fee type
- **One-click reminders** — select unpaid, preview message, send
- **LOK-stöd report** — generates RF-compliant format from attendance data
  - Eligible activities (marked `subsidy_eligible`)
  - Participants aged 7-25
  - Leader information per activity
  - Activity count per period
  - Configurable for municipal variations
- **Financial summary** — income by category, by period, outstanding amounts, trends
- **Budget vs actual** — optional budget entry, variance display
- **Board-ready PDF** — one-click export for board meetings
- **Controlled export** — predefined report templates, no raw data dumps

### 10.4 — Sponsorship (`vf_association_sponsorship`)

Separate module due to `sale_management` dependency.

- **Sponsor packages** — definable tiers with benefits, pricing, validity periods
- **Sponsor profiles** — company info, contact persons, history
- **Contract management** — start/end dates, automatic renewal, invoicing
- **Targeted communication** — newsletter to sponsors, different from member comms
- **Sponsor visibility** — logo placement on portal/website (configurable)
- **Donations & gifts** — separate from membership fees, optional tax receipt
- **Sponsor dashboard** — overview of active sponsors, expiring contracts, revenue

### 10.5 — Merchandise (`vf_association_sponsorship`)

Via Odoo's `sale_management` + `website_sale`:

- **Product catalog** — association merchandise (jerseys, scarves, water bottles)
- **Member pricing** — special prices for members
- **Customization options:**
  - Name print (player name on jersey)
  - Number print (jersey number)
  - Back print / custom embroidery
  - Stored as product variants or sale order line options
- **Team orders** — coach orders for the whole team in one go
- **Delivery tracking** — standard Odoo sale flow

---

## 11. Onboarding & Configuration

### 11.1 — Onboarding Wizard

Shown automatically on first login after installation. Also accessible via
Settings > Förening > Konfigurationsguide.

Implemented as a `TransientModel` wizard with multiple steps.

**Step 1 — Typ av förening (Association Type)**

Selection with icon/illustration per type:
- Idrott (Sport)
- Kultur & musik (Culture & music)
- Socialt & ideellt (Social & nonprofit)
- Friluftsliv & scout (Outdoor & scouts)
- Annan (Other)

Saved to `vf.association.config` singleton.

**Step 2 — Verksamhetsdetaljer (Activity Details)**

Content varies based on Step 1 selection:

*If Sport:*
- Individual sport / Team sport / Both
- Which sports? (multi-select from common list + free text for custom)
- Competition activities? Yes/No
- Season-based? Yes/No → Autumn-Spring / Calendar Year / Custom dates

*If Culture & Music:*
- Type: Choir / Orchestra / Theater / Art / Dance / Other
- Performances/concerts? Yes/No
- Recurring rehearsals? Yes/No

*If Social & Nonprofit:*
- Type: Pensioners / Sobriety / Humanitarian / Religious / Other
- Regular meetings/gatherings? Yes/No
- Volunteer coordination needed? Yes/No

*If Outdoor & Scouts:*
- Type: Scouts / Hiking / Climbing / Kayaking / Orienteering / Other
- Camps/expeditions? Yes/No
- Certifications/badges? Yes/No

**Step 3 — Struktur (Structure)**

- Sections? Yes/No → Create initial sections with names
- Board/committee? Yes → Pre-create positions (chair, vice-chair, treasurer,
  secretary) — user confirms or modifies
- Minor members? Yes → Activate guardian requirement features
- Approximate member count? (helps suggest appropriate defaults)

**Step 4 — Ekonomi (Economy)**

- Membership fees? Yes → Activate fee module
- Payment frequency: Annual / Semi-annual / Quarterly / Monthly
- Family discount? Yes/No → Configure percentage
- Activity fees (pay-per-event)? Yes/No
- LOK-stöd / activity subsidies? Yes → Activate attendance reporting & subsidy module
- Online payments? Yes → Configure Mollie (or skip for later)

**Step 5 — Kommunikation & Dokument (Communication & Documents)**

- Internal messaging? Yes → Activate communication hub
- Document management? Yes → Activate document system
- Whistleblower channel? Yes → Activate (with handler assignment)
- Contact form on website? Yes → (requires portal module)

**Wizard result:**
- Feature toggles set in `res.config.settings`
- Default data records created (sections, positions, fee categories, activity types)
- Tailored activity types based on association type (e.g., Sport → Träning, Match,
  Cup, Läger; Culture → Repetition, Konsert, Workshop)
- Welcome documentation generated
- Next-steps checklist displayed

### 11.2 — Association Configuration Singleton

`vf.association.config` — one record per company.

- `association_type` — selection (from wizard)
- `association_subtype` — char (sport type, culture type, etc.)
- `has_sections` — boolean
- `has_minors` — boolean
- `has_competitions` — boolean
- `has_seasons` — boolean
- `season_type` — selection: autumn_spring, calendar_year, custom
- `season_start_month`, `season_end_month`
- `default_currency_id`
- `subsidy_municipality` — char (for LOK-stöd configuration)
- `whistleblower_handler_id` → vf.position
- `onboarding_completed` — boolean

---

## 12. Templates, Reports & Documents

### 12.1 — Document Management

Documents can be linked to:
- A specific member (personal documents, certificates)
- A group/team (team rules, training plans)
- A section (section policies, bylaws)
- An activity/event (event programs, results)
- The association as a whole (statutes, annual reports)

Features:
- **Version control** — upload new version, previous versions retained
- **Access control** — public, members_only, group_only, board_only, admin_only
- **Categories** — configurable taxonomy
- **Frontend embedding** — documents can be displayed inline in portal pages
- **Search** — full-text search within document metadata

### 12.2 — Email Templates

Pre-built templates (all in Swedish, translatable):

| Template | Purpose | Variables |
|---|---|---|
| Välkommen ny medlem | New member welcome | member_name, association_name, login_url |
| Avgiftspåminnelse | Payment reminder | member_name, fee_name, amount, due_date, pay_url |
| Avgiftskvitto | Payment receipt | member_name, amount, payment_date, reference |
| Mandatpåminnelse | Mandate expiry warning | person_name, position, end_date, days_remaining |
| Aktivitetspåminnelse | Activity reminder | activity_name, date, time, location |
| Närvarobekräftelse | Attendance confirmation | activity_name, date, attendees_count |
| Licenspåminnelse | License expiry | member_name, license_type, expiry_date |
| Styrelsesammankallelse | Board meeting call | date, time, location, agenda_url |

All templates editable by admin. Uses Odoo's `mail.template` framework with
QWeb rendering.

### 12.3 — Report Templates

PDF reports generated via QWeb (built into Odoo, no external dependencies):

- **Member list** — filterable by group, section, status, age range
- **Attendance report** — per activity, per group, per period
- **LOK-stöd report** — RF-compliant format
- **Financial summary** — income, outstanding, by category
- **Mandate overview** — current positions, holders, expiry dates
- **Group roster** — members of a team/group with relevant contact info

### 12.4 — Import/Export Templates

For the treasurer and admin:
- **CSV import template** — predefined column mapping for bulk member import
- **Export formats** — predefined, controlled, never raw database dumps
- **Accounting export** — SIE format (Swedish standard) for external accounting software

---

## 13. Calendar & Scheduling

### 13.1 — Calendar Integration

Activities are displayed in a calendar view:
- **Backend** — Odoo's native calendar view with color-coding by activity type
- **Portal** — visual calendar per group/team showing upcoming activities
- **iCal/ICS export** — per group/team, subscribable URL that parents can add
  to their own calendar (Google Calendar, Apple Calendar, Outlook)
  - Automatically updated when activities change
  - One URL per group (coach shares with parents)
  - Includes: activity name, time, location, description

### 13.2 — Schedule Display in Portal

- Weekly view per group: "This week's schedule"
- Upcoming activities list with quick register/deregister
- Time display respects user's timezone
- Mobile-optimized view

### 13.3 — Recurring Activities

Training schedules can be defined as recurring:
- `vf.activity.schedule` — defines pattern (every Tuesday 18:00-19:30)
- Generates individual `vf.activity` instances for each occurrence
- Exceptions can be added (cancelled, moved, modified)
- Linked to season: schedule active within season dates

---

## 14. Dashboard

### 14.1 — Single Dashboard, Role-Based Content

One dashboard view. Content and KPIs vary based on the logged-in user's role(s).
Implemented as an OWL 2 component with dynamic sections.

### 14.2 — Dashboard Content by Role

**Admin / Board (Administratör / Styrelse):**
- Total active members (with trend: +/- vs last period)
- New members this month
- Mandates expiring within 30 days (RED if critical positions)
- Outstanding fees (total amount, member count)
- Quick links: manage members, manage mandates, system settings
- Recent system activity log

**Treasurer (Kassör):**
- Unpaid fees total and count
- Payments received this period
- Overdue payments requiring action
- LOK-stöd eligible activities this period
- Revenue by category (chart)
- Quick actions: send reminders, generate report, view payments

**Leader / Coach (Ledare):**
- My team(s) roster summary (member count, new members)
- Upcoming activities for my team(s) (next 7 days)
- Attendance rate last 4 weeks (chart/percentage)
- Unread messages
- Quick actions: take attendance, send message to team, register for activity

**Member / Parent (Medlem / Målsman):**
- My upcoming activities (next 7 days)
- My children's upcoming activities (if guardian)
- Payment status (outstanding/next due)
- Unread messages
- Contact form (reach coach, treasurer, board)
- Quick links: my profile, my team, calendar

### 14.3 — Dashboard Customization

Admin can configure which sections are visible per role. Default configuration
should be sensible — most associations should never need to change it.

---

## 15. Internationalization

### 15.1 — Code Language

- All Python code, JavaScript code, variable names, model names, field names:
  **English**
- All module technical names: **English** (e.g., `vf_association`, not `vf_forening`)

### 15.2 — User-Facing Language

- **Swedish is the PRIMARY language** — all user-visible strings are written in
  Swedish first
- Every string MUST be wrapped in `_()` for translation support
- Field labels use `string=_("Svensk text")`
- Help texts use `help=_("Hjälptext på svenska")`
- Selection labels: `[('key', _("Svensk etikett"))]`
- XML data: Swedish text in `<field name="name">` — translatable via `.po` files
- `translatable=True` on all user-facing Char and Text fields

### 15.3 — Translation Files

- `i18n/sv.po` — Swedish (primary, complete)
- `i18n/vf_association.pot` — template for other translations
- Future: `i18n/en.po`, `i18n/no.po`, `i18n/fi.po` as needed

### 15.4 — No Hardcoded Strings

Zero tolerance for hardcoded user-visible strings anywhere:
- Not in Python (`raise UserError(_("Meddelande"))` — always with `_()`)
- Not in JavaScript (use Odoo's `_t()` function)
- Not in XML views (use `string=` attributes with translatable values)
- Not in email templates (use QWeb with translatable blocks)
- Not in report templates (use QWeb with translatable blocks)

---

## 16. Testing

### 16.1 — Requirement

Every model MUST have tests. A feature without tests does not exist.

### 16.2 — Test Coverage

Minimum test cases per area:

**Member:**
- Create adult member → success
- Create minor member without guardian → MUST fail
- Create minor member with guardian → success
- Set protection level → verify data hiding for non-admin users
- Medical note access → leader sees it, regular member doesn't

**Guardian:**
- Add guardian to minor → verify relationship created
- Remove last guardian from minor → MUST fail
- Separated parents: child in two households → both guardians receive communication

**Groups:**
- Add member to group → group membership created
- Member sees other members in same group
- Member does NOT see members in other groups

**Mandates:**
- Create mandate → status transitions (pending → active → expired)
- Critical position expires with no successor → warning generated
- Grace period: expired mandate holder retains access for N days
- Mandate reminder: fires at correct days before expiry

**Activities:**
- Create activity → register individual member
- Create activity → register entire team/group
- Take attendance → record created, subsidy eligibility computed
- Recurring schedule → generates correct activity instances

**Fees:**
- Create fee with installments → generates correct payment schedule
- Family discount → calculates correctly for 1st, 2nd, 3rd child
- Payment recorded → status transitions correctly
- Overdue → reminder triggered at correct time

**Security:**
- Protected member data → non-admin cannot read address/phone
- Record rules → leader sees only their group
- Export → protected data stripped automatically
- Treasurer → sees financial data, not medical notes

### 16.3 — Test Framework

Use `TransactionCase` for most tests, `HttpCase` for portal/frontend tests.

```python
# tests/test_member.py
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestMember(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test data...
```

---

## 17. Documentation

### 17.1 — In-Code Documentation

- Docstrings on all public methods
- Complex business logic explained with inline comments
- Security decisions documented at the point of implementation

### 17.2 — User Documentation

- README.md per module
- Installation guide
- Configuration guide (how to use onboarding wizard)
- Role-specific guides: "Guide för kassören", "Guide för ledaren"
- GDPR documentation: what data is collected, why, legal basis

### 17.3 — Developer Documentation

- This LLM-INSTRUCTION.md file (you're reading it)
- ARCHITECTURE-AND-INSTRUCTIONS.md (the companion document with analysis)
- OPEN-QUESTIONS.md (questions that need resolution)
- CHANGELOG.md (what changed and when)

---

## 18. Open Questions

Questions that are NOT blocking but need eventual resolution:

1. **SIE export format** — which version? SIE4? Required by which accounting systems?
2. **Mollie affiliate integration** — technical details pending from ARC Gruppen
3. **LOK-stöd format variations** — need to collect municipality-specific requirements
4. **OCA upstream sync** — how to handle the 7 inherited OCA modules going forward
5. **Mobile app vs PWA** — is a responsive portal sufficient or is native app needed?
6. **BankID integration** — for identity verification at registration? (Swedish eID)
7. **Sportfederations API** — any existing integrations with RF/SvFF/other federations?
8. **Multi-association** — can one Odoo instance serve multiple associations? (multi-company?)

---

*This document is maintained alongside the codebase and updated as decisions
are made. Last updated: 2026-02-24.*
