---
paths:
  - "source/InvoiceProcessor.py"
  - "source/processor_utilities.py"
  - "source/InvoiceAppFileIO.py"
  - "source/Invoice.py"
---

# Invoice parsing and file I/O

## The money rule

**Every currency value is a `Decimal`. Never introduce a `float` into a cost path.** Catching
Fishbowl's floating-point rounding errors is the entire point of the app — a `float` here would
reproduce the bug the tool exists to find. Use `format_currency()` from `processor_utilities.py`
to quantize, and `DECIMAL_ZERO` from `source/constants.py` as the zero literal.

## The parse pipeline

`InvoiceAppFileIO.read_invoice_file()` returns one string per page via pypdf. Then:

1. **`populate_invoice()`** pulls the header fields — order number, PO number, date, customer,
   payment terms, sales rep — out of **page 1 only**, by regex.
2. **`process_invoice()`** walks every page. On each it trims everything before the
   `Ordered Total Price` marker, then reads line by line, tracking `next_line_num`: a line
   starting `"<next_line_num> "` begins a payment row, which hands off to
   `process_payment_line()`. A row can span several physical lines, so that method re-slices the
   page from its start line to `"\n<curr_line_num+1> "` to capture the whole row.
3. **`process_payment_line()`** skips subtotal lines, then tries `find_ea_cost()` (quantity
   priced) and `find_hr_cost()` (hourly rate) in that order — first positive result wins, and if
   neither is found the row is skipped entirely. It then classifies via
   `search_for_labor_criteria()` and `search_for_shipping_criteria()`, adding to
   `labor_cost` / `shipping_cost` / **`material_cost` as the fallback**, and to `subtotal` in
   every case. Material is the default branch, not a matched category.
4. **`process_end_of_invoice()`** fires on the `Total:Subtotal` marker and reads sales tax and the
   listed total. See the footer rule below.

The controller then compares the computed total against the listed one and warns on a mismatch.

**The pipeline needs a text layer, and the controller refuses the invoice when there is none.**
`handle_process_invoice()` rejects a PDF whose pages all extract blank, before `populate_invoice()`
runs. Every step above is regex over pypdf's extracted text, so a PDF with no text silently
produces a complete, plausible, entirely zero result — and because the calculated and listed totals
then agree at `$0.00`, the mismatch warning does not fire either. That is what a scanned invoice,
or one re-printed through a virtual printer such as "Microsoft Print to PDF", looks like: the page
is stored as an image, or its text as vector outlines, and pypdf extracts `""`. Reporting it is the
only honest option short of adding OCR. **Keep that guard ahead of any new parsing step**, and note
that a rejected invoice contributes no block to `logs/results.txt`.

## Reading the footer

**The footer's labels are not on the same line as their values, and never read one by line index.**
pypdf's default extraction emits the footer's label column before its value column, so the page
reads:

```
Total:Subtotal:
Sales Tax:$1,234.56   <- the last label, then the SUBTOTAL
$0.00                 <- sales tax
$1,281.10             <- listed total
```

`process_end_of_invoice()` therefore anchors on `FOOTER_VALUE_LABEL` (`"Sales Tax:"`) and takes the
first `FOOTER_VALUE_COUNT` amounts after it in order — subtotal, sales tax, listed total — via
`find_currency_values()` in `processor_utilities.py`. That is what "by label" means here: a regex
pairing a label with the amount on its own line would read the subtotal as the sales tax. It used
to read `splitlines()[2]` and `[3]`, which a single extra line in the footer would have shifted
(#93).

The first amount, the invoice's own listed subtotal, is deliberately discarded — `invoice.subtotal`
is summed from the payment lines, and reporting where the two disagree is the point of the app.

A footer with no label, or with fewer amounts than expected, is **reported through
`report_error` and leaves both amounts at `DECIMAL_ZERO`** rather than raising. Because
`find_currency_values()` matches digits only, a non-numeric amount falls out as a short list rather
than a `decimal.InvalidOperation` escaping into the tkinter callback, where `--noconsole` would
have swallowed the traceback and the app would appear to do nothing.

**Classification is config-driven, not coded.** A new cost category or matching term belongs in
`Configs/Cost_Criteria.txt`, not in a new `if/elif` in the processor. Shared regex, lookup and
formatting helpers belong in `processor_utilities.py` — check it (`search_text_by_re`,
`search_payment_line`, `find_payment_terms`, `find_sales_rep`, `format_currency`) before adding a
new one.

## Config file formats

All three live in `Configs/`, use `*` as a comment-line prefix, skip blank lines, and are **not
committed to this repo** — they arrive from the `automated-invoice-testing` submodule via
`scripts/copy_resources.sh`.

| File | Format | Parsed into |
| --- | --- | --- |
| `Sales_Reps.txt` | `CODE=Name` per line, split on the first `=` | `dict` |
| `Payment_Terms.txt` | One term per line | `list` |
| `Cost_Criteria.txt` | `CATEGORY:` heading lines, then one entry per line beneath | three lists |

`Cost_Criteria.txt`'s recognized headings are `LABOR CRITERIA:`, `LABOR EXCLUSIONS:` and
`SHIPPING CRITERIA:` (upper-cased on read); anything else is reported to the debug log and
dropped. **`parse_cost_criteria_file()` clears its three lists in place rather than reassigning
them** — the `InvoiceProcessor` holds references to those same lists, so reassigning would leave
it pointed at the old contents after the user saves an edited config.

## Error reporting

`InvoiceAppFileIO` takes a `report_error(title, message)` callback, defaulting to a no-op and
wired to `InvoiceAppDisplay.show_popup` by the controller **before** the configs are parsed, so
parse failures surface. Every read is wrapped in `try/except OSError` and returns an empty
`dict`/`list` on failure rather than raising — a missing config degrades the run, it does not
crash it. Keep that shape.

`print_to_debug_file()` and the debug log reset are `__debug__`-gated and vanish from the release
build (`python -OO`); never let real behavior depend on them running.

## Output formatting

`Invoice.to_formatted_string()` is what the integration test diffs against the submodule's
`canonical_correct_results.txt`. **Any change to it, or to the processing above, breaks that
check** until the canonical file is regenerated in `automated-invoice-testing`. Treat a diff there
as a decision, not an accident.
