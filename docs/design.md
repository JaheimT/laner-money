# Design

Work in progress: M1 (see docs/roadmap.md). Steps 1 and part of 5 are
captured here; navigation, wireframes and the full design system follow.

## Direction

> **The data of Firefly III, the look of YNAB.**

Track everything (accounts, debts, budgets, bills, goals, ISA, investments,
net worth) but keep every screen calm and easy to read.

> **Like using Linux:** easy, simple defaults out of the box; change
> everything if you want to.

Most people never need to touch a setting. Advanced users can move,
resize and restyle anything (M10).

## Principles

1. **One question per screen.** Each screen exists to answer one question
   (see the screen list).
2. **Summary first, detail on tap.** All the data is there, but it's hidden
   until you ask for it (progressive disclosure).
3. **Few choices.** A clearly grouped menu; one main button per screen.
4. **Fast to log.** Adding a transaction takes seconds, on a phone too.
5. **Plain words.** "You owe £2,340", not "Liability balance: −234000".
6. **Calm, not alarming.** Colour only when it means something: moss for on
   track, ochre for "watch this", clay for a problem.
7. **Laner's own look.** Take inspiration, don't copy: solarpunk earth
   tones; violet only for security/trust states.
8. **Defaults first, options second.** Good presets for everyone; full
   control for those who want it.

## Period toggle (everywhere)

Every screen that shows money over time has the same control, in the
same place (top-right of the screen header):

```
Day  Week  [Month]  Year      ‹ November 2026 ›
```

- **Day / Week / Month / Year** sets the period; **‹ ›** steps one period
  back or forward; clicking the label jumps back to "now".
- Weeks run Monday–Sunday. Year means the calendar year; the ISA screen
  uses the tax year (6 April – 5 April) instead, and says so.
- Each screen remembers its own last choice (Budget defaults to Week,
  everything else to Month).
- Worked-out figures (e.g. a weekly budget shown as a month) are marked "≈".

Where it applies:

| Screen | What the period changes |
|---|---|
| Dashboard | One toggle for the whole dashboard: in/out/net tile, budget, recent transactions, change in net worth |
| Transactions | Which transactions are listed, and the in/out/net totals |
| Budget | Spent vs budget for that period |
| Bills | Calendar view: day list, week strip, month grid, or year overview |
| Net worth | The "change" figures and how the chart groups points; the chart also has **All** |
| Account detail | Balance change and transactions in that period |
| Savings goals | How much was saved towards each goal in that period |

## Screens (M1 step 1)

⭐ = top 3, most used: these get the easiest-to-reach places.

**Everyday**

| Screen | The question it answers |
|---|---|
| Dashboard (control room) | "How am I doing right now?" Everything at a glance. |
| Transactions | "Where did my money go?" |
| Add / edit transaction | "I just spent something; log it fast." |

**Money overview**

| Screen | The question it answers |
|---|---|
| Accounts | "What do I have and what do I owe?" |
| Account detail | "What's happening in this one account?" |
| Debts | "What do I owe, what is it costing me, and when will it be gone?" Balance, APR, minimum payment, payoff date, good/bad label. |
| Net worth ⭐ | "Am I getting richer over time?" |

**Planning**

| Screen | The question it answers |
|---|---|
| Budgets & pots ⭐ | "How much can I still spend, and are my pots on track?" |
| Savings goals | "Will I hit my target in time?" |
| ISA allowance | "How much can I still put in my ISA this tax year?" |
| Bill calendar ⭐ | "What's coming out, and when?" Including what's due before payday. |

**Investments** (M9)

| Screen | The question it answers |
|---|---|
| Holdings | "What are my investments worth today?" |

**Admin**

| Screen | The question it answers |
|---|---|
| Import | "Can I bring in my bank statement instead of typing it?" |
| Settings | Categories, ISA allowance per tax year, backups, password, layout and theme. |
| Login / lock | "Is this really me?" (violet: a security state) |

## Dashboard: the control room

A grid of widgets showing the whole financial picture at once. Dense
but organised:

- Each widget answers one question, with one headline number and a small
  visual (sparkline, progress bar, mini calendar). Tap for the full screen.
- Most important widgets are biggest and top-left.
- Same layout every time, so your eyes learn where things live.
- On a phone, widgets stack in one column in the same priority order.

Default layout (wide screen). Numbers are made up:

```
                         Day  Week  [Month]  Year   ‹ Nov 2026 ›
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Net worth    │ Cash         │ Debt         │ This period  │
│ £12,480  ↑   │ £3,210       │ £2,340  ↓    │ +£410 net    │
├──────────────┴──────────────┼──────────────┴──────────────┤
│ Net worth over time         │ Budget: this week           │
│ (chart: assets, debts)      │ (progress bars per pot)     │
├─────────────────────────────┼─────────────────────────────┤
│ Bills: month calendar       │ Coming up before payday     │
├──────────────┬──────────────┼──────────────┬──────────────┤
│ Savings goals│ ISA allowance│ Debts        │ Recent       │
└──────────────┴──────────────┴──────────────┴──────────────┘
                                         [ + Add transaction ]
```

## Navigation (M1 step 2)

The **dashboard is home**; a **sidebar on the left** lists every screen,
grouped. Always visible on wide screens.

```
┌───────────────────┬──────────────────────────────────────────┐
│ 🌿 Laner Money    │                                          │
│                   │                                          │
│ [ + Add ]         │                                          │
│                   │                                          │
│ ▣ Dashboard       │                                          │
│ ≡ Transactions    │          (the control room grid)         │
│                   │                                          │
│ MONEY             │                                          │
│   Accounts        │                                          │
│   Debts           │                                          │
│   Net worth  ⭐   │                                          │
│   Holdings        │                                          │
│                   │                                          │
│ PLAN              │                                          │
│   Budget     ⭐   │                                          │
│   Bills      ⭐   │                                          │
│   Savings goals   │                                          │
│   ISA allowance   │                                          │
│                   │                                          │
│ ───────────────   │                                          │
│ ⇪ Import          │                                          │
│ ⚙ Settings        │                                          │
│ 🔒 Lock           │                                          │
└───────────────────┴──────────────────────────────────────────┘
```

- **Groups:** Money (what I have and owe) and Plan (what's coming and
  what I'm aiming for), as in option A. Top 3 listed first in each group
  where it makes sense.
- **+ Add** sits at the top of the sidebar: one click from any screen.
- **Current screen** is highlighted (moss background).
- **Collapse to icons** to give the dashboard more room; remembered
  between visits.
- **Lock** uses violet (security state).
- **Phone / narrow screens:** the sidebar becomes a slide-out menu (☰
  button top-left); **+ Add** becomes a floating button bottom-right.
- Holdings appears once M9 exists; screens that don't exist yet aren't
  shown.

## Key screens (M1 step 3)

Rough layouts: structure only, no colour. Each sits in the main area
next to the sidebar. Numbers are made up.

### Transactions
```
┌──────────────────────────────────────────────────────────┐
│ Transactions   Day Week [Month] Year  ‹ November 2026 ›  │
│ 🔍 Search                                                │
│ [All accounts ▾] [All categories ▾]                      │
├──────────────────────────────────────────────────────────┤
│  In £1,940        Out £1,530        Net +£410            │
├──────────────────────────────────────────────────────────┤
│ Sat 22 Nov                                       −£34.20 │
│   🛒 Groceries   Tesco            Current       −£23.10  │
│   ☕ Eating out  Flat white       Credit card    −£3.60  │
│   ⇄ Transfer     → Emergency Fund               £7.50    │
│ Fri 21 Nov                                     +£1,900   │
│   💷 Salary      Acme Ltd         Current    +£1,900.00  │
└──────────────────────────────────────────────────────────┘
```
- Grouped by day with day totals; transfers shown neutral (⇄), not as
  spending.
- Clicking a row opens the edit panel on the right; the list stays put.

### Add transaction (side panel)
```
┌──────────────────────────────┐
│ Add               ✕          │
│ [Expense] Income  Transfer   │
│        £ 12.50               │   ← big, cursor starts here
│ Category  [Groceries    ▾]   │   ← suggested from payee / recent
│ Account   [Current      ▾]   │   ← remembers last used
│ Date      [Today        ▾]   │
│ + More (note, pot)           │   ← hidden until needed
│ [ Save ]  [ Save & add another ] │
└──────────────────────────────┘
```
- Transfer swaps Category for **From → To** account.
- Opens as a side panel (current default; full page on phones).

### Budget
```
┌──────────────────────────────────────────────────────────┐
│ Budget      Day [Week] Month  Year     ‹ 17–23 Nov ›     │
├──────────────────────────────────────────────────────────┤
│  £34 left of £80        4 days left    ≈ £8.50 a day     │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░                                 │
├──────────────────────────────────────────────────────────┤
│ Groceries     £30 / £50   ▓▓▓▓▓▓░░░░   £20 left          │
│ Eating out    £28 / £30   ▓▓▓▓▓▓▓▓▓░   £2 left   (ochre) │
│ Transport      £8 / £20   ▓▓▓░░░░░░░   £12 left          │
├──────────────────────────────────────────────────────────┤
│ Pots                                                     │
│ Emergency Fund   £1,200 / £3,000   ▓▓▓▓░░░░░   40%       │
│ Christmas          £90 / £200      ▓▓▓▓▓░░░░   45%       │
│                                       [ Edit budget ]    │
└──────────────────────────────────────────────────────────┘
```
- Top line answers "how much can I spend?", including a per-day figure.
- Moss = fine, ochre = nearly full, clay = over.
- Toggle **Day / Week / Month / Year**; ‹ › steps back and forward one
  period. Defaults to Week (matches the £80/week Spending pot); the last
  choice is remembered.
- Each budget has a home period (e.g. £80 a **week**). Other views scale
  it: Day ≈ £11.43, Month = £80 × days in month ÷ 7, Year ≈ £4,171. Scaled
  figures are marked "≈" so it's clear they're worked out, not set.

### Bills
```
┌──────────────────────────────────────────────────────────┐
│ Bills  Day Week [Month] Year  ‹ November 2026 ›  [+ Bill]│
├──────────────────────────────┬───────────────────────────┤
│  M   T   W   T   F   S   S   │ Before payday (Fri 28)    │
│                          1   │   Mon 24  Phone     £18   │
│  2   3   4●  5   6   7   8   │   Thu 27  Spotify   £12   │
│  9  10  11  12● 13  14  15   │   Total due         £30   │
│ 16  17  18  19  20  21  22   │                           │
│ 23 [24●]25  26 [27●]28💷 29  │ This month                │
│ 30                           │   Bills    £742           │
│                              │   ✓ Paid   £694           │
│  ● bill   💷 payday          │   Due      £48            │
└──────────────────────────────┴───────────────────────────┘
```
- Click a day for its bills. Each bill: ✓ paid, due, or overdue (clay).

### Net worth
```
┌──────────────────────────────────────────────────────────┐
│ Net worth      Day Week [Month] Year  ‹ November 2026 ›  │
│ £12,480        +£320 this month                          │
├──────────────────────────────────────────────────────────┤
│  (chart: assets ──, debts ┄┄, net worth ━━)              │
│                                  [This period]  All      │
├────────────────────────────┬─────────────────────────────┤
│ Assets          £14,820    │ Debts            £2,340     │
│  Cash        £3,210  ▓▓░   │  Credit card  £840   bad    │
│  Investments £6,400  ▓▓▓▓  │  Student loan £1,500 good   │
│  Pension     £5,210  ▓▓▓   │                             │
├────────────────────────────┴─────────────────────────────┤
│ Last updated: Pension 3 weeks ago    [ Update balances ] │
└──────────────────────────────────────────────────────────┘
```
- The bottom line nudges me to update hand-entered balances so net worth
  stays accurate.

### Import review (M8)
```
┌──────────────────────────────────────────────────────────────┐
│ Import: statement-nov.csv → Current account                  │
│ 48 transactions · 41 sorted · 5 to check · 2 duplicates      │
├──────────────────────────────────────────────────────────────┤
│ To check (5)                                                 │
│  21 Nov  BRIGHTSIDE CAFE      −£4.20   [Choose ▾]            │
│  19 Nov  AMZN MKTP UK         −£17.99  [Choose ▾]            │
│ Sorted (41)                                      show all ▾  │
│  22 Nov  TESCO STORES 2041    −£23.10  Groceries   (rule)    │
│  20 Nov  SPOTIFY P1C9         −£11.99  Subscriptions (learnt)│
│ Duplicates, skipped (2)                          show ▾      │
├──────────────────────────────────────────────────────────────┤
│                       [ Cancel ]  [ Import 46 transactions ] │
└──────────────────────────────────────────────────────────────┘
```
- Nothing is saved until I press Import.
- Picking a category offers **☑ Always put "BRIGHTSIDE CAFE" in Eating
  out**, which creates a rule.
- Sorting order: my rules → learnt from past choices → starter UK rules →
  Uncategorised. All on my server; never sent to outside services.

## Customisation (built in M10, designed for now)

**Layout: like an iPhone home screen**
- Every tile is a self-contained **widget** in standard sizes (small,
  medium, wide), so any widget fits anywhere.
- Layouts are stored as **data** (which widget, where, what size), not
  hard-coded.
- Presets: **Control room** (default), **Minimal**, **Budget focus**,
  **Investor**.

**Look: like ricing**
- Every colour, radius and spacing value is a named **design token**
  (CSS custom properties, e.g. `--moss`, `--radius`). A theme is just a
  different set of token values.
- Presets: **Solarpunk** (default), **Night grove** (dark),
  **High contrast**.
- Custom themes can be imported and exported as small files.

**Rules**
- Themes are **values, never raw CSS or scripts**, so an imported theme
  can't run code or load things from outside sites.
- The **violet security colour can't be removed or reused**, so a theme
  can't make a fake lock screen look trusted.
- **Contrast check:** warn when a theme makes text hard to read.
- **"Reset to default"** is always available.

## Still to do in M1

- Step 4: full design system (type, spacing, components).
- Step 5: widget sizes and the token list in detail.
- Step 6: static mockups with fake data.
