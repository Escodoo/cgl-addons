Set the Cost Center (Equipment) field on a Purchase Order header; it
propagates to all lines automatically. Each line stays editable afterwards,
and clearing the header field removes the equipment cost center from the
lines again.

The field lists the analytic accounts of the **Equipamentos** plan, which the
module installs. The accounts themselves are customer master data: register
them under Accounting > Configuration > Analytic Accounts, choosing the
Equipamentos plan. Until at least one account exists there, the dropdown is
legitimately empty.

The field is only visible to users in the *Analytic Accounting* group, so
that setting must be enabled under Accounting settings.
