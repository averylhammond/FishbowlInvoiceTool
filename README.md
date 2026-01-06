[![Python-CI](https://github.com/averylhammond/FishbowlInvoiceTool/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/averylhammond/FishbowlInvoiceTool/actions/workflows/unit-tests.yml)

**************************************
INSTRUCTIONS TO SET UP FOR DEVELOPMENT
**************************************
1) Clone repo into a project folder.

2) In order to run on example resources (payment info files and example invoices), clone the default branch
   of https://github.com/averylhammond/automated-invoice-testing into the same project folder.
    - The necessary folder structure is shown below:
     <PRE>- project_root/
          ├── automated-invoice-testing/
          │   └── resources/
          └── FishbowlInvoiceTool/
              └── scripts/copy_resources.sh</PRE>

3) Run ./scripts/copy_resources.sh to copy the necessary configuration files. This will allow you to run
   the application using sample invoices and other config data. After running the script, your folder
   structure should look like this:
     <PRE>-FishbowlInvoiceTool/
          ├── Configs/
          │   └── Cost_Criteria.txt
          |   └── Payment_Terms.txt
          |   └── Sales_Reps.txt
          └── Invoices/
              └── S0-12345.pdf
              └── S0-98675.pdf
              └── etc</PRE>

4) Open a Python virtual environment
    - python -m venv venv

5) Activate virtual environment
    - Linux
        - source venv/bin/activate
    - Windows
        - source venv/Scripts/activate

6) Install dependencies
    - pip install -r requirements/dev.txt

    - NOTE: If on Linux, you need to install tkinter separately since it's not
            included in the standard library. Then run step 4.

        - For Debian based distros:
            - sudo apt-get install python3-tk for deb based distros
        - For Fedora users:
            - sudo dnf install python3-tkinter
        - For Arch based distros:
            - sudo pacman -S python3-tk

8) Run application
    - python main.py

9) Run unit tests
    - pytest tests/*


**********************************
INSTRUCTIONS TO SET UP FOR RELEASE
**********************************

1) Follow above instructions for development to set the repo

2) In virtual environment, install PyInstaller
    - pip install PyInstaller

3) Convert main.py into an exe
    - python -OO -m PyInstaller --onefile --noconsole --name AutoInvoiceProc main.py
    - Note: Remove the -OO when building a debug release

4) This will generate several files, including dist/AutoInvoiceProc.exe. Save this file
   in another location to move later.

5) If in a python virtual environment, exit it and run the following git commands
    - deactivate ( exit virtual environment if needed )
    - git reset --hard
    - git clean -fdxf

6) Paste the previously copied AutoInvoiceProc.exe into the clean repo and set up the 
   following folder structure for release-
   - FishbowlInvoiceTool
        - Configs
            - Payment_Terms.txt
            - Sales_Reps.txt
            - Cost_Criteria.txt
        - Invoices
        - AutoInvoiceProc.exe
        - ReadMe.txt
    

6) The parent folder can now be zipped up and packaged as a release on GitHub.

   https://github.com/averylhammond/FishbowlInvoiceTool#
