Fixes the Duration column in the Time Tracking tab of Manufacturing work
orders: the underlying field stores minutes, but Odoo displays it with a
widget that expects hours, so e.g. 124 minutes shows as "124:00" instead
of "2:04". This module adds a converted field so the column shows the
correct hours:minutes.
