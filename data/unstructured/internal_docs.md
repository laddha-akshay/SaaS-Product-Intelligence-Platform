# Internal Product Documentation

## Q1 2025 Strategic Initiatives

### Onboarding Redesign (Release 2.3) - Shipped Jan 18, 2025

**Context:**
Our onboarding funnel was leaking 40% of users by day 3. Analysis showed users were confused about which integrations to connect first. The product team built a new guided experience with Mixpanel tracking to understand where users drop off.

**What Changed:**

- Added 3-step integration wizard (Slack → Salesforce → Data Warehouse)
- Introduced compliance checklist (SSO, data classification, audit logging)
- New progress indicator showing users they're 67% through onboarding

**Expected Outcomes:**

- Increase day-3 activation from 60% → 75%
- Reduce support tickets related to "where do I start?"
- Get 85%+ of users through all 3 integrations (previously 62%)

**What Went Wrong (Jan 18-22):**

- New mandatory compliance checklist added 8 min to onboarding flow
- Activation dropped 18% in first 48h (from 42% to 34%)
- Support surge: 47 tickets vs typical 12/day about "why can't I skip this"
- Slack integrations passing but data warehouse connections 92% fail rate

**Root Cause:**
We made the compliance checklist mandatory on day 1 instead of day 7. Most small customers don't need it day 1. Should have been optional initially or progressive disclosure.

**Recovery Actions (Jan 23+):**

- Made compliance checklist optional, move to day 7
- Added "Skip for now" button with 1-click deferral
- Engineering fixed data warehouse connector (was timing out on slow networks)
- Posted in-app notification explaining the changes

**Current Status (Feb 1):**

- Activation back to 39% (recovered most of the loss)
- Support tickets normalized to 18/day
- Data warehouse success rate now 78%
- Learned: Users value speed over compliance scaffolding early

---

## Database Infrastructure

### PostgreSQL Migration (Completed Jan 2025)

**Why?**

- v12 reaching EOL in October 2025
- Newer versions have parallel query optimization
- Team wanted JSONB improvements for customer metadata

**Process:**

- Logical replication from v12 to v14 (zero downtime)
- Tested on 3TB production replica first
- Cut over during lowest traffic window (Sunday 2am PST)
- Full validation pass: 2.3B rows validated in 8 minutes

**Impact:**

- Query latency down 30% on complex analytics queries
- Vacuum/cleanup time reduced from 6h to 2h daily
- Backup size reduced 15% (better compression)
- No data loss, no customer impact during migration

---

## Retention Features Shipped (Q4 2024)

### Feature Flags System (Nov 15, 2024)

Launched internal feature flag system for gradual rollouts. Reduced risk of large deployments from 8-12h of manual testing to 20 min automated validation.

### Win-back Campaigns (Dec 1, 2024)

Built automated email campaigns for churned customers. Personalized based on product usage patterns. Expecting 12% win-back rate based on pilot.

### Expanded Retention Metrics (Dec 15, 2024)

Started tracking:

- Day 7, 14, 30 retention (previously only day 1)
- Feature adoption curves per persona
- NPS scores broken down by account segment

Impact: Q4 showed 15% YoY improvement in day-30 retention vs Q4 2023. Largely driven by feature flag controlled rollouts (fewer bad deployments).

---

## API Versioning Strategy

### Why API v2?

- v1 had inconsistent response formats (some endpoints return arrays, some objects)
- No pagination on list endpoints (scalability nightmare)
- No versioning scheme (breaks when we add required fields)
- Auth was header-based, hard to debug for users

### API v2 Changes (Rolling out Feb 2025)

- All responses wrapped: `{ "data": [...], "meta": { "pagination": {...} } }`
- Pagination: limit/offset on all list endpoints (default limit 100)
- Typed errors: `{ "error": { "code": "VALIDATION_ERROR", "fields": [...] } }`
- v1 endpoints at `/api/v1/*`, v2 at `/api/v2/*` (both operational during transition)

### Migration Plan

- Feb 1-28: Both versions active, v1 requests logged for analysis
- Mar 1: v1 marked deprecated (still works, warnings in logs)
- Apr 1: v1 removed (gives integrations 60 days to migrate)
- Sent 2 emails + in-app notification + API docs updated

### Expected Issues

- 20% of integrations are sleeping/unmaintained (won't migrate)
- 5 large enterprise customers need custom mapping logic
- Estimated support load: 200 help tickets, 15h engineering time

---

## Security & Compliance Updates

### SOC 2 Type II Audit (Completed Dec 2024)

- 6-month audit process
- Focus areas: access controls, encryption at rest/transit, incident response
- Result: Passed with zero high-severity findings
- Enables enterprise sales conversations

### GDPR Data Deletion (Jan 2025)

- Implemented right-to-be-forgotten
- Customer data purged within 24h of request
- Compliance tested with PII deletion scripts
- Impact: 3 customers requested deletion, zero issues

---

## Known Technical Debt

1. **User Service Monolith** — 120K lines, hard to test

   - Plan: Extract auth service (Q2 2025)
   - Impact on activation: Medium (might move to different datastore)

2. **Legacy Analytics Pipeline** — Runs nightly ETL, 6h window

   - Plan: Switch to streaming (Kafka) in Q2
   - Current impact: Reports 24h stale

3. **Redis Cluster Instability** — Occasional 500ms latency spikes
   - Root cause: Key eviction policy, wrong algorithm
   - Fix: Changed from LRU to LFU (least frequently used)
   - Deployed Feb 5, monitoring latency closely
