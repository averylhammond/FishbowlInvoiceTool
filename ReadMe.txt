Welcome to the Automated Invoice Processing Tool Version 3.1.0, released on 7/26/2025.

To use the tool:

1) Download any Fishbowl invoice you would like to process as a '.pdf' file, and place them
into the 'Invoices' folder.

2) In the 'Configs' folder, check the following files

	- Ensure that Sales_Reps.txt contains a list of all possible sales reps that could
	  be listed on an invoice. If a sales rep's name code shows up on an invoice and
	  there is no corresponding entry in this file to decode it, the sales rep will
	  be blank on the invoice report.

	  Any entries must be input as xxxxx=yyyyy where 'xxxxx' is the sales rep as it appears 
	  on the invoice, and 'yyyyy'  = is the name of the sales rep you would like the tool to 
	  display after processing the invoice.

	- Ensure that Payment_Terms.txt has been populated with an exhaustive list of all
	  possible payment terms that can appear on an invoice. If a payment term is encountered
	  that is not on this list, it will be blank on the invoice report.

	  Any entries must be input as it will appear on the invoice, one per line.

	- Ensure that Cost_Criteria.txt contains all necessary information to discern between
	  different cost types. I.E: shipping costs vs material costs vs labor costs.

	  Any entries must be input as it will appear on the invoice, one per line.


3) Run 'AutoInvoiceProc.exe' to launch the application. The app has two main use cases detailed below:
	
	1 - To use the app to process a single invoice at once, click the "Browse" button to open the file
	    browser. The browser will automatically direct you to the Invoices folder. Select the invoice
	    that you would like the process, and then click "Process This Invoice".

	2 - To process all invoices in the Invoices folder, simply click the "Process All Invoices" button.

4) The output of the processed invoice(s) can be read in the output window below the buttons, or in the
   logs/results.txt folder. Note that logs/results.txt will reset once the app is restarted.

5) Repeat until all invoices are processed, and then click "Exit" to close the program.