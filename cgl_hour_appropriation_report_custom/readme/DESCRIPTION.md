The "Relatório de Apropriação de Horas" report is a SQL view created with BI
SQL Editor. Its hours were shown as plain decimals (e.g. 203.99) and in a text
column that cannot be summed, so the totals of the groups did not look like
hours and minutes.

This module extends the list, pivot and graph views that BI SQL Editor
generates for the report so that the decimal hours column (`x_horas_decimal`)
is shown as HH:MM with the `float_time` widget. The widget also formats the
totals of the groups, which are still summed as decimals, so they add up
correctly (e.g. 203:59).

The text hours column (`x_horas`) is only **hidden** in the list view, not
removed: the SQL query is not changed, because changing it requires resetting
the report to draft, which deletes its menu and the users' favorites. The
column is still in the model, in the search view, in the export wizard and in
the pivot view, and it keeps the old values. Removing it needs the SQL query
of the report to be changed.

The module acts on any BI SQL view that has a float column named
`x_horas_decimal`, whatever its name, so a report with a column of that name
that is not an amount of hours would be shown as HH:MM too.

The SQL query, the action, the menu, the security and the users' favorites of
the report are not touched.
