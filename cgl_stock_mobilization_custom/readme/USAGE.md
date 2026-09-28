Before first use, go to Inventory > Configuration > Settings > Mobilização
de Materiais and set:

- **Local de Materiais em Obra**: the stock location that represents
  material currently at any construction site.
- **Plano Analítico de Obras**: the analytic plan whose accounts identify
  each site.

Saving creates (or re-points, if the configured location changes later)
the "Mobilização" and "Desmobilização" transfer types, wired as each
other's return type.

To send material to a site, create a transfer with the "Mobilização"
operation type and set the site's analytic account on the distribution,
same as any other internal transfer. To register what comes back, use the
"Devolução"/"Desmobilização" transfer, entering only the quantity that is
actually returning; any remainder is left open on a backorder.

Once it is clear a pending quantity will not come back, open that
backorder and click "Registrar Baixa (não retornou)" to pre-fill a
write-off (`stock.scrap`) per pending line. Fill in the reason and a
justification, then validate it; the pending move is cancelled
automatically.

The "Materiais em Obra" report (Inventory > Reporting) consolidates, per
site, what was mobilized, returned and written off, with quantities and
values.
