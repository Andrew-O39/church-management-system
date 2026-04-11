# Shepherd — User Guide

**Shepherd** is the church management workspace your parish uses for day-to-day operations: events, volunteering, attendance, ministries, notifications (including SMS and WhatsApp where configured), and reporting. This guide explains how to use the **current** Shepherd web app from a parish **member** or **administrator** perspective.

> **This is an end-user handbook.** It is not developer documentation, an API reference, or a technical architecture document.

---

## Purpose of Shepherd

Shepherd helps your church:

- **Stay organised** — events, ministries, volunteers, and reminders in one place.
- **Communicate** — messages inside the app, and (when set up) by SMS or WhatsApp to people who use the app.
- **Separate two kinds of records** — **operational** work uses **app users** (people with logins). **Official parish registry** records are maintained separately and do **not** automatically create logins.

---
## How Shepherd is organised (quick overview)

Shepherd is organised into two main areas:

1. **Operational area (day-to-day work)**
   - Events
   - Volunteers
   - Attendance
   - Notifications
   - Dashboard and Exports (admin)

   These features work with **App users (people who can log in)**.

2. **Parish registry (official records)**
   - Membership records
   - Sacramental information
   - Registration numbers
   - Demographic reporting

   These records are **separate from login accounts** and are managed by administrators.

If you remember only one thing:

> **App users = people who use the system**  
> **Parish registry = official church records**

---
### How the system is structured

```text
Parish Registry (official records)
---------------------------------
- Church members
- Sacraments
- Registration numbers
- Demographics

        │ (optional link)
        ▼

App Users (logins)
-----------------
- Email + password
- Profile
- Notifications
- Event participation

        │ (used by)
        ▼

Operational Features
-------------------
- Events
- Attendance
- Volunteers
- Notifications
- Exports / Dashboard


Admin workflow overview
-------------------
Create Event
     ↓
Assign Volunteers
     ↓
Add Reminders
     ↓
Run Reminders (optional)
     ↓
Record Attendance
     ↓
Export / Print Results

This is the most common weekly flow for parish administrators.


How a person can exist in Shepherd
---------------------

Case 1: Registry only
---------------------
Parish Registry ✔
App User ✘
→ Official record only (no login)

Case 2: App user only
---------------------
Parish Registry ✘
App User ✔
→ Can log in and use the system

Case 3: Linked (optional)
-------------------------
Parish Registry ✔
App User ✔
→ Same person has both a record and a login

Linking a registry record to a login is optional and done by administrators.
```
---
## Who uses Shepherd?

| Who | Typical use |
|-----|-------------|
| **Members and volunteers** | Sign in, update profile, view events, see volunteer roles, mark notifications read. |
| **Parish administrators** | Everything members can do, plus dashboard, exports, parish registry, app users, full event/volunteer/attendance tools, sending notifications, church settings, and reminder tools. |

---

## Roles in the app

After you sign in, the top bar shows your **name** and **role** (for example “admin”, “group leader”, or “member”).

- **Admin**  
  Full access to Shepherd’s administrative areas: **Dashboard**, **Exports**, **Church settings**, **Parish registry**, **App users**, and the full **Events** tools (editing, attendance, volunteers, event reminders).

- **Group leader** and **Member**  
  These roles use the same **navigation** as each other for admin-only links: they **do not** see Dashboard, Exports, Church settings, Parish registry, or App users in the menu. They **do** see Profile, Events, Notifications, Ministries, and Volunteers.

> **Note:** Shepherd’s interface treats only **admin** as a powerful role today. If you need administrative work done, your parish should use an **admin** account.

---

## Getting started

### Create an account

1. Open Shepherd in your web browser (your parish will give you the address).
2. Click **Create account** in the top bar (or on the home page).
3. Enter your **full name**, **email**, and **password** (at least 8 characters).
4. Submit the form.  
   - If the email is already registered, you’ll see a message to **sign in** instead.

Creating an account gives you an **app login**. It does **not** create a **parish registry** record.

### Sign in

1. Click **Sign in** in the top bar (or on the home page).
2. Enter your **email** and **password**.
3. After a successful sign-in:
   - **Administrators** are usually taken to **Parish registry** first (you can open any other area from the top menu).
   - **Other roles** are taken to **Profile** first.

If you were signed out, inactive, or your session expired, the sign-in page may show a short reason (for example session expired or account inactive).

### What you see after signing in

- **Admins** usually land on the **Parish registry** page.
- **Members / leaders** usually land on their **Profile** page.

From there, use the **top navigation bar** to move around the system.

### Sign out

Click **Log out** in the top-right area of the header.

---

## Navigation overview

When you are signed in, the **top navigation** typically includes:

| Link | Who | What it’s for |
|------|-----|----------------|
| **Profile** | Everyone | Your app profile (name, contact, SMS/WhatsApp preferences). |
| **Events** | Everyone | Event list and event detail. |
| **Notifications** | Everyone | Your inbox; admins also send notifications and run due reminders. |
| **Ministries** | Everyone | Admins manage all ministries; others see **my** ministries. |
| **Volunteers** | Everyone | Your assignments; admins also manage volunteer **roles**. |
| **Dashboard** | **Admins only** | Summary counts and reports (app users, events, attendance, volunteers, notification stats). |
| **Exports** | **Admins only** | CSV downloads and print views for **operational** data. |
| **Church settings** | **Admins only** | Church name and contact details used on print/exports. |
| **Parish registry** | **Admins only** | Official parish records (separate from logins). |
| **App users** | **Admins only** | Accounts that can sign in to Shepherd. |

Click the **Shepherd** name/logo on the left to return to the **home** page.

---

## Important concepts: Parish Registry vs App Users

| Concept | What it means |
|--------|----------------|
| **App user** | Someone with an email/password who can **sign in**. Operational features primarily use **app users (people with logins)** — including events, attendance, volunteers, and notifications. These are the people the system actively interacts with day to day.|
| **Parish registry** | **Official church office records** (membership status, sacramental fields, registration numbers, etc.). Maintained on the **Parish registry** pages. |
| **They are separate** | Adding or editing a **registry** record does **not** create a **login**. Linking a login to a registry record is optional and done by admins when needed. |
| **Exports** | The **Exports** page is for **operational** CSV/print: attendance, volunteers, **app users**. **Parish registry** CSV and print are started from the **Parish registry** page so filters apply there. |

---

## User guide — normal members and leaders

### Profile

1. Click **Profile** in the top bar.
2. Review or edit:
   - **Full name**
   - **Phone number** and **contact email** (used for how the church reaches you in the app)
   - **Address** (optional)
   - **WhatsApp** / **SMS** toggles and **preferred channel** (how you want to receive external messages when the church sends them)

3. Click **Save** (or the primary save action on the page) to store changes.

Your profile is your **app account** profile, not the parish registry card.

### Events (member view)

1. Click **Events** in the top bar.
2. Open an event by clicking its **title** or link.
3. On the event page you can see event details appropriate to your role.
4. **Volunteer assignments** for **you** and **your attendance** for that event appear in the member-oriented sections (not the full admin roster).

You **cannot** create events, edit all event fields, manage everyone’s attendance, or assign volunteers unless you are an **admin** (those controls are on the same route for administrators only).

### Volunteers (my assignments)

1. Click **Volunteers** in the top bar.
2. Find **your** upcoming (or listed) assignments.
3. Use links to open the related **event** when available.

Admins see extra tools on this page to define **volunteer roles** (labels like “Usher”, “Reader”, etc.).

### Ministries

1. Click **Ministries** in the top bar.
2. If you are **not** an admin, you’ll see ministries **you** are associated with (“my” ministries).
3. Open a ministry to see more detail if the page provides links.

Admins see a searchable list of **all** ministries and can **create** new ministries from this area.

On long **Ministries** screens, **collapsible sections** may group the create form, search, and list so the page is easier to scan.

### Notifications — your inbox

1. Click **Notifications** in the top bar.
2. Scroll to **Your inbox**.
3. Each message shows title, time, and read/unread state.
4. To mark **one** message as read, use **Mark read** on that row.
5. To clear unread quickly, use **Mark all read** (if shown).

The header bell area shows an **unread count** while you use the app; the list may **refresh on its own** every short interval so new messages appear.

**Sending** notifications is **admin-only** (see below). Members only **receive** them (in-app, and SMS/WhatsApp when the church sends through those channels and your profile allows it).

> **Important:**  
> Notifications are always delivered **in-app**.  
> SMS and WhatsApp are **additional channels** and depend on:
> - your phone number being set in **Profile**
> - your notification preferences being enabled
> - your parish having those channels configured

### What normal users cannot access

If you open an admin-only URL (for example **Parish registry** or **App users**), Shepherd may redirect you to **Profile** with a notice that those areas are **limited to administrators**.

---

## User guide — parish administrators

### After you sign in

- You may land on **Parish registry** first; use the top menu to open **Dashboard**, **Events**, etc.

### Dashboard

1. Click **Dashboard** in the top bar.
2. Review **Overview** statistics (app users, upcoming events, volunteer assignments, unread in-app messages, ministries).
3. Scroll through **Attendance by event**, **Top volunteers**, and **Notifications & delivery** (including SMS and WhatsApp attempt/failure summaries).

Long dashboard areas may use **collapsible sections** — you can expand or hide blocks (for example overview vs. detail sections) to scan the page more easily without changing the underlying numbers or lists.

The dashboard describes **operational** data. It is **not** a parish registry report.

### Church settings (branding for print and exports)

1. Click **Church settings** in the top bar.
2. Enter **Church name** (required), optional **short name**, **address**, **phone**, and **email**.
3. Click **Save**.

This information can appear at the top of **print** layouts and influence how exports are labelled. Keeping it accurate makes PDFs and printouts look professional.

### Parish registry — list, filters, exports

1. Click **Parish registry** in the top bar.
2. **Registry summary** cards show totals and breakdowns (membership status, demographics, sacramental/marital summaries — as shown on screen).
3. **Filter & export**:
   - Set filters (search, membership status, gender, sacramental flags, age band, etc.).
   - **Date of birth range** — optional **from** and **to** dates to find members whose date of birth falls in that range (both ends are optional; use validation messages if the range is invalid).
   - **Sacramental date ranges** — optional **from** and **to** dates for **baptism**, **first communion**, **confirmation**, and **marriage** (filter by when each sacrament occurred, not by place).
   - **Saved filters** — after you **Apply filters** at least once, you can **save** the current filter set as a **named preset** for later. Open a saved preset to reload those filters; you can **rename** or **remove** presets you no longer need.
   - **Reset filters** — clears the filter fields to their defaults (you can then **Apply filters** again or adjust before applying).
   - Click **Apply filters** when you are ready to search with the criteria on screen.
   - **Download CSV** — downloads a file matching the **current** applied filters.
   - **Open print view** — opens a printable page; use the browser’s **Print** dialog and choose **Save as PDF** if you need a file.

   The registry page groups major blocks (for example **summary**, **filters**, **saved filters**, **results**) into **collapsible sections**. Expanding or collapsing a section only changes what you see on screen — it does not change saved data or filter logic.

4. **Add** a record: click **Add member record** (or equivalent) and complete the form.

**Registration numbers**

- You may **leave Registration # blank**. Shepherd assigns the next number in the order **year + sequence** (for example `2026-0001`).
- You may **enter** a number manually if the parish needs a specific value; duplicates are blocked with a clear message.
- Registration numbers are **unique**.  
- If you enter a number that already exists, Shepherd will show an error and ask you to choose another.

5. **Edit** a record: click a person’s **name** in the table, change fields, then **Save changes**.

**Where registry exports live**

- Parish registry CSV and print use the **Parish registry** page filters.
- The separate **Exports** page does **not** include parish registry (it explains that registry export is from **Parish registry**).

### App users

1. Click **App users** in the top bar.
2. Search or filter the list.
3. Open a user to view or adjust account-oriented details (as the user detail page provides).

These are **login accounts**, not the same as registry rows.

### Events — create and manage

1. Click **Events** in the top bar.
2. As an admin, use the **create event** form: title, type, visibility, location, ministry (optional), start/end times, active flag.
3. Submit to create the event.
4. Open an event from the list.

On long admin screens (list, filters, and event detail), Shepherd may show **collapsible sections** so you can focus on one block at a time — for example **create event**, **search & filter**, and the **events list**, or on an event page **edit event**, **volunteer scheduling**, **event reminders**, and **attendance**.

**On the event detail page (admin)**

- **Edit** event fields and save.
- **Attendance**: set **present**, **absent**, or **excused** for eligible app users (per row).
- **Volunteers**: choose an app user and role, assign; edit notes where available.
- **Event reminders**:
  - Choose who the reminder applies to (for example event volunteers or ministry members).
  - Choose timing (presets such as 1 hour / 24 hours / 7 days before, or a custom offset where offered).
  - Choose channels: **in-app**, **SMS**, **WhatsApp** as needed.
  - Click **Add reminder** to save a rule.
  - Use **Run due reminders now** to process anything that is **due now** without waiting for the next automatic run (the page explains this).

Members do not see the full admin sections; they see their own attendance/volunteer slice.

### Volunteers — roles (admin)

1. Click **Volunteers** in the top bar.
2. In the **volunteer roles** section, create or edit roles (name, description, ministry link as the form allows).

The **Volunteers** page may use **collapsible sections** (for example **my assignments** and **volunteer roles**) on long screens.

Roles are used when assigning people on event pages.

### Notifications — send messages (admin)

1. Click **Notifications** in the top bar.

The notifications page may use **collapsible sections** for areas such as **send notification**, **your inbox**, and other blocks so you can expand only what you need.

**Event reminders (global button)**

- At the top, **Run due reminders now** runs **all** reminder rules that are currently due (not only one event). The screen shows a short summary after it runs.

**Send notification**

2. Under **Send notification**, enter **Title** and **Body**.
3. Pick a **Category** (general, event, volunteer, ministry, system).
4. Under **Delivery channels**, tick **In-app**, **SMS**, and/or **WhatsApp** as appropriate.  
   - SMS/WhatsApp use the **phone number** on each recipient’s **Profile**.
5. Choose **Audience**:
   - **Specific people** — search by name, email, or phone; add people to the list.
   - **Everyone in a ministry** — pick a ministry.
   - **Volunteers for an event** — pick an event.
6. Submit/send using the page’s primary button (for example **Send notification**).

**Sent notifications**

- Admins can review **sent** notifications and open a **detail** view for delivery information where the app provides it.

### Exports (operational only)

1. Click **Exports** in the top bar.
2. Read the note: **PDF** is produced via the browser (**Print → Save as PDF**), not by a separate “download PDF” file from the server.
3. The **Exports** page may show **Attendance**, **Volunteers**, and **App users** as **collapsible sections** — open the section you need, then use **Download CSV** or **Open print view** there.
4. For **Attendance**, **Volunteers**, or **App users**:
   - Optionally pick event, ministry, date range, or user filters as shown.
   - Click **Download CSV** to save a spreadsheet.
   - Click **Open print view** to open a print-ready page in a new tab; then use **Print or save as PDF** in that tab.

**Parish registry** export is **not** on this screen; use **Parish registry** instead.

### Print / Save as PDF (all export types that use print view)

1. Start from **Exports** or **Parish registry** → **Open print view**.
2. When the print page opens, use **Print or save as PDF** (or your browser’s print).
3. In the print dialog, choose **Save as PDF** if you want a file.

Church details from **Church settings** can appear at the top of the printed document when configured.

---

## Page-by-page quick reference

| Page | Path (typical) | Who |
|------|----------------|-----|
| Home | `/` | Anyone |
| Sign in | `/login` | Anyone |
| Create account | `/register` | Anyone |
| Profile | `/profile` | Signed-in |
| Events | `/events`, `/events/[id]` | Signed-in |
| Notifications | `/notifications` | Signed-in |
| Ministries | `/ministries`, `/ministries/[id]` | Signed-in |
| Volunteers | `/volunteers` | Signed-in |
| Dashboard | `/dashboard` | Admin |
| Exports | `/exports`, print helper `/exports/print` | Admin |
| Church settings | `/settings/church` | Admin |
| Parish registry | `/members`, `/members/new`, `/members/[id]` | Admin |
| App users | `/users`, `/users/[id]` | Admin |

---

## Common tasks (cheat sheet)

| Task | Steps |
|------|--------|
| Register for an account | **Create account** → fill form → submit. |
| Update my phone for SMS/WhatsApp | **Profile** → edit phone / toggles → **Save**. |
| See my volunteer roles | **Volunteers** or open the **event** linked from there. |
| See my ministries | **Ministries**. |
| Read notifications | **Notifications** → **Your inbox** → **Mark read** or **Mark all read**. |
| Create a registry record | **Parish registry** → **Add member record** → save (leave Registration # blank to auto-number). |
| Export filtered registry | **Parish registry** → set filters (including date ranges or a **saved** preset) → **Apply** → **Download CSV** or **Open print view**. |
| Create an event | **Events** → fill admin create form → open event to verify. |
| Assign a volunteer | Open **event** (admin) → **Volunteers** section → pick user and role → assign. |
| Record attendance | Open **event** (admin) → **Attendance** → set status per person. |
| Add an event reminder | Open **event** (admin) → **Event reminders** → fill rule → **Add reminder**. |
| Send due reminders now | **Notifications** (admin) → **Run due reminders now**, **or** open an **event** and use **Run due reminders now** for context-specific copy. |
| Send an announcement | **Notifications** (admin) → **Send notification** → audience + channels → send. |
| Download attendance CSV | **Exports** → Attendance section → **Download CSV**. |
| Save a printout as PDF | **Open print view** → browser **Print** → **Save as PDF**. |
| Set church name on printouts | **Church settings** → save **Church name** and contact fields. |

---
## Example workflow: Preparing for a Sunday service

1. Create an event  
   → Go to **Events** → create the service event.

2. Assign volunteers  
   → Open the event → go to **Volunteers** → assign roles (e.g. usher, reader).

3. Add reminders  
   → In the event → **Event reminders** → add a reminder (e.g. 24 hours before).

4. Run reminders  
   → On the day → click **Run due reminders now**.

5. Record attendance  
   → During/after the event → update attendance statuses.

6. Export results  
   → Go to **Exports** → download attendance CSV or print.

This is a typical weekly workflow for administrators.

---

## Tips and troubleshooting

- **“Administrators only” or redirect to Profile** — You opened an admin page with a non-admin account. Ask an admin to either promote your role or complete the task for you.
- **SMS/WhatsApp not received** — Check **Profile** phone number, toggles, and preferred channel. Admins should confirm the church’s messaging setup with whoever manages Shepherd technically.
- **Duplicate registration number** — Use a unique value or leave the field blank for auto-assignment; the app will explain if a number is already used.
- **Session expired** — Sign in again from **Sign in**; unsaved work on a page may be lost.
- **Inactive account** — The sign-in page may say the account is inactive; an admin must reactivate or create a new account per parish policy.

---

## Current limitations (practical)

- **Roles:** Day-to-day power features are aimed at **admins**; other roles use member-facing views.
- **PDFs:** There is no separate “Download PDF” for exports — use **print view** and **Save as PDF** in the browser.
- **Registry vs login:** Parish registry does **not** auto-create app accounts.
- **Exports page:** Operational exports only; **parish registry** exporting is on the **Parish registry** page.
- **Dashboard:** Admin-only; it does not replace detailed registry reporting.

---

## Glossary

| Term | Meaning |
|------|---------|
| **App user** | A person with a Shepherd **login**. |
| **Parish registry** | Official parish record for a person — may exist **without** a login. |
| **Operational** | Day-to-day workflows tied to **events**, **attendance**, **volunteers**, **notifications** — uses app identities. |
| **In-app notification** | Message visible in Shepherd’s **Notifications** inbox. |
| **Reminder rule** | A scheduled rule on an **event** that sends messages before the event starts (when due and when processed). |

---

## Shepherd name

The product is branded **Shepherd** in the app (title, logo, and home page). Your parish may still refer to it in older documents under another name — in the software, look for **Shepherd** in the header.

---

*This guide reflects the Shepherd application structure and wording as implemented in the product codebase. If your parish customizes URLs or hosting, replace “open Shepherd in your browser” with the address your administrator gives you.*
