Adds an Employee field (hr.employee) to the Time Tracking tab of
Manufacturing work orders, alongside the existing User field.

In Community, work order time tracking only records the system user
(res.users), which forces creating a system user for every shop-floor
operator. This module lets you record the actual employee who performed
the activity, which is the correct model for labor attribution, while
keeping the user field for auditing who logged the record.

It also fixes the Duration column in that same tab: the underlying field
stores minutes, but Odoo displays it with a widget that expects hours,
so e.g. 124 minutes shows as "124:00" instead of "2:04". This module
adds a converted field so the column shows the correct hours:minutes.
