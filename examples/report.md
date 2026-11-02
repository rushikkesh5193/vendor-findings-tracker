# Vendor findings and escalation report - ExampleOrg

As of 2026-10-23. 13 open findings, 3 overdue, 11 issues. SLAs and escalation thresholds are configurable defaults.

## Summary for senior stakeholders

- Northwind Payroll: F01 (critical) is 37 days overdue; needs senior leadership, recorded senior leadership.
- Contoso Cloud: F02 (high) is 34 days overdue; needs senior leadership, recorded owner.
- Fabrikam KYC: F03 (medium) is 13 days overdue; needs owner, recorded owner.

## Issues

### Critical (1)

- **FINDING_OVERDUE** `F01`: No MFA on admin console (Northwind Payroll) is 37 days overdue; escalation to senior leadership is due. *Action:* Chase the vendor and record the escalation.

### High (5)

- **ESCALATION_MISSING** `F02`: Backups not encrypted (Contoso Cloud) is 34 days overdue and needs escalation to senior leadership; recorded level is owner. *Action:* Escalate to senior leadership now.
- **FINDING_OVERDUE** `F02`: Backups not encrypted (Contoso Cloud) is 34 days overdue; escalation to senior leadership is due. *Action:* Chase the vendor and record the escalation.
- **ACCEPTANCE_EXPIRED** `F06`: The risk acceptance for Weak password policy expired on 2026-09-30. *Action:* Renew with a fresh approval or remediate.
- **ACCEPTANCE_INVALID** `F07`: Shared admin accounts is marked risk accepted without a complete approval (approver, approval date and expiry). *Action:* Complete the approval or reopen the finding.
- **UNKNOWN_VENDOR** `F10`: Unmapped vendor finding refers to vendor V99, which is not in the vendor list. *Action:* Correct the reference.

### Medium (5)

- **FINDING_OVERDUE** `F03`: Stale access reviews (Fabrikam KYC) is 13 days overdue; escalation to owner is due. *Action:* Chase the vendor and record the escalation.
- **NO_DUE_DATE** `F04`: Missing log retention has no due date; the high SLA of 30 days gives 2026-11-09. *Action:* Agree a due date with the vendor.
- **DUE_BEYOND_SLA** `F05`: No pen test in 18 months: due 2027-01-01 is 153 days after it was opened; the high SLA is 30 days. *Action:* Record an approved extension or bring the date back inside the SLA.
- **ACCEPTANCE_TOO_LONG** `F08`: The risk acceptance for No DR test evidence runs 2026-10-01 to 2028-01-01, longer than 12 months. *Action:* Shorten the expiry so the risk is reviewed at least annually.
- **CLOSED_NO_EVIDENCE** `F09`: Outdated TLS configuration was closed on 2026-07-20 with no closure evidence. *Action:* Attach the evidence the vendor provided.

## Ageing of open findings (days since opened)

| Bucket | Findings |
|---|---|
| 0-30 | 7 |
| 31-60 | 3 |
| 61-90 | 2 |
| >90 | 1 |

## By vendor

| Vendor | Open | Overdue | Oldest (days) |
|---|---|---|---|
| Contoso Cloud | 2 | 1 | 64 |
| Fabrikam KYC | 2 | 1 | 95 |
| Northwind Payroll | 1 | 1 | 52 |
| Adatum Analytics | 2 | 0 | 83 |
| Tailspin Messaging | 2 | 0 | 22 |
| Litware Support | 1 | 0 | 11 |
| Proseware Print | 1 | 0 | 21 |
| V99 | 1 | 0 | 8 |
| Wingtip Travel | 1 | 0 | 8 |

## By owner

| Owner | Open | Overdue | Oldest (days) |
|---|---|---|---|
| R. Iyer | 2 | 2 | 95 |
| A. Menon | 11 | 1 | 83 |
