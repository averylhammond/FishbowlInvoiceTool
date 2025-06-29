TODO: Move this to part of the release

Welcome to the Automated Invoice Processing Tool version 1.0!

To use the tool:

1) Download any invoice you would like to process as a '.pdf' file, and place them
into the 'Invoices' folder. The tool will process all files in one execution.

2) In the 'Configs' folder, ensure that any sales reps that can appear on the invoice
are listed in the 'salesReps.txt' file. 

Any entries must be input as xxxxx=yyyyy where 'xxxxx' is the sales rep as it appears 
on the invoice, and 'yyyyy'  = is the name of the sales rep you would like the tool to 
display after processing the invoice.

3) Similarly, ensure that any payment terms that could appear on the invoice are 
included in the 'paymentTerms.txt' file. Each line can have at most one entry.

4) Run 'AutoInvoiceProc.exe' to begin processing the invoices. Once the tool is 
finished, it will create/update two files: debug.txt, and results.txt. 

debug.txt contains a log of each cost that was processed and what type of cost it is. 
In the event that the tool incorrectly parses an invoice, this file can be used to figure
out where it went wrong.

results.txt contains all processed data on each invoice listed in the same order as the
invoice pdf files are listed in the 'Invoices' folder.


For help or support, please contact yours truly.