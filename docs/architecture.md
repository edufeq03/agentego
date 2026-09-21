# Architecture Details

This document outlines the architectural decisions and system design patterns implemented in Agente Go.

## 1. WhatsApp Integration Abstraction Layer
Instead of tightly coupling the application to a single WhatsApp provider (like Evolution API), the system uses an abstraction layer (`app/whatsapp/base.py`, `dispatcher.py`).
This design decision ensures that the backend can seamlessly switch between Evolution API, the official Meta API, or other providers without rewriting the core AI and business logic.

## 2. Multi-Tenancy Design
The application is designed as a true SaaS platform. The `Tenant` (Company) entity is the central pivot of the architecture. All major models (Leads, Messages, Events, CRM Deals, Pipelines, Configurations) contain a `tenant_id` foreign key.
This ensures strict data isolation at the application layer while allowing all clients to run on a shared infrastructure, significantly reducing hosting costs and simplifying deployments.

## 3. Database & Schema Evolution
- **PostgreSQL** handles the relational data model. The schema is highly normalized to support complex CRM and scheduling queries.
- **Alembic** is used for database migrations. The system evolved incrementally (e.g., `baseline_schema`, `crm_core_tables`, `whatsapp_provider_layer`) as new business capabilities and integration requirements were introduced.

## 4. Security Mechanisms Implemented
- JWT authentication and bcrypt for dashboard access.
- Strict tenant data separation on all API endpoints.
- Webhook token validation to ensure incoming messages are from trusted WhatsApp instances.
- Rate limiting and CORS configurations.
