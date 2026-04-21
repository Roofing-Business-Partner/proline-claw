# Requesting a ProLine Partner API Key

ProLine's API uses two separate credentials:

| Credential | What it authorizes | How to get it |
|---|---|---|
| `PARTNER_KEY` | The integrator (developer or agent) | Manually issued by ProLine after you apply |
| `COMPANY_KEY` | A specific ProLine tenant's data | Self-serve in ProLine → Settings → Integrations |

Unlike many SaaS APIs, ProLine does **not** auto-issue partner keys. They vet every applicant and want to understand what your integration does and how you handle customer data. This is usually a good thing — it's one reason ProLine tenants trust partner integrations in the first place.

Plan for a few business days between applying and getting a key.

---

## What ProLine wants to know

When you apply, be ready to describe:

1. **What the integration does.** Concrete capabilities and the user-facing outcome — not marketing language.
2. **Which endpoints you'll call and how often.** Reference `docs/endpoints.md` for the full list. Note which you'll write to and which are read-only.
3. **How customer data is handled.** Where it flows, where it's stored, retention, and who on your team has access. If you're using an AI agent (Claude, ChatGPT, etc.), say so explicitly and describe what the agent can and can't do.
4. **Who will hold the partner key.** One integrator = one partner key. It's not shared across customers — customer-level scoping happens via the `COMPANY_KEY`.
5. **Your company + contact info.** Company name, primary technical contact, and where customers can reach you if something goes wrong.

---

## Email template

Adjust to your situation. Send to ProLine support / partnerships — check [proline.app](https://proline.app) for the current contact address.

```
Subject: Partner API key request — [Your Company / Integration Name]

Hi ProLine team,

I'd like to request a Partner API key for [your company / product name].

What the integration does:
[1–3 sentence summary of the user outcome. Example: "We run an AI
assistant that helps roofing contractors manage their pipeline,
automate post-inspection follow-up, and surface deals that are
slipping through the cracks. The assistant takes actions in
ProLine on behalf of the authenticated company user."]

Endpoints we'll use:
- find/project, edit/project — read/update project and contact data
- find/contact, find/event — lookup
- events/edit, events/cancel — appointment management
- find/team_member — rep lookup
(Full list in our repo if helpful: [link])

Data handling:
- Customer data is [stored where? retained how long? encrypted?]
- Access is limited to [describe]
- [If using an LLM: The LLM has access to project/contact data when
  invoked by the authenticated company user. No data is used for
  model training. Rate of API calls is capped at roughly one call
  per five seconds per endpoint.]

Who holds the key:
- Primary technical contact: [Name, email]
- Company: [Company name, website]

We're happy to jump on a call or answer any follow-up questions.

Thanks,
[Your name]
```

---

## After you have the partner key

1. Put it in your local `.env`:
   ```bash
   PROLINE_PARTNER_KEY=<the-key-ProLine-issued>
   PROLINE_COMPANY_KEY=<per-tenant-key-from-ProLine-Settings>
   ```
2. **Do not commit `.env` to git.** The included `.gitignore` handles this — verify `git status` shows `.env` as ignored before your first commit.
3. Run `python3 scripts/onboard.py` to validate the keys and discover your tenant's stage/user IDs.

---

## One partner key, many companies

Your partner key authenticates *you* (the integrator). Each ProLine company you work with will provide their own `COMPANY_KEY`. If you're running the agent for multiple roofing companies, keep the partner key constant and swap `PROLINE_COMPANY_KEY` per deployment — or run separate copies of the agent per tenant so there's no cross-tenant leakage.

If you're building a multi-tenant SaaS on top of this skill, talk to ProLine about their multi-company expectations up front.
