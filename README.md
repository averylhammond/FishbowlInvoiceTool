[![Python-CI](https://github.com/averylhammond/FishbowlInvoiceTool/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/averylhammond/FishbowlInvoiceTool/actions/workflows/unit-tests.yml)

**************************************
INSTRUCTIONS TO SET UP FOR DEVELOPMENT
**************************************
1) Clone this repo into a project folder.

2) In order to test with example resources (payment info files and example invoices), clone the default branch
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
TO CREATE A RELEASE
**********************************

1) Clone this repo, or commit existing changes.

2) In order to copy in resources needed for release (payment info files and example invoices), clone the default 
   branch of https://github.com/averylhammond/automated-invoice-testing into the same project folder.
    - The necessary folder structure is shown below:
     <PRE>- project_root/
          ├── automated-invoice-testing/
          │   └── resources/
          └── FishbowlInvoiceTool/
              └── scripts/package_release.sh</PRE>

4) Run "./scripts/package_release.sh true", this will do the following:
    - Run a git clean
    - Create and activate a python virtual environment if one is not in use already
    - Install all project dependencies, even if they are already present
    - Install and run the latest version of PyInstaller to generate an executable
    - Copy the latest Configs/ folder from the automated-invoice-testing repo
    - If the first argument was true, it will also copy the latest Invoices/ folder
      from the automated-invoice-testing repo for use in automated testing. If the
      argument is false, it will create the folder, but not move the existing
      invoices over.
    - Zips up the release folder and places it into the /release folder.
    - Deactivate the currently active virtual environment

6) The zipped up release folder can now be published on GitHub.

   https://github.com/averylhammond/FishbowlInvoiceTool#
