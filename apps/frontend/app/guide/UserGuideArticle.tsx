/**
 * Handbook body — wording mirrors repository root USER_GUIDE.md (canonical source).
 * Update both when the guide changes.
 */
export default function UserGuideArticle() {
  return (
    <article className="space-y-10 text-base leading-relaxed text-slate-800 print:space-y-8">
      <header className="space-y-3 border-b border-slate-200 pb-8 print:border-slate-300">
        <p className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">Shepherd — User Guide</p>
        <p>
          <strong>Shepherd</strong> is the church management workspace your parish uses for day-to-day operations:
          events, volunteering, attendance, ministries, notifications (including SMS and WhatsApp where configured),
          and reporting. This guide explains how to use the <strong>current</strong> Shepherd web app from a parish{" "}
          <strong>member</strong> or <strong>administrator</strong> perspective.
        </p>
        <blockquote className="border-l-4 border-indigo-200 pl-4 text-slate-700">
          <p className="font-semibold text-slate-900">This is an end-user handbook.</p>
          <p className="mt-1">
            It is not developer documentation, an API reference, or a technical architecture document.
          </p>
        </blockquote>
      </header>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="purpose-of-shepherd" className="scroll-mt-28 space-y-4">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">Purpose of Shepherd</h2>
        <p>Shepherd helps your church:</p>
        <ul className="list-disc space-y-2 pl-6">
          <li>
            <strong>Stay organised</strong> — events, ministries, volunteers, and reminders in one place.
          </li>
          <li>
            <strong>Communicate</strong> — messages inside the app, and (when set up) by SMS or WhatsApp to people who
            use the app.
          </li>
          <li>
            <strong>Separate two kinds of records</strong> — <strong>operational</strong> work uses{" "}
            <strong>app users</strong> (people with logins). <strong>Official parish registry</strong> records are
            maintained separately and do <strong>not</strong> automatically create logins.
          </li>
        </ul>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="how-shepherd-is-organised-quick-overview" className="scroll-mt-28 space-y-4">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">How Shepherd is organised (quick overview)</h2>
        <p>Shepherd is organised into two main areas:</p>
        <ol className="list-decimal space-y-4 pl-6">
          <li>
            <strong>Operational area (day-to-day work)</strong>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>Events</li>
              <li>Volunteers</li>
              <li>Attendance</li>
              <li>Notifications</li>
              <li>Dashboard, Exports, and Audit log (admin)</li>
            </ul>
            <p className="mt-2">These features work with <strong>App users (people who can log in)</strong>.</p>
          </li>
          <li>
            <strong>Parish registry (official records)</strong>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>Membership records</li>
              <li>Sacramental information</li>
              <li>Registration numbers</li>
              <li>Demographic reporting</li>
            </ul>
            <p className="mt-2">
              These records are <strong>separate from login accounts</strong> and are managed by administrators.
            </p>
          </li>
        </ol>
        <p>If you remember only one thing:</p>
        <blockquote className="border-l-4 border-slate-200 pl-4 text-slate-800">
          <p>
            <strong>App users = people who use the system</strong>
          </p>
          <p className="mt-2">
            <strong>Parish registry = official church records</strong>
          </p>
        </blockquote>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="how-the-system-is-structured" className="scroll-mt-28 space-y-4">
        <h3 className="text-lg font-semibold text-slate-900">How the system is structured</h3>
        <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-slate-50 p-4 font-mono text-xs leading-relaxed text-slate-800 sm:text-sm">
          {`Parish Registry (official records)
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

Linking a registry record to a login is optional and done by administrators.`}
        </pre>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="who-uses-shepherd" className="scroll-mt-28 space-y-4">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">Who uses Shepherd?</h2>
        <div className="overflow-x-auto print:overflow-visible">
          <table className="w-full min-w-[20rem] border-collapse border border-slate-200 text-left text-sm">
            <thead>
              <tr className="bg-slate-50">
                <th className="border border-slate-200 px-3 py-2 font-semibold text-slate-900">Who</th>
                <th className="border border-slate-200 px-3 py-2 font-semibold text-slate-900">Typical use</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">
                  <strong>Members and volunteers</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  Sign in, update profile, view events, see volunteer roles, mark notifications read.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">
                  <strong>Parish administrators</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  Everything members can do, plus dashboard, exports, parish registry, app users, full
                  event/volunteer/attendance tools, sending notifications, church settings, and reminder tools.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="roles-in-the-app" className="scroll-mt-28 space-y-4">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">Roles in the app</h2>
        <p>
          After you sign in, the top bar shows your <strong>name</strong> and <strong>role</strong> (for example
          &quot;admin&quot;, &quot;group leader&quot;, or &quot;member&quot;).
        </p>
        <ul className="list-disc space-y-3 pl-6">
          <li>
            <strong>Admin</strong>
            <br />
            Full access to Shepherd&apos;s administrative areas: <strong>Dashboard</strong>, <strong>Exports</strong>,{" "}
            <strong>Church settings</strong>, <strong>Audit log</strong>, <strong>Parish registry</strong>,{" "}
            <strong>App users</strong>, and the full <strong>Events</strong> tools (editing, attendance, volunteers, event
            reminders).
          </li>
          <li>
            <strong>Group leader</strong> and <strong>Member</strong>
            <br />
            These roles use the same <strong>navigation</strong> as each other for admin-only links: they{" "}
            <strong>do not</strong> see Dashboard, Exports, Church settings, Audit log, Parish registry, or App users in
            the menu.
            They <strong>do</strong> see Profile, Events, Notifications, Ministries, and Volunteers.
          </li>
        </ul>
        <blockquote className="border-l-4 border-amber-200 pl-4 text-slate-800">
          <p>
            <strong>Note:</strong> Shepherd&apos;s interface treats only <strong>admin</strong> as a powerful role
            today. If you need administrative work done, your parish should use an <strong>admin</strong> account.
          </p>
        </blockquote>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="getting-started" className="scroll-mt-28 space-y-6">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">Getting started</h2>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Create an account</h3>
          <ol className="list-decimal space-y-2 pl-6">
            <li>Open Shepherd in your web browser (your parish will give you the address).</li>
            <li>
              Click <strong>Create account</strong> in the top bar (or on the home page).
            </li>
            <li>
              Enter your <strong>full name</strong>, <strong>email</strong>, and <strong>password</strong> (at least 8
              characters).
            </li>
            <li>
              Submit the form.
              <ul className="mt-2 list-disc pl-5">
                <li>If the email is already registered, you&apos;ll see a message to sign in instead.</li>
              </ul>
            </li>
          </ol>
          <p>
            Creating an account gives you an <strong>app login</strong>. It does <strong>not</strong> create a{" "}
            <strong>parish registry</strong> record.
          </p>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Sign in</h3>
          <ol className="list-decimal space-y-2 pl-6">
            <li>
              Click <strong>Sign in</strong> in the top bar (or on the home page).
            </li>
            <li>
              Enter your <strong>email</strong> and <strong>password</strong>.
            </li>
            <li>
              After a successful sign-in:
              <ul className="mt-2 list-disc pl-5">
                <li>
                  <strong>Administrators</strong> are usually taken to <strong>Parish registry</strong> first (you can
                  open any other area from the top menu).
                </li>
                <li>
                  <strong>Other roles</strong> are taken to <strong>Profile</strong> first.
                </li>
              </ul>
            </li>
          </ol>
          <p>
            If you were signed out, inactive, or your session expired, the sign-in page may show a short reason (for
            example session expired or account inactive).
          </p>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">What you see after signing in</h3>
          <ul className="list-disc space-y-2 pl-6">
            <li>
              <strong>Admins</strong> usually land on the <strong>Parish registry</strong> page.
            </li>
            <li>
              <strong>Members / leaders</strong> usually land on their <strong>Profile</strong> page.
            </li>
          </ul>
          <p>
            From there, use the <strong>top navigation bar</strong> to move around the system.
          </p>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Sign out</h3>
          <p>
            Click <strong>Log out</strong> in the top-right area of the header.
          </p>
        </div>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="navigation-overview" className="scroll-mt-28 space-y-4">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">Navigation overview</h2>
        <p>
          When you are signed in, the <strong>top navigation</strong> typically includes:
        </p>
        <div className="overflow-x-auto print:overflow-visible">
          <table className="w-full min-w-[36rem] border-collapse border border-slate-200 text-left text-sm">
            <thead>
              <tr className="bg-slate-50">
                <th className="border border-slate-200 px-3 py-2 font-semibold text-slate-900">Link</th>
                <th className="border border-slate-200 px-3 py-2 font-semibold text-slate-900">Who</th>
                <th className="border border-slate-200 px-3 py-2 font-semibold text-slate-900">What it&apos;s for</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Profile</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">Everyone</td>
                <td className="border border-slate-200 px-3 py-2">
                  Your app profile (name, contact, SMS/WhatsApp preferences).
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Events</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">Everyone</td>
                <td className="border border-slate-200 px-3 py-2">Event list and event detail.</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Notifications</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">Everyone</td>
                <td className="border border-slate-200 px-3 py-2">
                  Your inbox; admins also send notifications and run due reminders.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Ministries</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">Everyone</td>
                <td className="border border-slate-200 px-3 py-2">
                  Admins manage all ministries; others see <strong>my</strong> ministries.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Volunteers</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">Everyone</td>
                <td className="border border-slate-200 px-3 py-2">
                  Your assignments; admins also manage volunteer <strong>roles</strong>.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Dashboard</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Admins only</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  Summary counts and reports (app users, events, attendance, volunteers, notification stats).
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Exports</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Admins only</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  CSV downloads and print views for <strong>operational</strong> data.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Church settings</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Admins only</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  Church name and contact details used on print/exports.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Audit log</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Admins only</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  History of important admin actions (who, what, when); filter and expand for technical detail.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Parish registry</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Admins only</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  Official parish records (separate from logins).
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>App users</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Admins only</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">Accounts that can sign in to Shepherd.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p>
          Click the <strong>Shepherd</strong> name/logo on the left to return to the <strong>home</strong> page.
        </p>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="important-concepts-parish-registry-vs-app-users" className="scroll-mt-28 space-y-4">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">
          Important concepts: Parish Registry vs App Users
        </h2>
        <div className="overflow-x-auto print:overflow-visible">
          <table className="w-full min-w-[24rem] border-collapse border border-slate-200 text-left text-sm">
            <thead>
              <tr className="bg-slate-50">
                <th className="border border-slate-200 px-3 py-2 font-semibold text-slate-900">Concept</th>
                <th className="border border-slate-200 px-3 py-2 font-semibold text-slate-900">What it means</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">
                  <strong>App user</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  Someone with an email/password who can <strong>sign in</strong>. Operational features primarily use{" "}
                  <strong>app users (people with logins)</strong> — including events, attendance, volunteers, and
                  notifications. These are the people the system actively interacts with day to day.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">
                  <strong>Parish registry</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Official church office records</strong> (membership status, sacramental fields, registration
                  numbers, etc.). Maintained on the <strong>Parish registry</strong> pages.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">
                  <strong>They are separate</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  Adding or editing a <strong>registry</strong> record does <strong>not</strong> create a{" "}
                  <strong>login</strong>. Linking a login to a registry record is optional and done by admins when needed.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">
                  <strong>Exports</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  The <strong>Exports</strong> page is for <strong>operational</strong> CSV/print: attendance,
                  volunteers, <strong>app users</strong>. <strong>Parish registry</strong> CSV and print are started from
                  the <strong>Parish registry</strong> page so filters apply there.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="user-guide-normal-members-and-leaders" className="scroll-mt-28 space-y-8">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">User guide — normal members and leaders</h2>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Profile</h3>
          <ol className="list-decimal space-y-2 pl-6">
            <li>
              Click <strong>Profile</strong> in the top bar.
            </li>
            <li>
              Review or edit:
              <ul className="mt-2 list-disc pl-5">
                <li>
                  <strong>Full name</strong>
                </li>
                <li>
                  <strong>Phone number</strong> and <strong>contact email</strong> (used for how the church reaches you
                  in the app)
                </li>
                <li>
                  <strong>Address</strong> (optional)
                </li>
                <li>
                  <strong>WhatsApp</strong> / <strong>SMS</strong> toggles and <strong>preferred channel</strong> (how
                  you want to receive external messages when the church sends them)
                </li>
              </ul>
            </li>
            <li>
              Click <strong>Save</strong> (or the primary save action on the page) to store changes.
            </li>
          </ol>
          <p>Your profile is your <strong>app account</strong> profile, not the parish registry card.</p>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Events (member view)</h3>
          <ol className="list-decimal space-y-2 pl-6">
            <li>
              Click <strong>Events</strong> in the top bar.
            </li>
            <li>
              Open an event by clicking its <strong>title</strong> or link.
            </li>
            <li>On the event page you can see event details appropriate to your role.</li>
            <li>
              <strong>Volunteer assignments</strong> for <strong>you</strong> and <strong>your attendance</strong> for
              that event appear in the member-oriented sections (not the full admin roster).
            </li>
          </ol>
          <p>
            You <strong>cannot</strong> create events, edit all event fields, manage everyone&apos;s attendance, or assign
            volunteers unless you are an <strong>admin</strong> (those controls are on the same route for administrators
            only).
          </p>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Volunteers (my assignments)</h3>
          <ol className="list-decimal space-y-2 pl-6">
            <li>
              Click <strong>Volunteers</strong> in the top bar.
            </li>
            <li>
              Find <strong>your</strong> upcoming (or listed) assignments.
            </li>
            <li>
              Use links to open the related <strong>event</strong> when available.
            </li>
          </ol>
          <p>Admins see extra tools on this page to define volunteer roles (labels like &quot;Usher&quot;, &quot;Reader&quot;, etc.).</p>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Ministries</h3>
          <ol className="list-decimal space-y-2 pl-6">
            <li>
              Click <strong>Ministries</strong> in the top bar.
            </li>
            <li>
              If you are <strong>not</strong> an admin, you&apos;ll see ministries <strong>you</strong> are associated
              with (&quot;my&quot; ministries).
            </li>
            <li>Open a ministry to see more detail if the page provides links.</li>
          </ol>
          <p>Admins see a searchable list of all ministries and can create new ministries from this area.</p>
          <p>
            On long <strong>Ministries</strong> screens, <strong>collapsible sections</strong> may group the create form,
            search, and list so the page is easier to scan.
          </p>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Notifications — your inbox</h3>
          <ol className="list-decimal space-y-2 pl-6">
            <li>
              Click <strong>Notifications</strong> in the top bar.
            </li>
            <li>
              Scroll to <strong>Your inbox</strong>.
            </li>
            <li>Each message shows title, time, and read/unread state.</li>
            <li>
              To mark <strong>one</strong> message as read, use <strong>Mark read</strong> on that row.
            </li>
            <li>
              To clear unread quickly, use <strong>Mark all read</strong> (if shown).
            </li>
          </ol>
          <p>
            The header bell area shows an <strong>unread count</strong> while you use the app; the list may refresh on its
            own every short interval so new messages appear.
          </p>
          <p>
            <strong>Sending</strong> notifications is <strong>admin-only</strong> (see below). Members only receive them
            (in-app, and SMS/WhatsApp when the church sends through those channels and your profile allows it).
          </p>
          <blockquote className="border-l-4 border-indigo-200 pl-4 text-slate-800">
            <p>
              <strong>Important:</strong>
            </p>
            <p className="mt-2">Notifications are always delivered in-app.</p>
            <p className="mt-2">
              SMS and WhatsApp are <strong>additional channels</strong> and depend on:
            </p>
            <ul className="mt-2 list-disc pl-6">
              <li>your phone number being set in Profile</li>
              <li>your notification preferences being enabled</li>
              <li>your parish having those channels configured</li>
            </ul>
          </blockquote>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">What normal users cannot access</h3>
          <p>
            If you open an admin-only URL (for example <strong>Parish registry</strong> or <strong>App users</strong>),
            Shepherd may redirect you to <strong>Profile</strong> with a notice that those areas are limited to
            administrators.
          </p>
        </div>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="user-guide-parish-administrators" className="scroll-mt-28 space-y-8">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">User guide — parish administrators</h2>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">After you sign in</h3>
          <ul className="list-disc space-y-2 pl-6">
            <li>
              You may land on <strong>Parish registry</strong> first; use the top menu to open <strong>Dashboard</strong>,{" "}
              <strong>Events</strong>, etc.
            </li>
          </ul>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Dashboard</h3>
          <ol className="list-decimal space-y-2 pl-6">
            <li>
              Click <strong>Dashboard</strong> in the top bar.
            </li>
            <li>
              Review <strong>Overview</strong> statistics (app users, upcoming events, volunteer assignments, unread
              in-app messages, ministries).
            </li>
            <li>
              Scroll through <strong>Attendance by event</strong>, <strong>Top volunteers</strong>, and{" "}
              <strong>Notifications &amp; delivery</strong> (including SMS and WhatsApp attempt/failure summaries).
            </li>
          </ol>
          <p>
            Long dashboard areas may use <strong>collapsible sections</strong> — you can expand or hide blocks (for
            example overview vs. detail sections) to scan the page more easily without changing the underlying numbers or
            lists.
          </p>
          <p>
            The dashboard describes <strong>operational</strong> data. It is <strong>not</strong> a parish registry
            report.
          </p>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Audit log</h3>
          <ol className="list-decimal space-y-2 pl-6">
            <li>
              Click <strong>Audit log</strong> in the top bar (with other admin tools, for example after{" "}
              <strong>Church settings</strong>).
            </li>
            <li>
              The table shows <strong>when</strong> something happened, <strong>who</strong> did it (name and email when
              stored—otherwise email or another identifier), a short plain-language <strong>what</strong> label,{" "}
              <strong>context</strong> where helpful, and <strong>details</strong> (a readable summary of the action).
            </li>
            <li>
              Use <strong>Apply</strong> to filter by <strong>action code</strong> (the same short codes the app
              stores—shown in the filter hint) and optional <strong>date/time</strong> range. Use pagination when the list
              is long.
            </li>
            <li>
              Expand a row (<strong>▼</strong>) to open <strong>technical details</strong> (for example internal IDs and
              metadata) if you need them; day-to-day review usually stays in the main table.
            </li>
          </ol>
          <p>
            The audit log supports accountability and traceability across many admin workflows. It is not a full
            analytics or compliance platform. Very old rows may not include a stored display name for{" "}
            <strong>who</strong>.
          </p>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Church settings (branding for print and exports)</h3>
          <ol className="list-decimal space-y-2 pl-6">
            <li>
              Click <strong>Church settings</strong> in the top bar.
            </li>
            <li>
              Enter <strong>Church name</strong> (required), optional <strong>short name</strong>, <strong>address</strong>,{" "}
              <strong>phone</strong>, and <strong>email</strong>.
            </li>
            <li>
              Click <strong>Save</strong>.
            </li>
          </ol>
          <p>
            This information can appear at the top of print layouts and influence how exports are labelled. Keeping it
            accurate makes PDFs and printouts look professional.
          </p>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Parish registry — list, filters, exports</h3>
          <ol className="list-decimal space-y-4 pl-6">
            <li>
              Click <strong>Parish registry</strong> in the top bar.
            </li>
            <li>
              <strong>Registry summary</strong> cards show totals and breakdowns (membership status, demographics,
              sacramental/marital summaries — as shown on screen).
            </li>
            <li>
              <strong>Filter &amp; export</strong>:
              <ul className="mt-2 list-disc space-y-2 pl-5">
                <li>Set filters (search, membership status, gender, sacramental flags, age band, etc.).</li>
                <li>
                  <strong>Date of birth range</strong> — optional <strong>from</strong> and <strong>to</strong> dates to
                  find members whose date of birth falls in that range (both ends are optional; use validation messages
                  if the range is invalid).
                </li>
                <li>
                  <strong>Sacramental date ranges</strong> — optional <strong>from</strong> and <strong>to</strong>{" "}
                  dates for <strong>baptism</strong>, <strong>first communion</strong>, <strong>confirmation</strong>,
                  and <strong>marriage</strong> (filter by when each sacrament occurred, not by place).
                </li>
                <li>
                  <strong>Saved filters</strong> — after you <strong>Apply filters</strong> at least once, you can{" "}
                  <strong>save</strong> the current filter set as a <strong>named preset</strong> for later. Open a saved
                  preset to reload those filters; you can <strong>rename</strong> or <strong>remove</strong> presets you
                  no longer need.
                </li>
                <li>
                  <strong>Reset filters</strong> — clears the filter fields to their defaults (you can then{" "}
                  <strong>Apply filters</strong> again or adjust before applying).
                </li>
                <li>
                  Click <strong>Apply filters</strong> when you are ready to search with the criteria on screen.
                </li>
                <li>
                  <strong>Download CSV</strong> — downloads a file matching the <strong>current</strong> applied filters.
                </li>
                <li>
                  <strong>Open print view</strong> — opens a printable page; use the browser&apos;s <strong>Print</strong>{" "}
                  dialog and choose <strong>Save as PDF</strong> if you need a file.
                </li>
              </ul>
              <p className="mt-3 text-slate-800">
                The registry page groups major blocks (for example <strong>summary</strong>, <strong>filters</strong>,{" "}
                <strong>saved filters</strong>, <strong>results</strong>) into <strong>collapsible sections</strong>.
                Expanding or collapsing a section only changes what you see on screen — it does not change saved data or
                filter logic.
              </p>
            </li>
            <li>
              <strong>Add</strong> a record: click <strong>Add member record</strong> (or equivalent) and complete the
              form.
            </li>
          </ol>
          <div className="space-y-2">
            <p>
              <strong>Registration numbers</strong>
            </p>
            <ul className="list-disc space-y-2 pl-6">
              <li>
                You may <strong>leave Registration # blank</strong>. Shepherd assigns the next number in the order{" "}
                <strong>year + sequence</strong> (for example <code className="rounded bg-slate-100 px-1">2026-0001</code>
                ).
              </li>
              <li>
                You may <strong>enter</strong> a number manually if the parish needs a specific value; duplicates are
                blocked with a clear message.
              </li>
              <li>
                Registration numbers are <strong>unique</strong>.
              </li>
              <li>
                If you enter a number that already exists, Shepherd will show an error and ask you to choose another.
              </li>
            </ul>
          </div>
          <ol className="list-decimal space-y-2 pl-6" start={5}>
            <li>
              <strong>Edit</strong> a record: click a person&apos;s <strong>name</strong> in the table, change fields,
              then <strong>Save changes</strong>.
            </li>
          </ol>
          <div className="space-y-2">
            <p>
              <strong>Where registry exports live</strong>
            </p>
            <ul className="list-disc space-y-2 pl-6">
              <li>
                Parish registry CSV and print use the <strong>Parish registry</strong> page filters.
              </li>
              <li>
                The separate <strong>Exports</strong> page does <strong>not</strong> include parish registry (it explains
                that registry export is from <strong>Parish registry</strong>).
              </li>
            </ul>
          </div>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">App users</h3>
          <ol className="list-decimal space-y-2 pl-6">
            <li>
              Click <strong>App users</strong> in the top bar.
            </li>
            <li>
              Search or filter the list. Administrators show an <strong>Administrator</strong> badge in the role column.
            </li>
            <li>Open a user to manage their <strong>login account</strong> and app profile fields.</li>
          </ol>
          <p>
            <strong>Multiple administrators:</strong> A parish can (and should) have more than one admin account—each
            staff member who needs full access should use <strong>their own</strong> login. Shared admin passwords are{" "}
            <strong>not</strong> recommended. From a user&apos;s detail page, an admin can <strong>grant administrator access</strong>{" "}
            or <strong>remove administrator access</strong>, subject to safeguards so the system is never left with no active
            administrator. If you see an error about the last administrator, add or promote another admin first.
          </p>
          <p>
            These are <strong>login accounts</strong>, not the same as registry rows.
          </p>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Events — create and manage</h3>
          <ol className="list-decimal space-y-2 pl-6">
            <li>
              Click <strong>Events</strong> in the top bar.
            </li>
            <li>
              As an admin, use the <strong>create event</strong> form: title, type, visibility, location, ministry
              (optional), start/end times, active flag.
            </li>
            <li>Submit to create the event.</li>
            <li>Open an event from the list.</li>
          </ol>
          <p>
            On long admin screens (list, filters, and event detail), Shepherd may show <strong>collapsible sections</strong>{" "}
            so you can focus on one block at a time — for example <strong>create event</strong>,{" "}
            <strong>search &amp; filter</strong>, and the <strong>events list</strong>, or on an event page{" "}
            <strong>edit event</strong>, <strong>volunteer scheduling</strong>, <strong>event reminders</strong>, and{" "}
            <strong>attendance</strong>.
          </p>
          <p>
            <strong>On the event detail page (admin)</strong>
          </p>
          <ul className="list-disc space-y-2 pl-6">
            <li>
              <strong>Edit</strong> event fields and save.
            </li>
            <li>
              <strong>Attendance</strong>: set <strong>present</strong>, <strong>absent</strong>, or{" "}
              <strong>excused</strong> for eligible app users (per row).
            </li>
            <li>
              <strong>Volunteers</strong>: choose an app user and role, assign; edit notes where available.
            </li>
            <li>
              <strong>Event reminders</strong>:
              <ul className="mt-2 list-disc pl-5">
                <li>Choose who the reminder applies to (for example event volunteers or ministry members).</li>
                <li>
                  Choose timing (presets such as 1 hour / 24 hours / 7 days before, or a custom offset where offered).
                </li>
                <li>
                  Choose channels: <strong>in-app</strong>, <strong>SMS</strong>, <strong>WhatsApp</strong> as needed.
                </li>
                <li>
                  Click <strong>Add reminder</strong> to save a rule.
                </li>
                <li>
                  Use <strong>Run due reminders now</strong> to process anything that is <strong>due now</strong> without
                  waiting for the next automatic run (the page explains this).
                </li>
              </ul>
            </li>
          </ul>
          <p>Members do not see the full admin sections; they see their own attendance/volunteer slice.</p>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Volunteers — roles (admin)</h3>
          <ol className="list-decimal space-y-2 pl-6">
            <li>
              Click <strong>Volunteers</strong> in the top bar.
            </li>
            <li>
              In the <strong>volunteer roles</strong> section, create or edit roles (name, description, ministry link as
              the form allows).
            </li>
          </ol>
          <p>
            The <strong>Volunteers</strong> page may use <strong>collapsible sections</strong> (for example{" "}
            <strong>my assignments</strong> and <strong>volunteer roles</strong>) on long screens.
          </p>
          <p>Roles are used when assigning people on event pages.</p>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Notifications — send messages (admin)</h3>
          <ol className="list-decimal space-y-4 pl-6">
            <li>
              Click <strong>Notifications</strong> in the top bar.
            </li>
          </ol>
          <p>
            The notifications page may use <strong>collapsible sections</strong> for areas such as{" "}
            <strong>send notification</strong>, <strong>your inbox</strong>, and other blocks so you can expand only
            what you need.
          </p>
          <p>
            <strong>Event reminders (global button)</strong>
          </p>
          <ul className="list-disc space-y-2 pl-6">
            <li>
              At the top, <strong>Run due reminders now</strong> runs <strong>all</strong> reminder rules that are
              currently due (not only one event). The screen shows a short summary after it runs.
            </li>
          </ul>
          <p>
            <strong>Send notification</strong>
          </p>
          <ol className="list-decimal space-y-2 pl-6" start={2}>
            <li>
              Under <strong>Send notification</strong>, enter <strong>Title</strong> and <strong>Body</strong>.
            </li>
            <li>
              Pick a <strong>Category</strong> (general, event, volunteer, ministry, system).
            </li>
            <li>
              Under <strong>Delivery channels</strong>, tick <strong>In-app</strong>, <strong>SMS</strong>, and/or{" "}
              <strong>WhatsApp</strong> as appropriate.
              <ul className="mt-2 list-disc pl-5">
                <li>
                  SMS/WhatsApp use the <strong>phone number</strong> on each recipient&apos;s <strong>Profile</strong>.
                </li>
              </ul>
            </li>
            <li>
              Choose <strong>Audience</strong>:
              <ul className="mt-2 list-disc pl-5">
                <li>
                  <strong>Specific people</strong> — search by name, email, or phone; add people to the list.
                </li>
                <li>
                  <strong>Everyone in a ministry</strong> — pick a ministry.
                </li>
                <li>
                  <strong>Volunteers for an event</strong> — pick an event.
                </li>
              </ul>
            </li>
            <li>
              Submit/send using the page&apos;s primary button (for example <strong>Send notification</strong>).
            </li>
          </ol>
          <p>
            <strong>Sent notifications</strong>
          </p>
          <ul className="list-disc space-y-2 pl-6">
            <li>
              Admins can review <strong>sent</strong> notifications and open a <strong>detail</strong> view for delivery
              information where the app provides it.
            </li>
          </ul>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Exports (operational only)</h3>
          <ol className="list-decimal space-y-2 pl-6">
            <li>
              Click <strong>Exports</strong> in the top bar.
            </li>
            <li>
              Read the note: <strong>PDF</strong> is produced via the browser (<strong>Print → Save as PDF</strong>), not
              by a separate &quot;download PDF&quot; file from the server.
            </li>
            <li>
              The <strong>Exports</strong> page may show <strong>Attendance</strong>, <strong>Volunteers</strong>, and{" "}
              <strong>App users</strong> as <strong>collapsible sections</strong> — open the section you need, then use{" "}
              <strong>Download CSV</strong> or <strong>Open print view</strong> there.
            </li>
            <li>
              For <strong>Attendance</strong>, <strong>Volunteers</strong>, or <strong>App users</strong>:
              <ul className="mt-2 list-disc pl-5">
                <li>Optionally pick event, ministry, date range, or user filters as shown.</li>
                <li>
                  Click <strong>Download CSV</strong> to save a spreadsheet.
                </li>
                <li>
                  Click <strong>Open print view</strong> to open a print-ready page in a new tab; then use{" "}
                  <strong>Print or save as PDF</strong> in that tab.
                </li>
              </ul>
            </li>
          </ol>
          <p>
            <strong>Parish registry</strong> export is <strong>not</strong> on this screen; use{" "}
            <strong>Parish registry</strong> instead.
          </p>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Print / Save as PDF (all export types that use print view)</h3>
          <ol className="list-decimal space-y-2 pl-6">
            <li>
              Start from <strong>Exports</strong> or <strong>Parish registry</strong> → <strong>Open print view</strong>.
            </li>
            <li>
              When the print page opens, use <strong>Print or save as PDF</strong> (or your browser&apos;s print).
            </li>
            <li>
              In the print dialog, choose <strong>Save as PDF</strong> if you want a file.
            </li>
          </ol>
          <p>
            Church details from <strong>Church settings</strong> can appear at the top of the printed document when
            configured.
          </p>
        </div>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="page-by-page-quick-reference" className="scroll-mt-28 space-y-4">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">Page-by-page quick reference</h2>
        <div className="overflow-x-auto print:overflow-visible">
          <table className="w-full min-w-[28rem] border-collapse border border-slate-200 text-left text-sm">
            <thead>
              <tr className="bg-slate-50">
                <th className="border border-slate-200 px-3 py-2 font-semibold text-slate-900">Page</th>
                <th className="border border-slate-200 px-3 py-2 font-semibold text-slate-900">Path (typical)</th>
                <th className="border border-slate-200 px-3 py-2 font-semibold text-slate-900">Who</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border border-slate-200 px-3 py-2">Home</td>
                <td className="border border-slate-200 px-3 py-2 font-mono text-xs sm:text-sm">/</td>
                <td className="border border-slate-200 px-3 py-2">Anyone</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">Sign in</td>
                <td className="border border-slate-200 px-3 py-2 font-mono text-xs sm:text-sm">/login</td>
                <td className="border border-slate-200 px-3 py-2">Anyone</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">Create account</td>
                <td className="border border-slate-200 px-3 py-2 font-mono text-xs sm:text-sm">/register</td>
                <td className="border border-slate-200 px-3 py-2">Anyone</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">Profile</td>
                <td className="border border-slate-200 px-3 py-2 font-mono text-xs sm:text-sm">/profile</td>
                <td className="border border-slate-200 px-3 py-2">Signed-in</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">Events</td>
                <td className="border border-slate-200 px-3 py-2 font-mono text-xs sm:text-sm">/events, /events/[id]</td>
                <td className="border border-slate-200 px-3 py-2">Signed-in</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">Notifications</td>
                <td className="border border-slate-200 px-3 py-2 font-mono text-xs sm:text-sm">/notifications</td>
                <td className="border border-slate-200 px-3 py-2">Signed-in</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">Ministries</td>
                <td className="border border-slate-200 px-3 py-2 font-mono text-xs sm:text-sm">
                  /ministries, /ministries/[id]
                </td>
                <td className="border border-slate-200 px-3 py-2">Signed-in</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">Volunteers</td>
                <td className="border border-slate-200 px-3 py-2 font-mono text-xs sm:text-sm">/volunteers</td>
                <td className="border border-slate-200 px-3 py-2">Signed-in</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">Dashboard</td>
                <td className="border border-slate-200 px-3 py-2 font-mono text-xs sm:text-sm">/dashboard</td>
                <td className="border border-slate-200 px-3 py-2">Admin</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">Exports</td>
                <td className="border border-slate-200 px-3 py-2 font-mono text-xs sm:text-sm">
                  /exports, print helper /exports/print
                </td>
                <td className="border border-slate-200 px-3 py-2">Admin</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">Church settings</td>
                <td className="border border-slate-200 px-3 py-2 font-mono text-xs sm:text-sm">/settings/church</td>
                <td className="border border-slate-200 px-3 py-2">Admin</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">Audit log</td>
                <td className="border border-slate-200 px-3 py-2 font-mono text-xs sm:text-sm">/audit-logs</td>
                <td className="border border-slate-200 px-3 py-2">Admin</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">Parish registry</td>
                <td className="border border-slate-200 px-3 py-2 font-mono text-xs sm:text-sm">
                  /members, /members/new, /members/[id]
                </td>
                <td className="border border-slate-200 px-3 py-2">Admin</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2">App users</td>
                <td className="border border-slate-200 px-3 py-2 font-mono text-xs sm:text-sm">/users, /users/[id]</td>
                <td className="border border-slate-200 px-3 py-2">Admin</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="common-tasks" className="scroll-mt-28 space-y-4">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">Common tasks (cheat sheet)</h2>
        <div className="overflow-x-auto print:overflow-visible">
          <table className="w-full min-w-[32rem] border-collapse border border-slate-200 text-left text-sm">
            <thead>
              <tr className="bg-slate-50">
                <th className="border border-slate-200 px-3 py-2 font-semibold text-slate-900">Task</th>
                <th className="border border-slate-200 px-3 py-2 font-semibold text-slate-900">Steps</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">Register for an account</td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Create account</strong> → fill form → submit.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">Update my phone for SMS/WhatsApp</td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Profile</strong> → edit phone / toggles → <strong>Save</strong>.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">See my volunteer roles</td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Volunteers</strong> or open the <strong>event</strong> linked from there.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">See my ministries</td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Ministries</strong>.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">Read notifications</td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Notifications</strong> → <strong>Your inbox</strong> → <strong>Mark read</strong> or{" "}
                  <strong>Mark all read</strong>.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">Create a registry record</td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Parish registry</strong> → <strong>Add member record</strong> → save (leave Registration #
                  blank to auto-number).
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">Export filtered registry</td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Parish registry</strong> → set filters (including date ranges or a <strong>saved</strong> preset) →{" "}
                  <strong>Apply</strong> → <strong>Download CSV</strong> or <strong>Open print view</strong>.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">Create an event</td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Events</strong> → fill admin create form → open event to verify.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">Assign a volunteer</td>
                <td className="border border-slate-200 px-3 py-2">
                  Open <strong>event</strong> (admin) → <strong>Volunteers</strong> section → pick user and role → assign.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">Record attendance</td>
                <td className="border border-slate-200 px-3 py-2">
                  Open <strong>event</strong> (admin) → <strong>Attendance</strong> → set status per person.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">Add an event reminder</td>
                <td className="border border-slate-200 px-3 py-2">
                  Open <strong>event</strong> (admin) → <strong>Event reminders</strong> → fill rule →{" "}
                  <strong>Add reminder</strong>.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">Send due reminders now</td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Notifications</strong> (admin) → <strong>Run due reminders now</strong>, <strong>or</strong> open
                  an <strong>event</strong> and use <strong>Run due reminders now</strong> for context-specific copy.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">Send an announcement</td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Notifications</strong> (admin) → <strong>Send notification</strong> → audience + channels →
                  send.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">Download attendance CSV</td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Exports</strong> → Attendance section → <strong>Download CSV</strong>.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">Save a printout as PDF</td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Open print view</strong> → browser <strong>Print</strong> → <strong>Save as PDF</strong>.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">Set church name on printouts</td>
                <td className="border border-slate-200 px-3 py-2">
                  <strong>Church settings</strong> → save <strong>Church name</strong> and contact fields.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="example-workflow-preparing-for-a-sunday-service" className="scroll-mt-28 space-y-4">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">Example workflow: Preparing for a Sunday service</h2>
        <ol className="list-decimal space-y-3 pl-6">
          <li>
            Create an event
            <br />→ Go to <strong>Events</strong> → create the service event.
          </li>
          <li>
            Assign volunteers
            <br />→ Open the event → go to <strong>Volunteers</strong> → assign roles (e.g. usher, reader).
          </li>
          <li>
            Add reminders
            <br />→ In the event → <strong>Event reminders</strong> → add a reminder (e.g. 24 hours before).
          </li>
          <li>
            Run reminders
            <br />→ On the day → click <strong>Run due reminders now</strong>.
          </li>
          <li>
            Record attendance
            <br />→ During/after the event → update attendance statuses.
          </li>
          <li>
            Export results
            <br />→ Go to <strong>Exports</strong> → download attendance CSV or print.
          </li>
        </ol>
        <p>This is a typical weekly workflow for administrators.</p>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="tips-and-troubleshooting" className="scroll-mt-28 space-y-4">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">Tips and troubleshooting</h2>
        <ul className="list-disc space-y-3 pl-6">
          <li>
            <strong>&quot;Administrators only&quot; or redirect to Profile</strong> — You opened an admin page with a
            non-admin account. Ask an admin to either promote your role or complete the task for you.
          </li>
          <li>
            <strong>SMS/WhatsApp not received</strong> — Check <strong>Profile</strong> phone number, toggles, and
            preferred channel. Admins should confirm the church&apos;s messaging setup with whoever manages Shepherd
            technically.
          </li>
          <li>
            <strong>Duplicate registration number</strong> — Use a unique value or leave the field blank for
            auto-assignment; the app will explain if a number is already used.
          </li>
          <li>
            <strong>Session expired</strong> — Sign in again from <strong>Sign in</strong>; unsaved work on a page may be
            lost.
          </li>
          <li>
            <strong>Inactive account</strong> — The sign-in page may say the account is inactive; an admin must
            reactivate or create a new account per parish policy.
          </li>
        </ul>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="current-limitations" className="scroll-mt-28 space-y-4">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">Current limitations (practical)</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>
            <strong>Roles:</strong> Day-to-day power features are aimed at <strong>admins</strong>; other roles use
            member-facing views.
          </li>
          <li>
            <strong>PDFs:</strong> There is no separate &quot;Download PDF&quot; for exports — use <strong>print view</strong>{" "}
            and <strong>Save as PDF</strong> in the browser.
          </li>
          <li>
            <strong>Registry vs login:</strong> Parish registry does <strong>not</strong> auto-create app accounts.
          </li>
          <li>
            <strong>Exports page:</strong> Operational exports only; <strong>parish registry</strong> exporting is on the{" "}
            <strong>Parish registry</strong> page.
          </li>
          <li>
            <strong>Dashboard:</strong> Admin-only; it does not replace detailed registry reporting.
          </li>
        </ul>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="glossary" className="scroll-mt-28 space-y-4">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">Glossary</h2>
        <div className="overflow-x-auto print:overflow-visible">
          <table className="w-full min-w-[24rem] border-collapse border border-slate-200 text-left text-sm">
            <thead>
              <tr className="bg-slate-50">
                <th className="border border-slate-200 px-3 py-2 font-semibold text-slate-900">Term</th>
                <th className="border border-slate-200 px-3 py-2 font-semibold text-slate-900">Meaning</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">
                  <strong>App user</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">A person with a Shepherd login.</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">
                  <strong>Parish registry</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  Official parish record for a person — may exist without a login.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">
                  <strong>Operational</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  Day-to-day workflows tied to events, attendance, volunteers, notifications — uses app identities.
                </td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">
                  <strong>In-app notification</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">Message visible in Shepherd&apos;s Notifications inbox.</td>
              </tr>
              <tr>
                <td className="border border-slate-200 px-3 py-2 align-top">
                  <strong>Reminder rule</strong>
                </td>
                <td className="border border-slate-200 px-3 py-2">
                  A scheduled rule on an event that sends messages before the event starts (when due and when processed).
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <section id="shepherd-name" className="scroll-mt-28 space-y-4">
        <h2 className="shepherd-section-title text-xl sm:text-2xl">Shepherd name</h2>
        <p>
          The product is branded <strong>Shepherd</strong> in the app (title, logo, and home page). Your parish may still
          refer to it in older documents under another name — in the software, look for <strong>Shepherd</strong> in the
          header.
        </p>
      </section>

      <hr className="border-slate-200 print:border-slate-300" />

      <footer className="space-y-2 border-t border-slate-200 pt-8 text-center text-sm italic text-slate-600 print:border-slate-300">
        <p>
          This guide reflects the Shepherd application structure and wording as implemented in the product codebase. If
          your parish customizes URLs or hosting, replace &quot;open Shepherd in your browser&quot; with the address your
          administrator gives you.
        </p>
      </footer>
    </article>
  );
}
