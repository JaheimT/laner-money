# Roadmap

Work ONE milestone at a time, in order, one numbered step at a time.
Stop after each step so I can review. Later milestones must stay possible,
but don't build for them yet.

**Phase 1** = my own one-stop shop for personal finances, running on my
homelab. **Phase 2** = making it accessible to other people, only once
I've used it and think it's a good product.

Security from day one in every milestone: ORM only, validated and
length-limited input, CSRF on every form, no secrets in code, no debug in
production. Solarpunk palette; violet only for security/auth states.

---

# Phase 1 — my one-stop shop

## M0 — Python foundation ✅
FastAPI + SQLAlchemy + Jinja2. List and add transactions; security basics
(ADR 0003).

## M1 — Design: navigation and look (steps 1–4 ✅; 5–7 paused for MVP)
Simple but effective: decide how the whole app fits together *before*
building lots of pages, so features slot into a plan instead of piling up.
1. List every screen the finished Phase 1 app needs, and the main
   question each one answers ("how much can I spend this week?").
2. Navigation: dashboard as home, left sidebar with every screen in
   clear groups (Money, Plan), what the home screen shows.
3. Wireframes for the key screens (dashboard, transactions, accounts,
   add-transaction) — rough layouts, no colour yet.
4. Design system: colours (moss, ochre, bark, sand; violet for security),
   type, spacing, and the reusable pieces (buttons, forms, tables, cards,
   money formatting, empty states, error messages).
5. Widget grid and theme tokens: every dashboard tile is a self-contained
   widget in standard sizes; every colour/size is a named token, so
   layouts and themes can be customised later (M10) without rework.
6. Static HTML/CSS mockups of the key screens with fake data. Check on a
   phone-sized screen too.
7. Write it up in docs/design.md so later milestones follow it.

## MVP — usable on my homelab (CURRENT, 2026-11-25)
Pulled forward from M2–M4 so I can start logging real spending now,
from anywhere on my tailnet. Done in order:
1. Alembic baseline (M2.1), so real data survives later schema changes.
2. Dashboard v1 as home: this month's in / out / net, spending by
   category, daily spending, recent transactions; transactions page by
   month with delete; add-transaction page. M1 design system, light and
   dark.
3. Login (M3.1–3.3): Argon2id password set by a command, secure
   sessions with expiry and logout, login rate limiting, violet screens.
4. Docker (M4.1–4.2): Dockerfile, docker-compose.yml, `.env.example`.
5. HTTPS over Tailscale Serve only (M4.3).
6. Basic nightly SQLite backups (first part of M4.4).
7. Dashboard laid out like the M1 control-room mockup. Tiles whose
   feature isn't built yet show an empty state saying what turns them on
   (never fake numbers).

Order after the MVP (changed 2026-11-25, so dashboard tiles come alive
quickest): Budget pot + category limits (from M6) → Accounts (M2.2) with
Cash / Debt / Net worth tiles (M5) → net worth chart and Debts tile →
Bills and payday (M8.1–2) → Savings goals (M6.2) and ISA (M7).

Still to do in their own milestones: M1 steps 5–7, the rest of M2,
the M3.4 security pass, tested restore and update procedure (M4.4).

## M2 — Foundations (localhost only)
1. Alembic migrations — before any real data goes in.
2. Accounts: name, type (cash, investment, pension, property, debt),
   asset or liability, opening balance. Every transaction belongs to one.
3. Edit and delete for transactions and accounts.
4. Categories dropdown (from ones already used), filters by month,
   category and account; monthly in / out / net.
5. Transfers between accounts (credit card payment, money into an ISA)
   that don't count as spending.
6. Apply the M1 design to every page built so far.

## M3 — Login + security pass 1
Must be done before the app is reachable from anything but localhost.
1. Single-user password hashed with Argon2id (`argon2-cffi`, no hand-rolled
   crypto), set by a command — never stored in code.
2. Sessions: random token, HttpOnly, SameSite=Strict, Secure cookie;
   expiry; logout.
3. Login rate limiting. Violet login/lock screens.
4. Review everything so far; `pip-audit` and `bandit`; findings in
   docs/security-notes.md.

## M4 — Homelab deploy (Docker)
1. Dockerfile: slim Python base, non-root user, DB in a mounted volume,
   no debug.
2. docker-compose.yml + `.env.example` (real secrets never committed).
3. HTTPS over Tailscale only (Tailscale Serve or Caddy); never public.
4. Automated daily SQLite backups, a tested restore, update procedure.
5. Start using it daily.

## M5 — Net worth
1. Dashboard: total assets, total liabilities, net worth.
2. Manual balance updates for accounts not tracked transaction by
   transaction (pension, investments).
3. Net worth over time chart.
4. Debt labels: good vs bad debt.

## M6 — Budgets, pots and savings goals
1. Pots: Spending (£80/week), Emergency Fund, ISA, Sinking Funds, each
   with a target and progress.
2. Savings goals: target amount and date; how much per month to get there.

## M7 — ISA allowance tracker
1. Tag deposits into ISA accounts by ISA type (cash, stocks & shares,
   LISA).
2. Allowance used and remaining for the current tax year (6 April –
   5 April), with a warning before going over.
3. Allowance limits stored per tax year as data, not hard-coded — the
   rules change (e.g. separate cash ISA limits).

## M8 — Bills and less typing
1. Recurring transactions: rent, subscriptions, salary.
2. Bill calendar: month view of upcoming bills and paydays; what's due
   before next payday.
3. CSV import from my bank: an import review screen before anything is
   saved, with duplicate detection.
4. Auto-categorisation, so I don't pick categories by hand: my own rules
   first, then learning from past choices (same merchant → same category),
   then editable starter rules for common UK merchants. "Always put X in Y"
   when I pick one; suggestions when adding by hand too; a Rules page in
   Settings. All matching happens on my server: statements are never sent
   to AI or other outside services.

## M9 — Investment holdings with live prices
1. Holdings per investment account: ticker/fund, units, cost.
2. Live prices from a price API, cached; manual price as a fallback.
3. Value, gain/loss, and allocation per account.
4. Security/privacy: API key in `.env`; only tickers ever leave the
   server (never amounts or account details); the app keeps working if
   the API is down; note in docs/security-notes.md what the provider
   can learn.

## M10 — Customisation: layouts and themes
Like Linux: easy, simple defaults; change everything if you want to.
1. Dashboard edit mode: move, resize, hide and add widgets. Works with
   plain buttons first (no JavaScript needed).
2. Layout presets: Control room (default), Minimal, Budget focus,
   Investor. Layout saved as data; "Reset to default" always available.
3. Theme presets: Solarpunk (default), Night grove (dark), High contrast.
4. Custom themes: change colours, radius, spacing, fonts. Import/export
   as small files.
5. Drag and drop on top of edit mode, with a small self-hosted JS
   library (nothing loaded from outside sites).
6. Safety rules: themes are values, never raw CSS or scripts; the
   violet security colour can't be removed or reused; contrast warning
   for unreadable themes.

## M11 — Live with it + security pass 2
Use it for a month or so; list and fix annoyances. Re-read every module
against docs/security-notes.md, update dependencies, re-run `pip-audit`
and `bandit`.

---

# Phase 2 — share it (only when I'm happy with Phase 1)

Not planned in detail on purpose. Possible order:
- JSON API (needed by everything below)
- Public Docker image for technical homelab users
- Desktop app for everyone: own window (pywebview), packaged with
  PyInstaller for Windows, Mac and Linux
- Phones: PWA first, app stores maybe later
- Maybe: automatic bank syncing (Open Banking) — big security
  responsibility, only once everything else is solid
