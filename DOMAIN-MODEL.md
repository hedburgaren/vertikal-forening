# Vertical Association - Phase 1 Domain Model

This document defines the domain model for Phase 1 implementation of Vertical Association, covering Members & Families, Groups & Sections, and Roles & Access Control.

---

## Core Design Principles

1. **Separation of Concerns**: Membership status is completely separate from role assignments
2. **Extend, Don't Replace**: Leverage Odoo's res.partner for person data, but create association-specific models
3. **Time-Bound Everything**: Roles and mandates must have explicit time boundaries
4. **Audit Trail**: All changes must be tracked for continuity
5. **Privacy by Default**: Sensitive data requires explicit access grants

---

## Entity Definitions

### 1. Member Management (vf_member)

#### vf.member
- **Purpose**: Represents association membership status (separate from person data)
- **Key Fields**:
  - `partner_id` → res.partner (the person)
  - `membership_number` (unique, auto-generated)
  - `membership_date` (when they became a member)
  - `is_minor` (computed from birth date)
  - `status` (active, inactive, suspended, archived)
  - `notes` (private administrative notes)

#### vf.guardian.relationship
- **Purpose**: Defines guardian relationships for minors
- **Key Fields**:
  - `member_id` → vf.member (the minor)
  - `guardian_id` → res.partner (the guardian)
  - `relationship_type` (primary, secondary, emergency)
  - `start_date`, `end_date`
  - `is_active` (computed)
  - `legal_custody` (boolean)

#### vf.family.relationship
- **Purpose**: Optional family connections between members
- **Key Fields**:
  - `member_id` → vf.member
  - `related_member_id` → vf.member
  - `relationship_type` (sibling, parent_adult, spouse, other)
  - `household_id` → vf.household (optional)

#### vf.household
- **Purpose**: Groups members living at the same address
- **Key Fields**:
  - `name` (optional, e.g., "The Smith Family")
  - `address_id` → res.partner
  - `member_ids` → vf.member (one2many)

### 2. Group & Section Organization (vf_group)

#### vf.section
- **Purpose**: Highest organizational level
- **Key Fields**:
  - `name`
  - `description`
  - `parent_id` → vf.section (for nested sections)
  - `manager_id` → res.partner (section manager)
  - `is_active`

#### vf.group
- **Purpose**: Teams, committees, working groups
- **Key Fields**:
  - `name`
  - `section_id` → vf.section
  - `group_type` (team, committee, working_group, other)
  - `description`
  - `max_members`
  - `min_age`, `max_age` (optional restrictions)
  - `is_active`
  - `parent_group_id` → vf.group (for sub-groups)

#### vf.group.membership
- **Purpose**: Links members to groups (separate from roles)
- **Key Fields**:
  - `member_id` → vf.member
  - `group_id` → vf.group
  - `join_date`
  - `leave_date` (optional)
  - `is_active` (computed)

### 3. Roles & Access Control (vf_role)

#### vf.role
- **Purpose**: Defines a role type with permissions
- **Key Fields**:
  - `name`
  - `description`
  - `access_level` (organization, section, group)
  - `is_managerial` (can assign other roles)
  - `requires_approval` (needs board approval)
  - `permission_ids` → ir.model.access (custom permissions)

#### vf.position
- **Purpose**: Defines a specific position within a group/section
- **Key Fields**:
  - `name`
  - `role_id` → vf.role
  - `group_id` → vf.group (optional)
  - `section_id` → vf.section (optional)
  - `is_active`
  - `max_holders` (how many people can hold this position)

#### vf.mandate
- **Purpose**: Time-bound assignment of a person to a position
- **Key Fields**:
  - `person_id` → res.partner
  - `position_id` → vf.position
  - `start_date`, `end_date`
  - `status` (pending, active, expired, revoked)
  - `appointed_by` → res.partner
  - `appointment_date`
  - `notes`

#### vf.mandate.extension
- **Purpose**: Tracks mandate extensions and renewals
- **Key Fields**:
  - `mandate_id` → vf.mandate
  - `original_end_date`
  - `new_end_date`
  - `extension_reason`
  - `approved_by` → res.partner
  - `approval_date`

---

## Key Relationships

```
res.partner (Person)
    ├── 1:1 → vf.member (Membership Status)
    ├── 1:N → vf.guardian.relationship (as Guardian)
    └── 1:N → vf.mandate (Position Assignments)

vf.member
    ├── 1:N → vf.guardian.relationship (as Minor)
    ├── 1:N → vf.family.relationship
    ├── N:1 → vf.household
    └── 1:N → vf.group.membership

vf.section
    ├── 1:N → vf.group
    └── 1:N → vf.position

vf.group
    ├── 1:N → vf.group.membership
    ├── 1:N → vf.position
    └── 1:N → vf.group (sub-groups)

vf.role
    └── 1:N → vf.position

vf.position
    └── 1:N → vf.mandate

vf.mandate
    └── 1:N → vf.mandate.extension
```

---

## Security Model

### Access Groups
- `vf_user`: Basic member access (own data)
- `vf_leader`: Group/section leaders (their groups)
- `vf_admin`: Association administrators
- `vf_treasurer`: Financial access (reports only)

### Permission Rules
1. Members can see their own data and their minor children's data
2. Leaders can see data for their groups/sections only
3. Guardians can see their minor children's data
4. All access is logged and auditable
5. Sensitive data (health, special needs) requires explicit permission

---

## Implementation Notes

1. **No Deletion**: Use `active` field for archiving
2. **Computed Fields**: Use for age, status, and relationships
3. **Constraints**: Ensure data integrity (e.g., minors must have guardians)
4. **Indexing**: Proper indexes on foreign keys and search fields
5. **Translation**: All user-visible strings must be translatable

---

## Open Questions (to be resolved during implementation)

1. How to handle membership fees? (Phase 3)
2. Integration with Odoo's existing membership module?
3. How to import existing member data?
4. GDPR compliance features needed?
5. Integration with website frontend? (Phase 4)

---

## Next Steps

1. Implement vf_member module with core models
2. Implement vf_group module with organization structure
3. Implement vf_role module with access control
4. Create security configurations
5. Add views and frontend integration
6. Write comprehensive tests
7. Document all APIs and data structures
