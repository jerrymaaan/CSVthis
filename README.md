# CSVthis: Can Someone Visualize this?

A graphical user interface for analysing data from CSV files. 
Primarily dedicated to the project "OELEK".

Author: Jeremias Friedel

## Directory
1. [Requirements](#requirements)
2. [Program Structure](#program-structure)
3. [Convention for CSV Files](#convention-for-csv-files)
4. [Configuration](#configuration)
5. [How to use CSVthis GUI](#how-to-use-csvthis-gui)
6. [Additional](#additional)
7. [Version History](#version-history)
    
## Requirements
The following Python packages are required to run the program:
- `PyQt5`
- `pyqtgraph`
- `pandas`

You can install them via pip:
```bash
pip install PyQt5 pyqtgraph pandas
```

Should work on mac and linux (probably without the icon in taskbar). 
Developed and tested on windows 11 and python 3.13.

## Program Structure
### Main Script (app.py)
Run the program using the app.py file.
```bash
python app.py
```
### Additional Files (lib)
The /lib directory contains additional required files and modules.

### Data Directory (data)
Place all the CSV files to be analyzed in the directory /data.

## Convention for CSV Files
There are some convention for the file name and the file structure. Otherwise, the program can cause errors.
### File name
The CSV file can be named as follows:
```bash
yymmdd_hhmm_xyz
```
- yy: The last two digits of the year.
- mm: The two-digit number of the month.
- dd: The two-digit number of the day.
- hhmm: The time (hours and minutes) when the measurement started.
- xyz: An optional identifier or description of the measurement (can be any number or text).

Not naming the CSV file as described won't cause an error! It just sets the headline to the files name, instead of a nice visualisation of year, month, day, etc.

### File structure
The CSV file should contain at least one column for x data and one column for y data. 
In the first row has to be a name for each data set.

## Configuration
You can and should change settings in the config.json file, regarding your CSV files and your data.
```bash
config.json
```

### General Settings (settings)
Contains global application settings.
- use_case: Name for your personal application 
(shown in window title top left).
- version: Current version of CSVthis. No need to change.
- column_in_hh_mm_ss: Name of a column containing time values in
hh:mm:ss format and has to be converted into seconds. Recommended
to use, because CSVthis can't plot the format hh:mm:ss yet.
Set to false if not needed.
- seperator: Sets the seperator used in the CSV file

### X-Axis Configuration (x_axis)
Defines properties for the X-axis.
- label: The label to display for the X-axis (string).
- column: The name of the CSV column used for the X-axis data (string).

### Main Y-Axis (main_y_axis)
Defines the primary Y-axis, typically used for the most critical data.
- name: Identifier for the Y-axis (string).
- label: Display label for the main Y-axis (string).
- columns: List of CSV column names to include in this axis (array of strings).

### Secondary Y-Axes (secondary_y_axes)
Defines additional Y-axes for secondary data series. Each axis is represented as an object in an array.
Each axis object includes:
- name: Identifier for the Y-axis (string).
- label: Display label for the Y-axis (string).
- color: Color used for this axis and its plots (string).
- columns: List of CSV column names associated with this axis (array of strings).

### Calculated Y-Axes (calc_y_axes)
Defines additional Y-axes for data that has to be calculated. 
Each axis with calculated data is represented as an object in the array 
'calc_y_axes' from config.json file.
Each object includes:
- name: Identifier for the Y-axis (string).
- label: Display label for the Y-axis (string).
- color: Color used for this axis and its plot (string).
- formula: Contains the formula for the calculation. Use [ ] for every
column you want to use in your formula. You can use operands or brackets, 
just like you would write a formula in python. CAREFUL: CSVthis uses 
the eval()-function so commands like "os.system('rm -rf /')" 
may harm your system!
- scripts: Recommended for advanced users with Python skills! 
Instead of 
using a formula as described above you can write your
own scripts for handling data. 
It contains another object with a list of your scripts.
Each key is
the identifier of your script and will be displayed as the graphs name.
Each value contains the filename of your script.
To write your own python script 
create a new python file in /lib/personal_scripts. The script name has to
be the same as how you mentioned it in the config.json. The file itself 
has to contain a function with the same name as the file and exactly 
one parameter. This parameter contains a pandas dataframe with 
the data from your CSV file. After your calculation the function 
must return a column of a dataframe with the same length as the 
original dataframe. Take a look at /lib/personal_scripts for examples.
To understand how your return value is 
handled take a look at calc_data() in main_window.py.

## How to use CSVthis GUI
1. First choose a file to analyse in the top left corner. 
Depending on the config.json the graphs should appear in the plot 
window. By left-clicking a graph its corresponding label will be shown. 
Left-click again hide it.
2. The button "Selektieren" opens a new window to hide selected
graphs from the plot window.
3. The button "Analysieren" opens another window which shows all plotted
data points. Right click to set a start and end row in the table. 
If set correctly there should appear resulting values in the table beneath 
and some dashed lines in the plot window indicating set 
start and end value.

## Additional
### Weird Curves
If some curves in the plot can't be hidden via the select menu, 
try renaming the columns in the CSV file. 
Also rename the columns in the config.json. The following column names may
lead to weird behavior:
- T1 (T2, T3, ... seems to work)
- pe

## Version History
v1.0.1:\
Added max deviation to analyse window.

v1.0.0:\
Release of CSVthis. Includes plotting data, labeling graphs, 
showing/hiding graphs and analysing data values
(mean, standard deviation, integral)