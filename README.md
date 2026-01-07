[![Python-CI](https://github.com/averylhammond/FishbowlInvoiceTool/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/averylhammond/FishbowlInvoiceTool/actions/workflows/unit-tests.yml)

**************************************
INSTRUCTIONS TO SET UP FOR DEVELOPMENT
**************************************
1) Clone this repo into a project folder.

2) In order to test with example resources (payment info files and example invoices), clone the default branch
   of https://github.com/averylhammond/automated-invoice-testing into the same project folder. Note that this
   repo is private in order to protect sensitive customer data.
    - The necessary folder structure is shown below:
     <PRE>- project_root/
          ├── automated-invoice-testing/
          │   └── resources/
          └── FishbowlInvoiceTool/
              └── scripts/copy_resources.sh</PRE>

3) Run ./FishbowlInvoiceTool/scripts/copy_resources.sh to copy the necessary configuration files. This will
   allow you to run the application using sample invoices and other config data. After running the script,
   your folder structure should look like this:
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

7) Run application
    - python main.py

8) Run unit tests
    - pytest tests/*


*******************************************
INSTRUCTION TO CREATE AND PACKAGE A RELEASE
*******************************************

1) Clone this repo, or commit existing changes.

2) In order to copy in resources needed for release (payment info and other config files), clone the default 
   branch of https://github.com/averylhammond/automated-invoice-testing into the same project folder. Note that
   this repo is private in order to protect sensitive customer data.
    - The necessary folder structure is shown below:
     <PRE>- project_root/
          ├── automated-invoice-testing/
          │   └── resources/
          └── FishbowlInvoiceTool/
              └── scripts/package_release.sh</PRE>

3) Run "./FishbowlInvoiceTool/scripts/package_release.sh false", this will do the following:
    - Deactivate the current python virtual environment (if active)
    - Run a git clean
    - Create and activate a fresh python virtual environment
    - Install all project dependencies for the release configuration
    - Install and run the latest version of PyInstaller to generate an executable
        - The executable will be placed into the release/FishbowlInvoiceTool folder
    - Copy the latest Configs/ folder from the automated-invoice-testing repo and
      place it into the release/FishbowlInvoiceTool folder
        - If the first argument was true, it will also copy the latest Invoices/ folder
          from the automated-invoice-testing repo for use in automated testing. If the
          argument is false, it will create the folder, but not move the existing
          invoices over.
    - Zips up the release/FishbowlInvoiceTool/ folder and saves it in the release folder
      as: release/FishbowlInvoiceTool.zip
    - Deactivates the python virtual environment

4) The zipped up application release can now be published on GitHub as an official release.

   https://github.com/averylhammond/FishbowlInvoiceTool#
