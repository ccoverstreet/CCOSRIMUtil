# CCO Srim Utility

This utility provides a python package and GUI for interfacing with SRIM and is used to convert the output of SRIM into an energy loss vs. depth format with sensible units. The GUI can post-process SRIM files with different packing fractions from already run SRIM results and directly run SRIM using the embedded SR Module.

## Installing

- Python
    - `python -m pip install srimutil_ccoverstreet`
    - Or in developer mode
        ```
        git clone https://github.com/ccoverstreet/CCOSRIMUtil
        cd CCOSRIMUtil
        python -m pip install -e .
        ```
- Download Windows executable

## Standalone GUI mode

- Python
    - `python -m srimutil_ccoverstreet`
- Or Windows exe
- SR Module setup known to work on Linux and Windows, unsure about Mac (would need wine)


### Normal SRIM Calculation

1. Open SRIM
2. Go to **Stopping/Range Tables**
3. For the **Ion** section, choose appropriate ion species and change the highest energy to that of the desired ion beam (ex. 950 MeV Au for M-Branch GSI)
4. Create composition
    - **Important**: Make sure to keep at least 1 character **AT ALL TIMES** in any numeric field in SRIM. If a numeric field is ever empty, it will crash the program.
5. Enter correct density
    - Usually can find this info from ICSD or an approximation using Vegard's law
    - **New Feature**: This SRIM utility now recalculates depth and energy loss based on a user provided value which means the value entered into SRIM is less important/can be ignored.
6. Set stopping power units to MeV/(mg/cm^2)
7. Press **Calculate Table**
8. You should see a popup asking about output location. Press ok on this window to continue to the SRIM output
9. You should now see a window containing text with the stopping information. Copy all the text from this window into a text file.

