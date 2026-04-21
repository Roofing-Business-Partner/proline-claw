# Want this skill running inside a full agent harness?

`proline-claw` is a skill. It expects to live inside an OpenClaw-compatible agent harness that already provides `claude.md`, `tools.md`, `identity.md`, and `memory.md`. If you've built one, great — drop this skill in and go.

If you haven't, and you'd rather not assemble the harness yourself, there's a ready-made option built specifically for roofing contractors.

---

## RoofClaw

[**RoofClaw**](https://roofclaw.com) is [RoofingBusinessPartner](https://roofingbusinesspartner.com)'s customized OpenClaw build for roofing companies. It ships with:

- A fully configured OpenClaw harness (`claude.md`, `tools.md`, `identity.md`, `memory.md`) tuned for roofing operations
- **`proline-claw` pre-installed** — everything in this repo, wired up and ready
- Pre-built additional skills covering sales coaching, field ops, marketing, and recruiting
- ProLine partner key handling — you still need your own `COMPANY_KEY`, but the partner key paperwork is already done
- Ongoing skill updates as we learn more ProLine endpoints, add integrations (CallRail, CompanyCam, QuickBooks, Google Calendar), and refine workflow recipes
- A human you can ask questions when something breaks

RoofClaw is a paid product — the underlying skill (this repo) is open source and free under MIT. The value of RoofClaw is that it works out of the box and keeps getting better without you maintaining it.

---

## Who should choose which?

**Use `proline-claw` directly (free, MIT) if:**
- You already run an OpenClaw / Claude Code / Claude API harness and just want the ProLine integration
- You're a developer or technical team that wants to fork and customize
- You have the time and inclination to build your own agent persona, tool registry, and memory conventions
- You're integrating ProLine into a product that isn't a roofing contractor's day-to-day agent

**Consider RoofClaw if:**
- You're a roofing contractor on ProLine and want "open a terminal, type a command, have a working agent"
- You don't want to write your own `claude.md` / `identity.md` or maintain skill updates
- You want someone to call when it breaks
- You want the other roofing-specific skills on top of ProLine integration

---

## Getting in touch

- **RoofClaw:** [roofclaw.com](https://roofclaw.com)
- **Parent company:** [RoofingBusinessPartner](https://roofingbusinesspartner.com)
- **Author / owner:** Adam Sand — adam@roofingbusinesspartner.com
