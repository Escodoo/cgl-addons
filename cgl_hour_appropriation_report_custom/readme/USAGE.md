Install the module. The views of every BI SQL view that already has its UI
created are extended right away. Open Timesheets \> Reports \> Relatório
de Apropriação de Horas: the **Horas** column is now shown as HH:MM, also in the
totals of the groups and in the pivot view.

The module applies to any BI SQL view with a float column named
`x_horas_decimal`.

The extension is also kept when the UI is deleted and created again (**Delete
UI** / **Create UI** or **Reset to Draft**), so it is not necessary to do
anything after changing the SQL query. Note that deleting the UI deletes the
action and the menu, as BI SQL Editor always did, which drops the favorites of
the users.
