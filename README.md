**************************************
INSTRUCTIONS TO SET UP FOR DEVELOPMENT
**************************************
1) Clone repo

2) Open a Python virtual environment
    - python -m venv venv

3) Activate virtual environment
    - Linux
        - source venv/bin/activate
    - Windows
        - source venv/Scripts/activate

4) Install dependencies
    - pip install -r requirements.txt

    - NOTE: If on Linux, you need to install tkinter separately since it's not
            included in the standard library. Then run step 4.

        - For Debian based distros:
            - sudo apt-get install python3-tk for deb based distros
        - For Fedora users:
            - sudo dnf install python3-tkinter
        - For Arch based distros:
            - sudo pacman -S python3-tk

5) Run script
    - python main.py


**********************************
INSTRUCTIONS TO SET UP FOR RELEASE
**********************************

1) Follow above instructions for development to set the repo

2) In virtual environment, install PyInstaller
    - pip install PyInstaller

3) Convert main.py into an exe
    - pyinstaller --onefile --noconsole --name AutoInvoiceProc main.py

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
            - paymentTerms.txt
            - salesReps.txt
        - Invoices
        - logs
        - AutoInvoiceProc.exe
        - README.txt
    

6) The parent folder can now be zipped up and packaged as a release on GitHub.

   https://github.com/averylhammond/FishbowlInvoiceTool#
