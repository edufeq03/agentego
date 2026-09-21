# Requirements & Design Decisions

This document bridges the gap between business needs and the implemented system solutions.

## The Core Challenge
Off-the-shelf WhatsApp bots often fail because they enforce a rigid, one-size-fits-all workflow. Different businesses require vastly different qualification processes and escalation rules.

## Design Decisions

### 1. Configurable Custom Fields
* **Business Requirement:** A gym needs to ask about "workout goals," while a real estate agency needs to know "budget range."
* **System Solution:** Instead of hard-coding every workflow into the database schema, I designed a system of configurable custom fields that can be added dynamically per tenant. The AI is instructed to gather these fields naturally during the conversation, extract the values, and store them systematically in the CRM (verified via `test_triage_custom_fields.py`).

### 2. Deterministic Human Handoff
* **Business Requirement:** AI cannot resolve 100% of complex customer issues (e.g., billing disputes). The business needs a fail-safe.
* **System Solution:** An explicit human handoff workflow. The AI operates within deterministic guardrails. If a user requests human assistance, or the AI detects frustration, it emits a `[SOLICITAR_HUMANO]` tag. The system intercepts this tag, pauses the AI for that specific lead, and alerts a human operator on the dashboard.

### 3. Smart Re-engagement
* **Business Requirement:** Following up with leads is crucial for sales, but automated spam can result in WhatsApp bans.
* **System Solution:** An automated customer re-engagement workflow with configurable multi-step cadences, delays, state management, and anti-spam guardrails. The system ensures follow-ups are context-aware and time-appropriate.
