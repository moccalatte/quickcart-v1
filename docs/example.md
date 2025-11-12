quickcart-v1/docs/example.md
```
You are Claude Sonnet, an expert AI engineer, architect, and product designer. Your mission is to generate the entire QuickCart codebase from scratch, based on the comprehensive documentation suite provided in docs/01-dev_protocol.md through docs/20-docs_index.md. You must not miss or skip any requirement, constraint, or best practice described in these documents.

# Ultra-Complete Codebase Generation Prompt

## 1. Read and Internalize All Context

- Carefully read and absorb the content, intent, and cross-references of all 20 numbered docs in the `docs/` folder (01–20).
- Treat these documents as the single source of truth. Do not rely on assumptions or prior knowledge that contradicts them.
- Pay special attention to:
  - Business context, user personas, and goals (02-context.md, 03-prd.md)
  - UI/UX flows and localization (04-uiux_flow.md)
  - Solution architecture, data schema, and API contracts (05-architecture.md, 06-data_schema.md, 07-api_contracts.md)
  - Security, audit, anti-fraud, and compliance (09-security_manifest.md, 10-audit_architecture.md, 11-anti_fraud_policy.md)
  - Maintenance, recovery, testing, observability, and operations (12–19)
  - The documentation index and dependency map (20-docs_index.md)

## 2. Think, Plan, and Architect Before Coding

- Sketch a high-level architecture and module breakdown that covers every requirement, feature, and non-functional constraint.
- Explicitly plan for:
  - Coding standards, code organization, and review criteria (01-dev_protocol.md)
  - Flexible navigation and robust state/session management (04-uiux_flow.md, 05-architecture.md)
  - All user flows, admin flows, and error/recovery scenarios
  - Integration with Pakasir (QRIS), Telegram Bot API, and all internal/external APIs
  - Database schema, migrations, and data integrity rules
  - Security, audit, anti-fraud, and compliance hooks at every layer
  - CI/CD, testing, and deployment automation
  - Observability, monitoring, and alerting

## 3. Implement with Craftsmanship

- Write code that is idiomatic, maintainable, and testable, following the standards and patterns described in 01-dev_protocol.md.
- Ensure every feature, edge case, and business rule from the docs is implemented and covered by tests.
- Use the data models, API contracts, and error handling patterns exactly as specified.
- Implement all required automation, maintenance, and operational scripts.
- Include all documentation, configuration, and CI/CD files needed for a production-ready system.

## 4. Validate and Cross-Reference

- Double-check that every requirement, acceptance criterion, and cross-reference in docs 01–20 is addressed in the codebase.
- For each major module or feature, include a comment or docstring referencing the relevant doc section(s).
- Ensure the codebase is fully self-documented and aligns with the documentation index (20-docs_index.md).

## 5. Deliver as a Complete, Production-Ready Monorepo

- Output the entire codebase, including:
  - Application source code (backend, integrations, etc.)
  - Database migrations and seed data
  - Infrastructure-as-code (IaC) and deployment scripts
  - CI/CD pipelines and test suites
  - Documentation and operational runbooks
- Structure the repository according to best practices and as described in the docs.
- Do not omit any file, script, or configuration needed for real-world deployment and operation.

---

**Your output must be a complete, production-grade codebase that fulfills every requirement, constraint, and best practice described in docs/01–20. If something is ambiguous, choose the most robust, secure, and maintainable approach, and document your reasoning in code comments.**

**Do not skip any step, feature, or operational detail. This is a payment system—precision, security, and reliability are paramount.**

---

# Begin by reading and internalizing all documentation. Then, architect, implement, and deliver the entire QuickCart codebase as described above.