# Technical Documentation & Architecture

### Data Schema
The platform utilizes a structured `platform_data.json` for multi-tenant isolation.
* **Users:** Global registry for auth and role-based access.
* **Seniors:** Encapsulated profiles containing meds, calendar, and history.
* **Links:** A relational mapping layer connecting Caregiver IDs to Senior IDs.

### Security & Compliance
* **Isolation:** Senior data is keyed by unique IDs, ensuring no cross-tenant data leakage.
* **Privacy:** Mandatory Mobile validation ensures a secure secondary contact point for SOS alerts.
* **HIPAA/PIPEDA Path:** The data structure is mapped for easy migration to encrypted PostgreSQL or AWS DynamoDB.

### Key Workflows
1. **The Handshake:** Explain how the `links` dictionary handles the "Auto-Tagging" logic when a senior signs up with a caregiver's email.
2. **Adherence Logic:** The `taken` and `arrived` boolean flags drive the Caregiver's "Metric" dashboard.
