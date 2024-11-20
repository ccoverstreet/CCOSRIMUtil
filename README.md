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
- Or Windows executable
- SR Module embedded in package known to work on Linux and Windows, unsure about Mac (would need wine)
    - Even if SR Module does not work on a system, the post-processing portion (bottomm left) can be used to import existing SRIM output files
- Can specify input parameters for SRIM Tables and directly run SRIM
- Can read and post-process output SRIM Tables to consistent units and converts to energy loss as a function of depth
    - Can specify packing fraction (result of porosity), density, and visualization/calculation parameters for the "annotated" plotting tab
- Results can be easily exported from the post-processing section to CSV files which can be conveniently used in other software

![GUI in use](img/GUI-demo.png)


