# Release Notes

## Release 2.4 - Feb 10, 2025

### Features

- **API v2 General Availability** - New response format with pagination. v1 still supported but deprecated.
- **Dashboard Theming** - Users can choose dark/light mode. Persisted in settings.
- **Bulk Operations API** - New `/bulk` endpoint accepts up to 1000 requests in single call.

### Bug Fixes

- Fixed data warehouse connector timeout on slow networks (was killing connections at 30s, now 120s)
- Resolved Redis latency spikes by switching eviction policy from LRU to LFU
- Analytics dashboard pagination now works on accounts with 100K+ events

### Performance

- API response time: -12% average (mainly from Redis fix)
- Dashboard load time: -18% (optimized D3 visualizations)
- Export time for large datasets: -25% (batch processing improvement)

### Deprecations

- `/api/v1/*` endpoints marked deprecated. Full removal planned April 1, 2025.
- Support for Python 2.7 in SDK ended (Python 3.8+ required now)

### Known Issues

- Dark mode has contrast issues on button hover states (fixing in 2.4.1)
- Bulk API endpoint returns 502 on exactly 1000 requests (edge case, fix pending)

---

## Release 2.3 - Jan 18, 2025 ⚠️ PARTIAL ROLLBACK

### Features

- **Guided Onboarding** - New 3-step integration wizard
- **Compliance Checklist** - SSO, data classification, audit logging requirements
- **Progress Indicator** - Shows users they're 67% through onboarding

### What Went Wrong

- **Activation dropped 18%** in first 48 hours (42% → 34%)
- **Support surge**: 47 tickets on Jan 18, vs 12 typical/day
- **Root cause**: Compliance checklist was mandatory on day 1 instead of day 7

### Remediation (Jan 23)

- Made compliance checklist optional
- Added "Skip for now" button with defer logic
- Fixed data warehouse connector timeout issue (92% failure → 78% success)
- Posted in-app notification explaining changes

### Current Status

- Activation recovered to 39% (still 3% below baseline, but trending up)
- Support tickets normalized to 18/day
- Most customers happy with optional compliance approach

---

## Release 2.2 - Dec 15, 2024

### Features

- **Advanced Retention Analytics** - New dashboard showing day-7/14/30 retention by segment
- **Feature Flag System** - Gradual rollout capability with kill switch
- **Improved Error Messages** - More actionable error messages for common failures

### Metrics Impact

- Reduced deployment testing time from 8-12h to 20 min (via feature flags)
- Identified 3 segments with low week-2 retention (now targeted with intervention)
- Support response time improved 22% (clearer errors = fewer clarification questions)

---

## Release 2.1 - Nov 15, 2024

### Features

- **Win-back Campaigns** - Automated emails for lapsed customers based on usage patterns
- **Customizable Dashboard** - Users can arrange widgets, save views
- **Webhook Retries** - Failed webhooks now retry 3x with exponential backoff

### Beta Testing

- Win-back campaigns in closed beta with 5 enterprise customers
- Expected win-back rate: 12% based on pilot results
- Full rollout planned in February

---

## Release 2.0 - Oct 1, 2024

### Major Changes

- **New UI Framework** - Migrated from Bootstrap to TailwindCSS (design consistency)
- **Improved Search** - Full-text search on accounts, users, events
- **Multi-workspace** - Users can belong to multiple organizations

### Breaking Changes

- Old dashboard URLs no longer work (301 redirect to new URLs)
- API auth header format changed (docs updated, SDKs auto-patched)

### Performance

- Page load time: -35% (code splitting + lazy loading)
- API response time: -15% (query optimization)

---

## Release 1.9 - Aug 20, 2024

### Features

- **Data Export** - CSV export of events, accounts, user data
- **Scheduled Reports** - Daily/weekly digest emails with charts
- **Audit Logging** - All user actions logged for compliance

### Reliability

- Uptime: 99.97% (no incidents this month)
- P95 latency: 240ms

---

## Database Migration Completed - Jan 2025

### Details

- PostgreSQL 12 → 14 (zero downtime migration)
- Logical replication approach used for safety
- Full validation pass: 2.3B rows in 8 minutes
- Executed Sunday 2am PST (lowest traffic window)

### Results

- Query latency: -30% on complex analytics queries
- Vacuum time: -67% (6h → 2h daily)
- Backup size: -15% (better compression in v14)

### No customer impact - completely transparent migration
