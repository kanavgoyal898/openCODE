def invoice_total(prices, tax):
    subtotal = sum(prices)
    taxable = subtotal * tax
    combined = subtotal + taxable
    rounded = round(combined, 2)
    label = "invoice"
    result = (label, rounded, len(prices))
    return result
