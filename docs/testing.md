# Testing & Validation

The platform includes an automated test suite designed to validate both technical integration and complex business workflows.

## Automated Testing Strategy

The test suite relies heavily on isolated unit and integration tests, using **mocks** for external services like OpenAI, WhatsApp providers, and external calendars. This allows testing of deterministic business logic without incurring API costs or network latency.

### Test Execution

Tests can be executed locally with:
```bash
pytest
```

### Key Test Coverages:
- **`test_triage_custom_fields.py`:** Verifies that dynamic custom fields are correctly injected into the AI context, extracted from user messages, and saved to the CRM lead profile.
- **`test_smart_reengagement.py`:** Validates the automated follow-up cadences, ensuring anti-spam delays and state transitions work as expected.
- **`test_multiagents.py`:** Ensures the Agent Router correctly hands off conversations between the general triage AI and domain-specific specialists.
- **`test_whatsapp_agenda.py`:** Validates the scheduling workflow, including parsing natural language dates/times and avoiding double bookings.
- **Domain-specific Tests (`test_agenda.py`, `test_beleza.py`):** Ensures that niche-specific business rules (like minimum scheduling notice) are enforced by the AI.

These tests serve as living documentation of the system's requirements and provide a safety net for continuous schema and feature evolution.
