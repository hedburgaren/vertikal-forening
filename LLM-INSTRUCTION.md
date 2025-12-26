# LLM Instruction – Vertical Association (Odoo 18 CE)

This document defines mandatory rules for any Large Language Model contributing to this repository.
These rules exist to protect long-term quality, security and maintainability.

---

## Role of the LLM

The LLM is expected to work **autonomously**.

Functionality must be fully implemented.  
Partial solutions, sketches or MVP reasoning are not permitted.

A feature either works completely, or it does not exist.

---

## Communication Rules

The LLM MUST NOT:
- ask for naming decisions
- ask for minimum scope or MVP definitions
- pause development waiting for confirmation
- block progress due to uncertainty

The LLM MAY ONLY interrupt the user for:
- questions that directly affect functional correctness
- legal or security-critical behavior

All other questions MUST:
- be written to a documentation file
- be clearly described
- NOT stop execution

Development must always continue.

---

## Technical Constraints

- Target platform: **Odoo 18 Community Edition**
- Code for pre-Odoo-18 is strictly forbidden
- Deprecated APIs, legacy XML attributes and outdated security models are not allowed
- All modules must follow OCA conventions

---

## Architecture Rules

- Each functional area must live in its own module
- No god-modules
- No undocumented cross-dependencies
- Domain modeling must precede implementation

---

## Security & Privacy

- Data related to minors, guardians, health or edge cases is always treated as sensitive
- Access must be explicitly granted, never assumed
- When in doubt, default to more restrictive access
- Deletion should be replaced with archiving unless legally required

---

## Import / Export

- Raw import/export functionality must be restricted to system administrators only
- All other users must rely on controlled reports and exports
- No unrestricted CSV or data dumps

---

## Mandates & Continuity

- Time-limited roles must include:
  - reminders before expiration
  - grace periods after expiration
- The system must never leave an association without administrative access
- Loss of access due to calendar year transitions must be prevented

---

## Internationalization

- All code is written in English
- All user-visible text must be translatable
- Hard-coded strings are forbidden
- Frontend and backend must support localization equally

---

## Frontend Support

- Where functionality is relevant to members, guardians or leaders:
  - frontend integration snippets must be provided
- Frontend must respect the same access rules as backend

---

## Documentation as Artifact

- All assumptions and unresolved questions must be documented
- Design decisions must be understandable without chat history
- README and documentation files are first-class deliverables

---

## Naming & Neutrality

- Do not introduce vendor-specific or internal names
- Use neutral, generic and community-friendly terminology
- Project branding must remain association-focused, not company-focused

---

## Final Rule

The LLM must act as if this system will be maintained for **20 years**  
by people who were not involved in its creation.

Short-term convenience must never override long-term stability.
