# Shepherd — Security & Data Protection

Shepherd is designed to help churches manage their work while keeping personal data safe, private, and controlled.  
This document explains, in simple terms, how your data is protected.

---

# 1. Our approach to security

We understand that parish data is sensitive.  
This includes names, contact details, sacramental records, and internal church information.

Our approach is simple:

- Only the right people can access data
- Data is not publicly visible
- Systems are protected with multiple layers of security
- We follow responsible and widely accepted practices

---

# 2. Who can access your data?

### Administrators
Only authorised parish administrators can access:

- Parish registry records
- Exports (CSV and print)
- App users
- Church settings

### Regular users
Regular members and volunteers:

- Cannot access parish registry records
- Cannot access admin pages
- Can only see their own information and relevant event details

If a non-admin tries to access restricted pages, they are redirected automatically.

---

# 3. Secure login and access control

All users must sign in using:

- Email
- Password

Additional protections:

- Sessions expire automatically after a period of inactivity
- Inactive accounts cannot access the system
- Sensitive actions require a valid logged-in session

This prevents unauthorized access even if someone leaves a device unattended.

---

# 4. Separation of data (important protection)

Shepherd keeps two types of data separate:

### App users (people with logins)
Used for:
- Events
- Attendance
- Volunteers
- Notifications

### Parish registry (official church records)
Used for:
- Sacraments
- Membership status
- Historical records

👉 These are not automatically linked.

This separation reduces risk and protects sensitive archival data.

---

# 5. Where is the data stored?

Your data is stored in a secure database system.

Important points:

- It is not a public website
- It cannot be opened in a browser
- It cannot be searched online

Only the Shepherd application can access it.

---

# 6. Who can access the database?

The database is protected so that:

- Only the Shepherd backend system can connect to it
- Secure credentials are required for access
- Direct access from the internet is blocked

### About hosting providers

The system may be hosted on professional infrastructure providers.

- They provide the servers and environment
- They do not use or access your data
- Access to systems is restricted and monitored

---

# 7. Protection against hackers

Shepherd uses several layers of protection:

### Not publicly exposed
The database is not directly reachable from the internet.

### Authentication required
Only valid users can access the system.

### Backend enforcement
Security is enforced on the server, not just the interface.

### Multiple safeguards
These include:

- Login protection
- Server-level restrictions
- Database authentication
- Controlled access to endpoints

---

# 8. Data integrity (keeping records accurate)

The system prevents errors and inconsistencies:

- Duplicate registration numbers are blocked
- Invalid data is rejected
- Controlled updates ensure records remain consistent

This protects both accuracy and reliability.

### Administrative audit log

Shepherd also records **selected administrative and security-related events** in a database-backed **audit log** (for example sign-in outcomes, registry and settings changes, exports, notifications, events, attendance, volunteer assignments, and similar actions). This supports **accountability**, basic **traceability**, and can help administrators notice **unusual or unexpected activity** when reviewing entries over time.

**Passwords**, **session tokens**, and other authentication secrets are **not** stored in the audit log. The log does **not** keep full copies of exported datasets. The audit log is **not** a full security information (SIEM) system.

---

# 9. Backups and data safety

Shepherd includes **PostgreSQL logical backups** you can run on a schedule:

- Backups use the standard **`pg_dump`** tool and are stored as **timestamped SQL files** in a directory you configure (`BACKUP_DIR`). The **`pg_dump` / `psql` client major version** should match your PostgreSQL server (see project `README.md`); mismatch can break restores.
- After each successful run, **older files are removed** so only the most recent `BACKUP_RETENTION_COUNT` backups are kept (by design; adjust retention to your parish policy).
- **Restoring** uses **`psql`** (or the provided helper script in the repository) against a **target database** you control. Restoring over live data can **overwrite** records—always test on a **copy** first.

**Limitations:** backups live where you configure them (e.g. a Docker volume or disk path). They are **not** automatically copied off-site; for disaster recovery, copy backup files to another location or service your organisation trusts. Rate limiting on sign-in helps reduce brute-force noise but is **per server process** and is not a substitute for network-level protection in production.

---

# 10. Privacy and responsible use

Shepherd is designed with privacy in mind:

- Data is only visible to authorised users
- Data is not shared externally
- Personal information is handled responsibly

Where applicable, the system aligns with general privacy expectations such as GDPR.

---

# 11. What Shepherd does NOT do

To be clear:

- We do not make your data public
- We do not sell or share your data
- We do not allow unrestricted access to records

---

# 12. Honest note about security

No system in the world can guarantee zero risk.

However:

- Shepherd uses established and responsible practices
- Access is controlled and monitored
- Risks are minimized through multiple layers of protection

---

# 13. Your role in keeping data safe

Security is shared responsibility.

Users should:

- Keep passwords private
- Log out on shared devices
- Use trusted devices when possible
- Inform administrators of suspicious activity

Administrators should:

- Limit admin access to trusted individuals
- Keep contact details accurate
- Review user access periodically

---

# 14. Summary

Shepherd protects parish data by:

- Restricting access to authorised users
- Keeping data separate and controlled
- Using secure systems and infrastructure
- Preventing direct access to databases
- Applying multiple layers of protection

The goal is simple:

👉 To provide a safe, reliable, and respectful environment for managing church records.

---

# Shepherd

Helping your church stay organised, connected, and secure.
