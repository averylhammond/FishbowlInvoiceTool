Unit Test Status: [![Python-CI](https://github.com/averylhammond/FishbowlInvoiceTool/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/averylhammond/FishbowlInvoiceTool/actions/workflows/unit-tests.yml)

Code Coverage Status: [![codecov](https://codecov.io/gh/averylhammond/FishbowlInvoiceTool/branch/main/graph/badge.svg)](https://codecov.io/gh/averylhammond/FishbowlInvoiceTool)

Integration Test Status: ![Integration Tests](https://github.com/averylhammond/FishbowlInvoiceTool/actions/workflows/integration-tests.yml/badge.svg)

**************************************
INSTRUCTIONS TO SET UP FOR DEVELOPMENT
**************************************

1) Clone this repo into a project folder.

2) In order to test with example resources (payment info files and example invoices, located here
   <https://github.com/averylhammond/automated-invoice-testing>), the automated-invoice-testing repo
   has been added as a submodule to this project.

   Run git submodule update --init to clone and initialize the repo
    - The resulting folder structure is shown below:
     <PRE>- project_root/
          └── FishbowlInvoiceTool/
              └── scripts/copy_resources.sh
              └── automated-invoice-testing/
                  └── resources/</PRE>

3) Run ./FishbowlInvoiceTool/scripts/copy_resources.sh to copy the necessary configuration files. This will
   allow you to run the application using sample invoices and other config data. After running the script,
   your folder structure should have the following additions:
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
