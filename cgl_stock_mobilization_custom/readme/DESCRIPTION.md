Tracks material sent to (and returned from) construction sites ("obras")
instead of treating a site as a customer delivery.

Adds "Mobilização" and "Desmobilização" internal transfer types between the
warehouse and a configurable intermediate stock location, so material stays
part of inventory while it is off-site. A partial return automatically
leaves the remaining quantity open as pending, and a dedicated write-off
("Baixa de Material Não Retornado") records the reason (lost / stolen /
damaged / other), a free-text justification and the corresponding cost for
whatever does not come back, linked to the original transfer and to the
site's analytic account. A consolidated report shows, per site, how much
was mobilized, returned, is still pending and was written off, with values.
