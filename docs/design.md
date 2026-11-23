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
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Net worth    │ Cash         │ Debt         │ This month   │
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

- Step 3: wireframes of the key screens.
- Step 4: full design system (type, spacing, components).
- Step 5: widget sizes and the token list in detail.
- Step 6: static mockups with fake data.
