KORF HYDRAULICS
VERSION 3.6

USER GUIDE

Page 1 of 98

OVERVIEW AND CONTACTS

OVERVIEW

Korf Hydraulics is an advanced fluid flow program for determining pressures and flow rates in pipes and piping
networks.

It is based on a novel method for solving piping problems. Study the programming principles before attempting
real calculations with this software.

CONTACTS

Korf Hydraulics is developed, maintained and distributed by Korf Technology Ltd. Refer any technical or
commercial questions to:

Email: support@korf.ca
Web: www.korf.ca

Page 2 of 98

LEGAL AND DISCLAIMER

DISCLAIMER

Absolute no guarantee is given as to the accuracy and performance of this product. The developers and
distributors are not responsible for any loss or damages incurred as a result of using this product.

LEGAL

This product is protected by copyright law and international treaties. This product is licensed, not sold and Korf
Technology Ltd remains the sole owner.

ABBREVIATIONS

Unisim - UniSim Design™ by Honeywell International Inc.
Hysys - Aspen Hysys™ by Aspen Technology Inc.
Aspen - Aspen Plus™ by Aspen Technology Inc.

Page 3 of 98

INSTALLATION

INSTALL

To INSTALL Korf Hydraulics in a new directory,

  Download ksetup-xx.exe from the Korf Technology website.
  Run ksetup-xx.exe and follow the installation procedure (xx refer to version number).
  Run Korf from the Start | Programs | Korf Technology menu or DblClick on Korf_xx.exe from

Explorer/File Manager.

Admin or Power User status is required for installation. On request Korf can provide a version that can be
installed by any user, provided all the required system files are present (normally they are).

After installation, Korf is in Evaluation mode and can be used 10 times. To continue using it after the Evaluation
version has expired, please contact Korf to obtain a license file.

The license file must be named Korf.lic and must be in the Korf library directory (default is \Lib under program
directory).

UNINSTALL

UNINSTALL Korf Hydraulics from the Start | Programs | Korf Technology menu or My Computer | Control Panel
| Add/Remove Programs. Then delete the old Korf directory and its remaining contents.

UPGRADING ISSUES

 Do not install newer versions of Korf Hydraulics in the same directory as previous versions, as the
existing pipe database (pipeid.lib), physical properties database (propa.lib) and pipe database
(pipefit.csv) will be overwritten with the newer files.
If old files (or files from other users) do not run in the newer version, please check that there are pipe
ID's for all nominal pipe sizes and pipe schedules used in the file.



 Korf will prompt the user to indicate if older files were saved using European locale (comma as decimal

place). If so, Korf will regard commas in numbers saved as text as decimal points (this is due to a bug
in older versions, see bug report for more detail).

SYSTEM REQUIREMENTS

Korf Hydraulics has the following system requirements:

IBM compatible PC


 Windows XP/Vista/7/8/10/11 (Win95/98 are no longer supported)
 Microsoft Word (for rtf report) and Excel (for xml report and csv database)
 Hard disk with about 10 MB free space

Page 4 of 98

GETTING STARTED

OPEN AN EXAMPLE

Open the example file called "Crane10.kdf" in the Sample folder (under the Korf Hydraulics program folder). It
contains three circuits from the CRANE Technical Paper 410.

 To run the example, click the Run Hydraulics toolbar button (orange triangle with pipe).
 Click OK when the Runlog is displayed.
 To view the results on the drawing, click the Show Results toolbar button (screen with orange R).
 Move the mouse over the drawing area and double click on some of the equipment.
 The screen should look as below.

BUILDING YOUR FIRST CIRCUIT

To draw a circuit consisting of a single pipe:

1.  Click to select the Feed on the equipment palette.
2.  Click on the drawing area to create the Feed. Do the same for the Product.
3.  Click to select the Pipe on the equipment palette.
4.  Move the mouse to the Feed outlet till the mouse pointer changes to an up arrow.
5.  Left click at the Feed outlet to start a pipe.
6.  Move the cursor to the Product inlet till the pointer changes to an up arrow. Click again.

Page 5 of 98

7.  To change the pipe data or physical properties, double click on the pipe label.

To run the circuit:

1.  Click the Resume Hydraulics button on the toolbar (orange triangle with pipe).
2.  When the Runlog appears click OK.
3.  Click the View Result button on the toolbar (screen with orange R).

For this pipe there are five variables, viz. inlet pressure, inlet dP, outlet pressure, outlet dP and flow rate. There
is one internal specification, viz. the pressure drop through the pipe. Thus, there are four additional
specifications required to solve the circuit.

By default, Korf assumes (specifies) a Feed pressure of 400 kPag, Feed    dP of 0 kPa, Product pressure of 50
kPag and Product dP of 0 kPa. You may delete any one of these pressures and choose to specify the flow rate
instead.

Page 6 of 98

GRAPHICAL INTERFACE

MAIN WINDOW

CREATING AND MANAGING EQUIPMENT

Create equipment by selecting them (left click) from the equipment selection palette. Then click on the drawing
area to create them.

Equipment (except Junctions and T-pieces) has specific inlets and outlets on the drawing. The inlet has a small
vertical line.

Equipment can be moved around the drawing area by dragging them (holding down the left button).

Select multiple equipment by holding down the CTRL key while clicking on them. Select the Mixer/Splitter
before selecting the connecting pipes.

Alternatively equipment can be selected by holding down the mouse button and dragging the mouse to create a
selection box.

To deselect a specific equipment, hold down the SHIFT key and click on it. To deselect all, press the Escape
key, or Equipment | Deselect All from the menu or click on an open area.

Page 7 of 98

To drag multiple equipment, hold down the CTRL key while dragging them.

Pipes stay connected while equipment is dragged.

Equipment can be edited by:
 double click on it



select it with a single left click and edit it from the menu
right click on it and select edit from the popup menu

New equipment can also be created by copying and pasting existing equipment. Select the equipment (hold
down CTRL key for multiple equipment), then select COPY (Ctl-C) and PASTE (Ctl-V) from the main or popup
menu.

If multiple pipes/equipment are copied, the connectivity information is converted correctly for all equipment
including reference equipment (pipes, pumps and valve). Only exception are equations, which have to be
changed manually.

Flow in pipes can be negative, but equipment in and outlet positions are as shown on screen. The Junction
node is different in that all pipes connect at the center of the equipment. If you want to drag a pipe away from a
Junction, you first have to click on the pipe to select it. You can then drag the pipe away from the Junction
(disconnect it).

CREATING AND MANAGING PIPES

Create pipes by selecting them (left click) from the equipment selection palette. Then click on the drawing area
or at an equipment outlet to start the pipe. The cursor is at a valid equipment outlet when it changes to an up
arrow.

Left click again to add bends to a pipe. These bends are only used for drawing purposes, not pressure drop.

End a pipe by double clicking on the drawing area, or single click at an equipment inlet. The cursor is at a valid
equipment inlet when it changes to an up arrow.

Hit ESCAPE to undo while drawing a pipe.

Pipe ends are dragged with the equipment they are connected to. Other pipe bends can be dragged when the
cursor changes to an arrow with small sizing arrows.

Dragging pipe ends away from equipment disconnects them.

To stop dragging pipes and equipment, uncheck the View | Enable Drawing menu item.

Pipes can be edited by:

 double click on it



select it with a single left click and then edit it from the menu
right click on it and select edit (or edit fluid) from the popup menu.

New pipes can also be created by copy and pasting existing pipes. Select the pipes (hold down CTRL key for
multiple pipes), then select COPY (Ctl-C) and PASTE (Ctl-V) from the main or popup menu.

Before the hydraulics can be run, all pipes must be connected to equipment. To connect an existing pipe to
equipment, drag the pipe starting end to an equipment outlet (or pipe end to an equipment inlet). Let go of the
mouse left button once the pointer changes to an up arrow.

DIALOG UNITS OF MEASURE

Page 8 of 98

The defaults units used to display data on screen and in the report are set in the Tools | Options menu.

Most of the equipment dialogs also allow the units of the entry to be different from the default units. If the user
changes the units, the number displayed in the text box will also be converted.

If the user does not want the number to change as the units are changed, the number should be removed first.
This is done as follows: double click on the entry to highlight is, press CTRL-X to cut it to the clipboard, change
the units, click again in the text box and press CTRL-V to paste it.

HELP

Two methods are used to assist the user.

 Firstly, press F1 at any time to display Help.
 Secondly, information or defaults are displayed at the bottom of dialogs for most entries.

Page 9 of 98

HYDRAULIC METHODOLOGY

DEFINING A HYDRAULIC PROBLEM

The steps to solve hydraulic circuits are:

1)  Draw the piping network on the screen drawing area.
2)
3)  Provide physical properties and conditions for every pipe.

Input the required equipment data (sizes, elevations, levels, fittings, etc).

Input properties manually or,

a)  Use defaults properties or,
b)
c)  Base properties on that of another pipe or,
d)
e)  Flash a stream.

Import properties from Hysys, Aspen or a text file or,

4)  Provide all the specifications required.
5)  Make sure the number of specifications provided equals the number required for all cases.
6)  Run the hydraulic simulation.
7)  Show the results on screen or view the result file.

If you just draw the circuit on the screen, the number of specifications provided and number required are equal,
as Korf assumes certain defaults for each line and each equipment. If you thus add a specification, you must
remove one somewhere else.

HYDRAULIC METHODOLOGY

Korf regards all flow rates and all inlet and outlet equipment pressures as unknowns or variables.

To solve these unknowns or variables, Korf performs a mass balance across every piece of equipment and a
pressure drop calculation across every pipe. These are called internal specifications.

Even with these internal specifications, a unique solution is not possible. In addition, the user needs to specify
additional pressures, flows and equipment sizes (Cv, bore, etc) to ensure a unique solution is possible. These
are called user specifications.

Keeping track of user specifications can be difficult for complex circuits. To aid the user,

 Korf continuously counts the number of user specifications provided and specifications required and

display it in the status bar.

 Korf can display the user specifications on the drawing below the respective equipment.

To solve the system, the number of specifications must equal the number of variables. When counting the
specifications, Korf assumes they are independent. If they are not, it will usually be picked up when the
simulation is run.

In general Korf can solve any problem as long as it has a unique solution and it is theoretically possible to solve
it by hand (even though this may be difficult and iterative).

It is important to realize that the sum of the individual mass balances results in an overall mass balance. Thus
Korf assures overall mass balance, and the user should not specify it. If the user try to specify an overall mass
balance, a solution will not be possible as Korf will find two identical specifications.

In addition to the internal specifications listed above, some of the user specification may require Korf to perform
a pressure drop calculation over certain equipment, such as control valves or orifices.

While there is no specific programming limit on the number for pipes, the variables used internally limits the
number of specifications to roughly 8000 and the number of pipes to roughly 4000.

Page 10 of 98

RECYCLE CIRCUITS

Korf can solve systems that consist of only a recycle circuit. The user is however required to:

  For Hydraulic calculations, add a junction or vessel to the circuit and add a feed/product line to/from it.

Do not specify this flow as zero, as Korf will determine it to be zero from the mass balances.
  For HMB calculations, a small positive flow into and out of the circuit is required. Also initialize the

vapour and liquid compositions for vessels.

  Remember to specify a pressure somewhere in the circuit.

This complication arises because purely recycle circuits require one more specification than
variables/unknowns to be completely specified (the way Korf counts and solve the circuits).

CHOKED FLOW CIRCUITS

Korf supports compressible fluids, including choked flow. If a compressible circuit does not run due to
specifications that are not independent, it may be due to a missing upstream or downstream pressure
specification around a choked point. Run (from the menu) instead of Resuming a simulation (from the tool bar) to
restart a simulation that does not run due to choked flow that incorrectly developed during preliminary iterations.

Page 11 of 98

HYDRAULIC SPECIFICATIONS

EQUIPMENT SPECIFICATIONS

Korf is extremely flexible in what you can specify. The only requirement is that the number of specifications
equals the number of unknowns.

To specify an item for a pipe/equipment, enter a value for that item. For multiple cases, separate the values
with a semi-colon (;). Multiple case entries are only supported if the label has a star (*).

If an item is not specified, simply enter nothing (leave it blank or delete the existing value) and Korf will
calculate it.

If a series circuit of lines has a specified mass flow rate, the user should specify the mass flow for ONLY ONE
of the lines, typically the pipe leaving the Feed. Korf will calculate the other flow rates in the series circuit from a
mass balance around each piece of equipment. If you wrongly specify the flow at more than one place in a
series circuit, Korf counts each as a specification (but of course this is not correct as they are not independent
specifications).

In general, flow rates can be positive or negative, but equipment has specific drawing inlets and outlets.

When you specify a pressure drop, it is always based on the drawing inlet and outlet, not the actual flow inlet
and outlet. For example, if the exchanger has a specified dP=100 and the flow is negative, the exchanger will
act as a pump. If a negative flow is required, change the dP spec to -100 or specify a rating dP, which is
pressure drop in the flow direction.

At least one pressure must be specified. Korf calculates the pressures throughout the network, and it needs a
pressure somewhere in the network to base the other pressures on. This is an obvious requirement, but it is
easily overlooked, especially for recycle networks.

Do not specify the flow rates for all the pipes entering and leaving the circuit. Korf effectively performs an
overall mass balance and at least one flow entering/leaving must be unspecified.

The orange arrow on the toolbar Resumes the hydraulic calculations from current values. If the circuit fails to
run due to choked compressible flow or poor current values, then Run the hydraulics from defaults from the
Hydraulics | Hydraulics | Run menu.

EQUIPMENT INPUTS

Korf sees a difference between SPECIFIED values and INPUT values for equipment and lines. INPUT values
(elevations, diameters, physical properties, etc.) on the forms are not counted as specifications, but the
program will assume a default value or calculate it from other input.

The liquid fraction and composition MUST be entered for each pipe, whether the flow is specified or not and
whether the lines are in series or not. When only the hydraulics is run (not heat and mole balance), Korf does
not propagate properties. Properties can be copied between pipes, based on another pipe or imported from
Hysys/Aspen/Text file to limit typing.

REMEMBER:

 THERE IS A DIFFERENCE BETWEEN INPUTS AND SPECIFICATIONS.
 LIQUID FRACTION AND PHYSICAL PROPERTIES ARE REQUIRED FOR EVERY LINE.



SPECIFY THE MASS FLOW FOR ONLY ONE OF THE LINES IN A SERIES NETWORK (IF KNOWN).

Page 12 of 98

PROCESS METHODOLOGY

PROCESS METHODOLOGY

Korf can perform a heat and mole balance (HMB) and flash calculations to determine the stream composition,
condition and physical properties in piping networks.

The following approach is used in integrating hydraulics and flash calculations:

 All flow rates and pressures are always determined by hydraulic calculations. This is based on the

current liquid fraction, temperature and physical properties.

 All compositions, liquid fractions and physical properties are always determined by the HMB. This is

based on the current flow rates and pressures.

It is clear from above that the hydraulics depends on the HMB, and the HMB depends on the hydraulics. To
initialize the system, the following sequence is recommended:

 Draw the circuit and provide the required hydraulic specifications.
 Run the hydraulics based on the defaults (liquid water) properties. This will initialize all pressures and

flows to reasonable values.

 Select a flash method, thermodynamic method and components.
 Provide the required compositions and run the HMB.
 Simultaneously run hydraulics and HMB.

If the circuit fails to converge when hydraulics and HMB are run simultaneously, then:

  Run the hydraulics till it converges.
  Run the HMB once from the Process | HMB menu.
  Repeat two steps above till the simulation no longer changes.

Korf uses an equation based approach to solving the mole and heat balance. The composition (or enthalpy) of
all streams is determined simultaneously, and not sequentially like most simulators. This works well for complex
piping networks, with many “recycle” streams.

By default velocity is not accounted for in the enthalpy balance. To include velocity, select that option from the
Process tab in the Options menu.

Page 13 of 98

PROCESS SPECIFICATIONS

The steps below are required to perform heat and mole balance calculations in Korf.

SELECT A FLASH METHOD

Select the flash method from Tools | Options | Process.

 Korf method uses built in routines for flash calculations and transport properties.
 Hysys/Unisim method links to Hysys/Unisim (if installed) to perform flash calculations and calculate

transport properties.

In both cases the mole and enthalpy balances are solved by Korf.

SELECT A THERMODYNAMIC METHOD

Select the thermodynamic method to use for K-values and enthalpy. For the Korf, Hysys and Unisim flash
methods it is set under Tools | Options | Process (see the Tools menu section).

To prevent failure due to unrealistic results during intermediate iterations, it is recommended to select the
Antoine/Ideal methods to initially obtain a realistic solution. Other methods (SRK, etc.) can then be used to
refine the solution.

Select whether the 3 phase flash algorithm should be used for the Korf flash method (version 3.4). By default
the Korf method will use a 2 phase flash algorithm.

SELECT COMPONENTS

Select the components under the Process | Components menu. The available components differ between the
flash methods, and all components must be deleted before the flash method can be changed.

SPECIFY COMPOSITIONS AND CONDITIONS

The compositions and thermal conditions (flash type, temperature and/or LF) are required at all Feeds. It is
entered at the pipe connected to the Feed (right click, Edit Fluid). In additions, it is also strongly recommended
to initialize the compositions of the vapor and liquid streams leaving vessels.

FLOW RATES AND DIRECTION

To perform the mole balance, Korf always assumes that all pipes connected to Feeds, Products and Vessels
have positive flow rates. If this is violated during an intermediate iteration, the simulation will fail and cannot
restart from current values.

First run (Hydraulics | Hydraulics | Run from the menu) and converge the hydraulics if the mole or heat balance
fail due to a wrong flow direction. This will converge the hydraulics starting from defaults (not previous values).

Flows close to zero may oscillate between slightly positive and slightly negative, which will cause the mole and
heat balance to fail. To prevent this, Korf resets all flow rates less that 0.1 kg/h to zero.

VESSELS

Page 14 of 98

Vessels represent a particular challenge. It occurs because the hydraulics step calculates flow rates, but in
vessels flow rates are clearly determined by the HMB and flash calculations. As a result, vessels become an
iteration point between the hydraulics and HMB.

In HMB vessels have the following requirements/limitations:
 Vapor must leave at the top nozzle (nozzle 1).
 Liquid must leave at the bottom nozzle (nozzle 2).
  Optionally provide a Water stream from nozzle 3.
 Other outlet nozzle must not be connected to pipes.
 Specify on the Vessel dialog that the outlet flow rates must be determined from the HMB (version 3.4).

In prior versions the user entered a "V" or initial value for the specified vapour flow rate.

 All flows associated with vessels must be positive.
  Provide initial estimates for the vapor and liquid composition leaving the vessel.

In general the compositions throughout a simulation are determined from the compositions at Feeds. For
recycle circuits with Vessels, it is important that the user also change the vessel outlet compositions else the
simulation may converge on an incorrect composition.

PUMPS AND COMPRESSORS

The horsepower of pumps and compressors are determined by the hydraulics, and is thus only approximate.
The heat and mole balance then uses this horsepower to perform a heat balance. This is to ensure consistency
with simulations where only the hydraulics is run.

Typically it is done differently in commercial simulators, as the outlet conditions and horsepower are based on
an isentropic flash and then adjusted for efficiency.

For pumps the difference is usually negligible, but for compressor the difference can be substantial.

EXCHANGERS

The outlet flash type for exchangers is determined as follows:





If the connecting line flash type is set to PH (or nothing), then the stream enthalpy is the inlet enthalpy
plus the exchanger duty.
If the connecting line flash type is set to anything else (TP or PF), then the flash is perform at these
values provided for the stream (inlet).

Initially it is better to use a TP flash for the outlet, as the exchanger duty may give unrealistic results if the flow
rate is not close to design.

PIPES

The outlet flash type for pipes is determined as follows:





If the pipe duty is set to a value or to nothing (to estimate heat loss), then an adiabatic flash is
performed at the outlet.
If the pipe duty is set to "T" (without quotes), then the pipe outlet temperature is made the same as the
inlet temperature to simulate isothermal pipe flow.

Page 15 of 98

FILE MENU

All menu items have the normal meaning, except the following.

FILE OPEN/SAVE

Korf data files (*.kdf) are comma delimited text files. Even though it is typically unnecessary to edit this file
manually, it is interesting to examine the content of this file by using a text editor (such as notepad).

The typical format of the data files are:

\Equipment type, Equipment index or number, Property, List of Values and Units

For example, the vapour physical properties (vapour density, viscosity, mole weight, compressibility and cp/cv)
for line 1 is saved as:

"\PIPE",1,"VPROP",10.6235,"kg/m3",8.6355E-03,"cP",52.381,0.91124,1.092

Currently the units of measure in the data files are ignored, and all values in the data files must be in Korf
internal units.

IMPORT

File. This command is used to import a comma delimited text file into Korf. It is typically employed to import
physical properties for pipes. For example, the following text file (created by Hysys) can be used to import the
vapor and liquid properties for line L1:

"KORF_3.0"
"\PIPE","L1","TEMP",52.25,52.25,52.25,"C"
"\PIPE","L1","PRES",398.675,398.675,398.675,"kPag"
"\PIPE","L1","OUTIN",-1
"\PIPE","L1","VPROP",10.6235,"kg/m3",8.6355E-03,"cP",52.381,0.91124,1.092
"\PIPE","L1","LPROP",570.23815,"kg/m3",0.1531296,"cP",20,"dynes/cm"
"\PIPE","L1","LF",0.4876889,0.4876889,0.4876889

The three numbers shown for temperature, pressure and liquid fraction represent the inlet, outlet and average
number. The values and units of measure MUST be Korf internal units, as shown in the example. The vapor
density is optional (can use 1.0), as it will be recalculated by Korf from the updated operating pressure.

The format for the text file is the same as for other data file created/used by Korf. The only difference is that
data files created by Korf reference the equipment index numbers (integers), whereas an imported file should
reference the equipment number (a string such as L1).

The import action for each pipe is determined by the settings in the Import Dialog (refer to Equipment | Pipes).
For example, stream data will not be imported if the stream is locked.

After the import is complete, Korf generates an Import Log. The Import log can be saved from the Hydraulics |
Result | Save Runlog. It indicates exactly what data was imported, skipped or not found.

The above example was generated in Hysys, and the code/instructions are included in the Korf Sample
directory.

Korf can also import physical properties directly from a stream in a Hysys or Aspen simulation, which is much
easier than to import text files. Refer to the discussion under Equipment | Pipes.

Simulator. This command is used to import the fluid properties of all linked streams from a Hysys or UniSim
simulation into the linked Korf pipes. The simulator stream properties are imported to both the pipe inlet and

Page 16 of 98

outlet.

The simulator file and linked stream are set on the Fluid Dialog (Import button) for each pipe. If a linked stream
is not entered, Korf will search for a Hysys/UniSim stream with the same name as the Korf pipe.

If a Hysys/UniSim file is not provided, Korf will import from the open and active case. It is preferred to open the
file in Hysys/UniSim prior to import.

An import log will be displayed indicating which pipes were imported, which were not linked and with were
locked.

PAGE SETUP

Drawing setup

This command set the size of the screen drawing area to a standard or custom paper size. It does not affect
the printed paper size, which is changed under Printer Properties (Print Drawing | Properties).

To prevent the border from being displayed, edit the data file to replace the -1 with 0 for the following entry:

"\GEN",0,"DWGBOR",-1

Report setup

A text report in rich text format (rtf) is generated after a successful run. Use this command to set the default font
size, paper size and margins used for the report. It is always in landscape orientation. Reduce the margins or
font to ensure the text does not flow over to two lines.

How these settings are used, depends on the rtf viewer. MS Word recognizes all, whereas WordPad ignores
the orientation and margins. In WordPad also ensure that word wrap is not set (View | Options | Rich Text).

SAVE SCREEN DRAWING

Page 17 of 98

Select these commands to save the client area or clipboard to a graphics file. Three graphic formats are
supported, BMP, JPG and PNG. Irrespective of which format is selected, the file is also saved in BMP format. It
is then converted to JPG or PNG if required, but the BMP file is not deleted. JPG filenames are converted to
DOS 8.3 file format.

The size of the saved BMP file depends on the screen resolution/settings and can be huge. It is recommended
to save the drawing as a PNG file and to delete the original bmp file. PNG format is preferred as it superior to
BMP or JPG for computer generated images.

Clipboard

This saves the picture that is currently in the Windows clipboard. Press the ALT | Print Screen keys
simultaneously to copy the whole Korf window (including the toolbar, status bar and menubar) to the clipboard.
Then select this menu command to save the clipboard to a file which can be included in Word, Excel or similar.
Alternatively, the picture in the clipboard can be pasted directly into compatible Windows applications.

Client

This command saves the drawing area only. The size that is stored is approximately equal to the screen size.
Zoom the drawing in/out till it fits.

Page 18 of 98

EDIT MENU

These menu commands operate on the selected equipment only. Most of these commands can also be
accessed by right clicking on the equipment.

ADD

To add equipment, select it from this menu item or from the equipment palette. Then click on the drawing area
to create it.

To add bends to the pipe, select the pipe or existing bend(s) and select Edit | Add Bends from the menu. A pipe
can have a maximum of 10 bends. These bends are only for display, and does not affect the hydraulics.

To add text, line, box or circle, select Add | Text/Line and click on the drawing area. A text string is always
added initially. To change it to a line, arrow, box or circle, double click on the top left corner. NOTE: To select a
text/line object, click on the top left corner, not the text/line itself.

EDIT

Select Edit | Equipment to edit the selected equipment. If multiple equipment is selected, the dialog for each will
open sequentially.

Select Edit | Pipe Fluid or Pipe Sizing to edit these dialogs for the selected pipes directly. This is quicker than
editing these dialogs through the pipe dialog.

Select Edit | Symbol to edit where and how the label and data for the selected equipment is located. If multiple
equipment is selected, then the dialog for each will open sequentially. The Relative X and Y dimension is
relative to the bottom left corner of the equipment.

Page 19 of 98

COPY and PASTE

Select Edit | Copy to copy all selected equipment (to internal memory).

Select Edit | Paste to paste a copy of all selected equipment. The new equipment will be located slightly right
and below the original. To drag them, hold down the CTRL key and drag them to the new location.

Equipment can also be copied and pasted using keyboard keys. Select the equipment (hold down CTRL key for
multiple equipment), then hit Ctl-C to copy and to Ctl-V to paste it.

It is not possible to copy and paste equipment between two Korf files/simulations.

SELECT EQUIPMENT

To select an equipment, left click on it. A dotted box will appear around it.

To select multiple equipment, hold down the CTRL key while clicking on equipment. Alternatively hold down the
left mouse button and drag the mouse to create a selection box.

To select all equipment, select Edit | Select All from the menu. Select Mixer/Splitter before selecting the
connecting pipes.

To deselect an equipment, hold down the SHIFT key while clicking on equipment.

To deselect all equipment, hit the ESCAPE key or select Edit | Deselect All from the menu.

To select a text/line object, click on the top left corner, not the text/line itself.

FIND

Enter the pipe or equipment number (such as L1, P2, etc) to find and highlight all equipment with that number.
Before using an equipment number in an equation, it is important to find all equipment with that number to
ensure the number is unique (only used by one piece of equipment).

Page 20 of 98

SHOW LABEL / ROTATE / FLIP

Select these actions to change the setting for all selected equipment, without going through the Edit Symbol
dialog.

PIPE COPY DATA

Physical properties are required for every pipe (if HMB is not run) and entering this data can be very time
consuming. Korf does however provide three methods to reduce the repetitive entry of data:

 Equipment defaults (including physical properties) can be set under Options. All new equipment

created will be initialized with these values.

 On the Pipe dialog (double click on a pipe), the user can import any other pipe into this pipe.

 Fluid properties for one pipe can be based on that of another pipe (on Fluid dialog).

 The Copy Pipe Data menu command (under Edit | Pipe | Copy Data) allows the user to make changes
to only one pipe, and then copy it to other pipes. It also allows the user to select more than one pipe as
target (by using the Shift and Alt keys similar to file manager) and to copy only the pipe data, physical
properties and/or fittings.

PIPE SET/CLEAR DIAMETERS

Clear diameters - This removed the input pipe size for all pipes. Thus, in the next run all pipes will be sized
based on the criteria in the Pipe Sizing dialog.

Set diameters - This sets all pipe sizes to the current calculated size.

Typically these commands are used to size pipes for the Normal case, and then fix (or set) all sizes for the
Rated and Turndown cases.

Page 21 of 98

VIEW MENU

All menu items have the normal meaning, except the following.

VIEW SPECIFICATIONS

Select View | Specifications to display the pressures, flow rates, Cv’s, etc that have already been specified. The
number of specifications displayed will match the number listed in the status bar. The specifications are
displayed even if the Label for that equipment is not shown.

VIEW RESULTS

This command will display the Property Selection Dialog (see below) from which the user can select which
results, fluid or pipe property to display on the screen drawing.

It provides a quick and easy way to review results or to ensure that all data has been entered correctly for all
equipment. To review the other results, double click on the specific equipment or view the report file.

Click OK to use the selected properties for the current simulation, or click Save As Default to store the selected
properties in the ini file for use when any simulation is opened.

RESET COLOR

The color of equipment and lines change depending on whether they are edited or whether Korf detected an
error during a simulation. Select this menu item to reset all equipment and pipes to the default colour. Default
colours can be changed under the Tools | Option menu item.

DISABLE / ENABLE DRAWING

Once the circuits have been drawn, it is often convenient to prevent moving pipes or equipment while data is
entered for the pipes and equipment. This can be achieved by disabling the drawing from the View |
Enable_Drawing menu, or by clicking the arrow on the toolbar.

Page 22 of 98

HYDRAULICS MENU

TITLE

This dialog sets the text that is displayed in the drawing title box (at the right bottom corner) and in the report
file. The current date and time is used if nothing is entered.

CASES

Korf supports a powerful case management methodology. The intention of multiple cases is to perform multiple
hydraulic runs for:

 The same hydraulic circuit (same hardware),
 At the same physical properties (same fluid),
 Using different flow rates, pressures and fluid levels.

For example, the user can have normal, rated, turndown and shutoff cases to accurately size and specify
pumps and control valves.

To run more than one case, enter multiple values for the pipe/equipment specifications, separated by a
semi-colon (;). Multiple case entries are only supported for labels that have a star (*).

The first value entered for a specification, is regarded as case 1. The second value is case 2, etc.

If a value is omitted for a case, Korf will use the last value provided. For example, if the specification is
“300;100”, Korf will use 300 for the 1st, and 100 for the 2nd, 3rd, and all subsequent cases.

If a specification is not present for a case, enter nothing. For example, if a specification is “300;;100”, Korf will
use 300 for the 1st, no specification for the 2nd, and 100 for the 3rd and subsequent cases. Enter “;300;100”
and “300;100;” for example if the first or last case has no specification.

To determine which cases to run, select the Hydraulic | Cases menu to display the dialog shown below.

Case Number: Indicate which cases to run, and in what order. Separate case numbers with a semi-colon. For
example, enter “3;1;2” to run case 3, then case 1 and then case 2. After the run, the simulation is left with the
last case results (case 2 in the example). If only one case number is provided, only that case is run.

Case Descriptions: Enter the description for each case, separated by a semi-colon.

Case Reporting: Indicate the extent of reporting required for each case (in the report file), separated by a
semi-colon. Valid entries are:

-1 = none
0 = full
1 = pressure profile only
3 = pressure profile and streams only

Page 23 of 98

4 = equipment only

For example, if the user enter “0;1;1”, case 1 will be reported in full, while case 2 and 3 will only contain the
pressure profile report.

CASE INPUT DIALOG

With many cases it is difficult to input and check all values on a single line, and Korf provides a Case Input
Dialog to simplify input.

Double click on any text input field that support case values (descriptions has a *). This will bring up the Case
Input Dialog as shown below.

Note: By default this dialog is disabled. To enable, select Show Case Dialog from the Tools | Options
menu.

Cancel – Click Cancel to close the dialog and return to the unchanged text input field.

Specification – To provide a specification, enter the value next to the appropriate case. Hit Enter and the OK
button when done. To provide no specification, enter “n” or “N”. As described above, the “n” or “N” will be
displayed as “;” on the pipe/equipment text input field. For the dialog shown, the equipment specification will be
“400;;300”.

SPECIFICATIONS

The number of specifications provided and number required from the user (user specifications) are
continuously displayed in the status bar. For a problem to have a unique solution, they must be equal.

In addition, this command display the total number of specifications (internal and user) and total number of
variables (pressures and flows). For a simulation to have a unique solution, they must be equal.

HYDRAULICS

Run

Select this command (or from toolbar) to run the problem starting from default values. If a previous run have
resulted in unrealistic physical properties or if choked flow incorrectly prevent a simulation from resuming, you
have to use this option (instead of resume) to ensure physical properties are initialized to realistic numbers.

Resume

Page 24 of 98

This command runs a problem by initializing from the previous results. This can reduce the number of iterations
significantly.

The behavior of oscillating systems can be traced by repeatedly hitting Resume, with the maximum number of
iterations set to 1 and with results shown on the drawing.

RESULTS

Runlog

Korf generates a runlog in plain text format when:

 Hydraulics is run.
 Heat and mole balance is run.
 Files are imported.

The primary purpose of the runlog is to trace the convergence progress and list any errors or warnings.

The Runlog can be opened in the default Windows “txt” viewer by selecting Hydraulics | Results | View_Runlog
from the menu.

Any runlog is temporarily stored in a file called “runlog.txt” in the data directory and is overwritten when a new
runlog is created. To store a runlog, select Hydraulics | Results | Save Runlog from the menu immediately after
it is generated.

It is recommended to associate Notepad with *.txt extensions. If you want a different viewer, change the
Windows file associations.

Report

Korf generates a report file in Rich Text Format (rtf) when the hydraulics is run. If any input changes, the
simulation must be rerun to generate a new report file.

The report file is in the default engineering units, and is the primary method of displaying results to the user. It
can be viewed with the default Windows viewer by selecting Hydraulics | Results | View_Report from the menu.

Results are temporarily stored in “resulth.rtf” in the data directory. Result files are overwritten if the simulation is
run again. To store a result file, select Hydraulics | Results | Save Report from the menu.

If the report file only contains the words "End of file }", then the simulation did not run successfully. Review the
log file (Hydraulics | Report | View Runlog) to identify the reason.

It is recommended to associate MS Word or Wordpad with “rtf” extensions. The file associations can be
changed in File Explorer (View | Folder Options | File Types). The easiest method is to delete the existing
association. Then double click on the rtf file and select the appropriate viewer from the dialog box. In WordPad
(and similar viewers), ensure word wrap is disabled.

Use Courier font, size 7 or 8, landscape page setup and 1-2 cm margins to view the report. These defaults can
be changed under File | Page Setup or modified in the word processor.

Circuits reported in the report file always start at a feed, junction or vessel.

Excel Report

Korf generates an XML file compatible with Excel when the Hydraulics or both the Hydraulics & HMB are run.

Page 25 of 98

After viewing this file in Excel, store it in the native Excel format (not xml) if required for later use.

IMPORTANT    - AFTER VIEWING RESULTS, ALWAYS CLOSE THE WORD / WORDPAD / EXCEL
DOCUMENT ELSE THE RESULTS FOR THE NEXT RUN CANNOT BE SAVED/VIEWED !

Page 26 of 98

PROCESS MENU

COMPONENTS

This dialog sets the components that are used throughout the current project. The dialog enables components
to be added and sorted in any order preferred by the user.

A maximum of 30 components can be selected.

The components that can be selected, depends on the selected Flash method. All components must be deleted
before the flash method can be changed.

For the Korf flash method the components are arranged in order of increasing carbon number. Hit the - key to
jump to the next carbon number.

To find a specific compound, enter part of the component name, formula or CAS number and click Find.
Continue clicking to cycle through all the matching compounds. A "not found" message will display once the
end is reached, and searching will start from the top again.

Hysys and UniSim components can be match exactly by entering the CAS number from these simulators.

Double click on a Database component name to display more information.

Only the Korf method natively support user pseudo components. A two step process is required to use pseudo
components:

  Step 1 - Define the pseudo component (see below).
  Step 2 - Select the pseudo component for use in the simulation (see above).

If Hysys or UniSim is selected as the flash method and "Case" as the thermodynamic method (both under Tools
| Options | Process), then only the Case Import/Remove buttons are enabled on this dialog. Use Case
Import/Remove to import or remove the component list from the open and active Hysys/UniSim case. In this
case the component list is managed in Hysys/UniSim and cannot be changed in Korf.

Page 27 of 98

DEFINE PSEUDO COMPONENTS

If a component is not in the default data base, the user can define a pseudo component. Pseudo components
are stored in the simulation data file (not the component data base).

Click on Add to add a new pseudo component.




If it is based on NONE, the initial boiling point and density is set to 400 K and 800 kg/m3.
If it is based on a library component, all initial properties are based on that library component. This is an
easy way to clone and modify a library component.

After adding a pseudo component, enter all the available physical properties. At the very minimum the user has
to provide the normal boiling point and standard liquid density.

Select an existing pseudo component and click Delete to remove it.

RUN

Heat and Mole Balance (HMB)

This will perform one mole balance and one heat balance only. The hydraulics will not be run.

The mole balance will be based on the current mass flow rates, and the flash calculations will be based on the
current pressures. All temperatures, liquid fraction and properties will be overwritten.

This option is very useful in cases where the combined hydraulics and HMB calculations fail.

Hydraulics and HMB

Select this command (or from the toolbar) to simultaneously run the hydraulics and HMB till the problem
converges.

Page 28 of 98

It is strongly recommended that this option not be used until a preliminary hydraulics run has been performed
separately. Carefully review the runlog and report file for errors or warnings.

RESULTS

Runlog

The Runlog is viewed and saved under the Hydraulics | Results menu.

Report

Korf generates a report file in Rich Text Format (rtf) when the HMB is run. If any input change, the simulation
must be rerun to generate a new report file.

The report file is in the default engineering units, and is the primary method of displaying results to the user. It
can be viewed with the default Windows viewer by selecting Process | Results | View_Report from the menu.

Results are temporarily stored in “resultm.rtf” in the data directory. Result files are overwritten if the simulation
is run again. To store a result file, select Process | Results | Save Report from the menu.

It is recommended to associate MS Word or Wordpad with “rtf” extensions. The file associations can be
changed in File Explorer (View | Folder Options | File Types) or search for Default App Settings. Prior to
Windows 10 the easiest method is to delete the existing association, then double click on the rtf file and select
the appropriate viewer from the dialog box.

In WordPad (and similar viewers), ensure word wrap is disabled.

Use Courier font, size 7 or 8, landscape page setup and 1-2 cm margins to view the report. These defaults can
be changed under File | Page Setup or modified in the word processor.

IMPORTANT    - AFTER VIEWING RESULTS, ALWAYS CLOSE THE WORD/WORDPAD DOCUMENT ELSE
THE RESULTS FOR THE NEXT RUN CANNOT BE SAVED/VIEWED !

Page 29 of 98

TOOLS MENU

OPTIONS

This dialog is used to set the defaults for the current project as well as the defaults for all projects.

 To set the defaults for the current project, select the defaults required and hit the OK button. The

defaults will be associated with the current project, and saved in the project's data file (kdf extension).

 To set the defaults for all projects, including the current one, select the defaults required and hit Save

as Default button. The defaults will be saved in the korf.ini file and used for all projects.

Most of the default options are self explanatory, except the following:

OPTIONS - GENERAL

Maximum Number of Iterations

Korf will stop the current simulation after the maximum number of iterations are reached.

The next simulation can be:

  Resumed by using the current calculated values (from toolbar or menu)
  Ran by using default initial values (from menu only)

Advanced Tips:

Page 30 of 98

If Korf oscillates, it is often useful to set the maximum iterations to 1, and hit the Resume button. The displayed
results on the drawing will indicate which variables are causing the oscillation.

Pump and Compressor Minimum Curve Slope

Pump/compressor curve are naturally divergent, and require special procedures in Korf. The curve slope is
artificially made more negative to improve convergence, at the expense of more iterations. To reduce the
number of iterations, you can enter a less negative value (such as -1 for compressors or 0 for pumps), but the
simulation may then not always converge.

Dampening Factor

Korf uses successive substitution between iteration and dampening is generally not recommended. For certain
circuits this may however lead to non-convergence, which are sometimes resolved by using a dampening factor
between 0 and 1 (say 0.25). Dampening is only applied to flow rates and pump/compressor/orifice/control valve
pressures.

Import of Fluid Properties

Fluid properties can be imported into one pipe (on the Fluid dialog) or for all pipes that are set up (under the
File | Import | Simulator menu). Before importing fluid properties, the source and file name must be selected
here.

Conditions and properties can be imported from:

 Text file (formatted)
 Aspen simulation
 Hysys/Unisim simulation

If a file name is not selected for Hysys or Unisim, then the active file that are currently open will be used.

OPTIONS - INTERFACE

Page 31 of 98

Colors

The color of equipment change depending on their current status. Use these three color boxes to set the color
that is used when the equipment is first drawn, when the equipment has been edited or when an error
conditions exist for a piece of equipment after the simulation is run. The color is reset to the current On Draw
color from the View | Reset Color menu command.

Grid

Select the grid size in the drop down box (100 or 50 twips). All equipment and pipes will snap to the nearest
grid. Select a grid size of 1 to disable the grid.

Select Show Grid to view the grid coordinates on the drawing. NOTE: Showing the grid can slow down drawing
considerably.

Show Case Dialog

Select this option to show the Case Input Dialog if the user double clicks on text input. See Hydraulics Menu.
This is the only way to display the Case Input Dialog.

File extension

Click on the FileExt button to associate kdf files with Korf. During installation kdf files will also be associated
with Korf, but this button is useful if another application changes the association.

Folder Locations

The user can change the location of the License, Library, Ini and temporary Data folder by editing the Korf.cfg
file in the program directory before starting the program. The default settings are:

gDirLic={app}\Lib\
gDirLib={app}\Lib\

Page 32 of 98

gDirIni={commonappdata}\Korf\Korf_33\
gDirData={commonappdata}\Korf\Korf_33\

Korf only supports the following variables for folders: {app}, {appdata}, {localappdata}, {commonappdata} and
{commondocuments}.

OPTIONS - HYDRAULICS

Use this dialog to edit the pressure drop methods.

Fittings

Select whether the pressure drop caused by fittings is based on the Equivalent length (EL), Crane or Hooper
2K method. Crane is the default method, but the 2K method is recommended for low Re numbers. The
Equivalent length method multiplies the fitting L/D values with the actual friction factor, whereas the Crane
method multiplies the fittings L/D value with the fully turbulent friction factor (fT).

Strictly speaking, the fT value for fittings using the Crane method should always be based on the roughness for
clean commercial steel, but this is not always followed in industry. The default is to base fT on steel roughness
(version 3.4), but the user can use the actual pipe roughness by deselecting the appropriate check box on this
dialog.

Compressible Pressure Drop

Select the method for compressible flow. Isothermal compressible flow is the default. Incompressible flow with
the Log acceleration method will give identical results to the Isothermal method. Select the HEMOmega method
(with adiabatic flash calculations) to approximate adiabatic compressible flow.

Page 33 of 98

Elevation 2-phase method

This option selects the density that is used for two phase elevation pressure drop calculations in pipes. It does
not apply to single phase flow.

Currently Korf supports the homogenous, liquid only (for start up situations), Flanigan, GPSA and Hughmark
two phase density. Flanigan is the default and recommended option.

For consistency with other methods, the Flanigan method was changed in version 2 to include the vapor
density. This will result in a small increase in the static loss compared to previous versions.

In two phase flow an elevation pressure drop is associated with all up flow sections. The pressure gain for
down flow sections is ignored, as is common engineering practice. The overall elevation change is determined
from the equipment elevations, and the sum of the internal up flow sections are set by the Sum Of Elevation
entry (Pipe dialogs).

Acceleration

This option selects the method that is used to calculate the pressure drop due to acceleration of the fluid in a
pipe.

None ignores the acceleration pressure drop.

Log assumes the acceleration pressure drop is proportional to ln(density out / density in). It is not often used,
but has the benefit that results from the Darcy equation with Log acceleration pressure drop are identical to the
isothermal compressible method for gases.

Homogeneous assumes the acceleration pressure drop is proportional to 1/(density out) – 1/(density in).

Two momentum acceleration methods are supported. They are identical, except that different hold up methods
(Hughmark or Lockhart-Martinelli) can be used.

Sonic Velocity Method

This option selects the method that is used to calculate the choked flow velocity in pipes. The selected method
will be used for all types of flow, including liquid and two-phase flow.

Adiabatic applies to adiabatic gas flow.

Isothermal applies to isothermal gas flow. It is the same as the Adiabatic method, except Cp/Cv = 1.

HEMOmega is based on the modified omega method and applies to gas, liquid and two-phase flow. It is
superior to the Adiabatic or Isothermal methods, but more complicated and thus more likely to cause
convergence issues.

Orifice 2-phase dP

This option selects the method that is used to calculate the 2-phase pressure drop through orifices, perforated
plates, flow nozzles and venturi’s.

Homogeneous assumes the 2-phase fluid is a homogeneous non-flashing mixture. It is based on the
Masoneilan method for control valves.

SumOfArea assumes the orifice bore is the sum of the area required for non-flashing vapour and liquid flow.
This was the default in previous versions and is based on the Murdock method, using a Murdock coefficient of
1.0 (compared to 1.26 recommended by Murdock). This method overpredicts flow and is no longer
recommended.

Page 34 of 98

HEMOmega combines the modified Omega method with the modified Diener-Schmidt non-equilibrium model
and the theoretical Buckingham equation. It is applicable to short and long restrictions with support for two
phase flashing and non-flashing flow as well as bubble point and sub cooled flashing liquid flow. The main
modifications are:

  Omega is calculated from the inlet and outlet properties, instead of the properties from an isentropic

flash at 70-90% of the inlet pressure. The user can however estimate omega separately and override
the calculated value.

  A custom curve fit based on the inlet vapour fraction and orifice/nozzle length is used instead of the
Diener-Schmidt equation. A length of 0 meter results in the frozen model and a length above 1-2
meters results in the homogeneous equilibrium model.

Control Valve 2-phase dP

This option selects the method that is used to calculate the 2-phase pressure drop through control valves.

Homogeneous assumes the 2-phase fluid is a homogeneous    non-flashing mixture. It is based on the
Masoneilan method.

SumOfCv assumes the valve Cv is the sum of the Cv required for non-flashing vapour and liquid flow. This was
the default in previous versions and is based on the Murdock method for orifices, assuming a Murdock
coefficient of 1.0. This method generally over predicts flow and is only recommended for two phase flow with
low (or zero) vapour fraction.

HEMOmega combines the modified Omega method with the modified Diener-Schmidt non-equilibrium model
and the theoretical Buckingham equation. It supports two phase flashing and non-flashing flow as well as
bubble point and sub cooled flashing liquid flow. The main modifications are:

  Omega is calculated from the inlet and outlet properties, instead of the properties from an isentropic

flash at 70-90% of the inlet pressure. The user can however estimate omega separately and override
the calculated value.

  A custom curve fit based on the inlet vapour fraction and orifice length is used instead of the

Diener-Schmidt equation. A length of 100mm is assumed for control valves, but can be changed by
editing the data file.    At 50-100 mm it matched the Diener-Schmidt equation.

Control Valve Liquid Choked Flow

This option selects the method that is used for flashing liquid choked flow through control valves.

2Phase uses the the 2-phase method selected above for flashing liquid choked flow.

FL uses the the FL method in Masoneilan/ISA for flashing liquid choked flow. It will only be used for control
valves with liquid at the inlet and 2-phase flow at the outlet, otherwise the 2-phase method selected above is
used.

OPTIONS - PROCESS

Use this dialog to edit the flash calculation methods.

Page 35 of 98

The user can only change the selected flash method if no components are currently selected for the project.
Thus, delete all components to enable this option.

Currently Korf supports three flash methods, viz. Korf, Hysys and UniSim. In previous version PPP was
supported, but that has been discontinued.

OPTIONS – KORF FLASH METHOD

Korf provides built-in support for flash calculations based on the algorithms of Michelsen and Mollerup.

These algorithms are stable and robust, but not equivalent to those in commercial simulators. In addition, the
Korf method currently only applies to:

 Non-polar mixtures of defined composition
 Pure water and steam

Korf Thermodynamics

Korf support two K-value methods:

 Antoine. K-values are based on the vapor pressure (Ps).

Ki = Pis / P

The vapor pressure is calculated from the Antoine or extended Antoine equation. Pressure is in kPaa
and temperature in K.

ln(Ps) = A + B/(T+C)

Page 36 of 98

ln(Ps) = A + B/T + D*ln(T) + E*T^2

In the case of water, the vapor pressure is calculated from the IF97 correlation in the sub-critical region.

 SRK. K-values are based on the ratio of the fugacity coefficients, which are calculated from the original,

unmodified Soave Redlich Kwong cubic equation of state.

Ki = ФiL / ФiV

Both K-value methods only apply to pure components or mixtures of non-polar components.

Korf support three enthalpy methods:



Ideal. This method assumes the vapor enthalpy equals that of an ideal gas. Liquid enthalpy equals the
vapor enthalpy minus the heat of vaporization. Mixtures are based on the molar average. The enthalpy
basis is H=0 for ideal gas at 0 K.

Heat of vaporization for each component is calculated from the Watson equation.

Hv = Hvb * ((1 – Tr) / (1 – Trb))^0.38

 SRK. Vapor and liquid phase enthalpies are calculated from the original, unmodified Soave Redlich

Kwong cubic equation of state. The enthalpy basis is H=0 for ideal gas at 0 K.

 WS97. Steam tables based on the International Association for the Properties of Water and Steam
Industrial Formulation 1997 (IAPWS-IF97). This formulation is recommended by the IAPWS as the
basis for contracts beginning January 1, 1999, with respect to performance test calculations for
machinery and systems using steam. The IAPWS-IF97 replaces the previous IFC-67. The enthalpy
basis is U=0 and S=0 for saturated liquid water at the triple point.

The enthalpy for the entire stream is calculated from this formulation. This enthalpy method should only
be used if the entire simulation contains only water/steam, and Korf will print a warning message if any
stream contains less than 99.9% water/steam.

For entropy, Korf will use IF97 with the WS97 option, and SRK for all other cases.

Resume Flash Calculations. If this option is selected, Korf will use the current temperature or pressure as
starting point for the next flash calculation. This greatly speed up convergence for subsequent runs. For certain
flash calculations (bubble or dew point flashes), more than one solution is possible in the retrograde region and
care should be used in selecting the initial temperature or pressure to ensure the desired solution (normal or
retrograde) is obtained. If this option is not selected, Korf always starts the flash calculation at 300 K or 200
kPaa.

3 Phase Flash. By default the 2 phase flash algorithm is used, but the option is available to use a 3 phase
algorithm (version 3.4). The 3 phase algorithm does not include phase stability analysis (tangent plane
analysis), and the user has to provide the heavy phase component. The default is WATER, and can be
changed by editing the data file.

"\GEN",0,"MHVYCOMP","WATER"

Include KE in Flash Calculations. If this option is selected, Korf will account for fluid velocity in the enthalpy
used for flash calculations.

Heat Loss Method. Korf supports two algorithms for estimating heat loss from pipes, Direct and NTU. Both will
give similar results, but one may be more stable than the other under certain conditions. Prior to version 3.3,
only the Direct method was available. The NTU method requires that a successful flash is possible for the
process fluid at the ambient temperature.

Korf Binary Interaction Coefficients

Page 37 of 98

Korf supports binary interaction coefficients for the SRK equation. By default binary interaction coefficients are
only provided for water+H2S and water+NH3.

Binary coefficients are stored in the propkij.lib file located in the library folder (default is \Lib sub folder). The
format of the file is:

"\KIJ",CompIndex1,CompIndex2,Coefficient,"Comment"

Component indexes are displayed under Tools | Component Data. To add another set, add the following to the
bottom of the file (for example N2 and H2S):

"\KIJ",30,22,0.14,"Nitrogen+H2S"

If the flash calculations fail for large binary interaction coefficients, reduce the Dampening Factor under Tools |
Options | Process tab.

Korf Transport Properties

Liquid density.

Water. If the stream is pure water (+99.9 % H2O) Korf calculates the liquid density from the IF97 steam tables.

Mixtures. For mixtures the liquid density is calculated in two steps.
Firstly, the saturated density (or specific volume) is calculated using the modified Rackett equation (API
Technical Data Book 6A3.1).

V = Sum (xi * RTci/Pci) * ZRA ^ (1 + (1 - Tr) ^ (2 / 7))
ZRA = Sum (xi * ZRAi)
ZRAi = based on known density in database.

Secondly, this density is corrected for pressure based on the Tait-COSTALD method (API Technical Data Book
6A3.4). If the temperature is more than 95% of critical (based on 6A3.4), the density is calculated from the SRK
equation.

Liquid viscosity.

Water. If the stream is pure water (+99.9 % H2O) Korf calculates the liquid viscosity from the IF97 steam
tables.

Mixtures. For mixtures the liquid viscosity is calculated in three steps.
Firstly, the component viscosity at atmospheric pressure is calculated from the database using the following
correlations. Viscosity is in cP and temperature in K.

Eqn 3.  Ln(Visc) = A+B/T+C*T+D*T^2
Eqn 4.  Ln(Visc) = A+B/T+C*Ln(T)+D*T

Secondly, the mixture viscosity at atmospheric pressure is calculated using API 11A3.1:

Visc1 = Sum (xi * Visci^1/3)^3

Thirdly, the mixture viscosity is adjusted for pressure using API 11A5.7:

Log(Viscp/Visc1) = P(psig)/1000 * (-0.0102 + 0.04042 * Visc1^0.181)

Liquid surface tension.

Water. If the stream is pure water (+99.9 % H2O) Korf calculates the liquid surface tension from the IF97 steam
tables.

Mixtures. For other mixtures the liquid surface tension is calculated from the Corresponding state and
Brock+Bird methods as implemented in Reid et al. NOTE: This method is not valid for components with
hydrogen bonding (alcohols, etc).

Page 38 of 98

Liquid thermal conductivity.

Water. If the stream is pure water (+99.9 % H2O) Korf calculates the liquid thermal conductivity from the IF97
steam tables.

Mixtures. For other liquid mixtures the thermal conductivity is estimated from API 12A3.2 with metric units per
Riazi. It is based on the average fluid boiling point.

Vapor density.

Vapor density (and total density) is calculated by the hydraulics, and is based on the vapor compressibility (Z).
The vapor compressibility is calculated from IF-97 steam tables for water/steam streams (+99.9 % H2O), and
from the SRK equation for all other streams.

Vapor viscosity.

Water. If the stream is pure steam (+99.9 % H2O) Korf calculates the vapor viscosity from the IF97 steam
tables.

Mixtures. For mixtures the vapor viscosity is calculated in three steps.
Firstly, the component viscosity at low pressure is calculated from the Thodos and Yoon method, as presented
in the API Technical Databook 11B1.6. Special correlations are used for helium and hydrogen, and water is
calculated from the steam tables.

Secondly, the mixture viscosity at atmospheric pressure is calculated using the Maxwell equation:

Visc = Sum (yi * Visci * Mwi^½) / Sum (yi * Mwi^½)

Thirdly, the mixture viscosity is adjusted for pressure using the Dean and Stiel method as presented in API
11B4.1.

Vapor Cp/Cv ratio.

The k vale (Cp/Cv) value calculated by Korf is a pseudo-ideal value based on the following equations:

k = Cp / (Cp - R)
Cp = Based on the enthalpy method specified

Vapour thermal conductivity.

Water. If the stream is pure water (+99.9 % H2O) Korf calculates the vapour thermal conductivity from the IF97
steam tables.

Mixtures. For other vapour mixtures the thermal conductivity is estimated from API 12B3.1 with metric units per
Riazi. It is based on the average fluid molecular weight.

Pseudo Components

The user has to provide at least the normal boiling point and standard liquid density. Unknown properties are
estimated as follows:

  Molecular weight is based on Riazi and Daubert per API 2B2.1
  Critical temperature, critical pressure and critical volume are based on Riazi (2005).
  Acentric factor is based on API 2A1.1.
  Vapour pressure is based on modified Antoine equation.

Ideal heat capacity is based on Lee-Kesler (Riazi 2005).
  Heat of vaporization is based on Riazi and Daubert (1987, per Riazi 2005).
  Liquid viscosity is based on API 11A4.2.

Page 39 of 98

OPTIONS – HYSYS™ OR UNISIM™ FLASH METHOD

If Hysys™ or Unisim™ is installed on the same PC as Korf, it can be used by Korf to perform the flash
calculations via an OLE interface.

There are several options to link these programs with Korf to obtain stream properties:



Import stream properties. First simulate the circuits in Hysys/UniSim. Secondly simulate the same
circuits in Korf. Thirdly, link the Korf pipes to the Hysys/UniSim streams and import the stream
properties. This can be imported for each stream (from the Fluid | Import dialog) or for all linked
streams at once (under File | Import | Simulators). As only fluid properties are imported, the
Hysys/UniSim simulation can contain any pure, pseudo or assay components.

  Utilize Hysys/UniSim for flash calculations. Firstly, the circuits are only drawn and simulated in Korf.
Secondly, the user selects Hysys/UniSim as the Flash method and any EOS (except Case) as the
Thermo method. Thirdly, the user selects the pure components. Lastly, the user enters the composition
and flash type for all pipes leaving Feeds and run the heat and material balance. Only mixtures of pure
components are supported and default settings for the EOS are used.

  Utilize a Hysys/UniSim Case for flash calculations. This option is selected by setting the

Thermodynamic method to "Case". It is similar to the above option, except that the thermodynamic
method and components are selected in the Hysys/UniSim case file. The Case components must then
imported into Korf (Process | Component) from the open and active Hysys/UniSim Case prior to
entering the compositions in Korf. This allows the user to use pseudo and assay components. The total
number of components is limited to 30.

Hysys™ or Unisim™ Thermodynamics

The thermodynamic method used by Hysys™ or Unisim™ can be set on the Options dialog or by editing the
following entry in the data file, replacing the SRK string with the required method.

"\GEN",0,"MHYSYS","SRK"

The thermodynamic methods available depends on Hysys™ or Unisim™, but the following options may be
available:

PengRob, SRK, SourPR, SourSRK, KDSRK, ZJRK, PRSV, Wilson, Uniquac, Nrtl, VanLaar,
Margules, CNull, ExtNRTL, GenNRTL, CS, GSD, Antoine, BraunK10, EssoTabular,
AsmeSteamPkg, Steam84Pkg, Amine, TabularPkg, LKP and AcidGasPkg.

Hysys™ or Unisim™ can be made visible on the Options dialog or by adding the following command to the
korf.ini file:

HysysView=-1

The AcidGasPkg uses reaction sets and support was added in version 3.4.1. The user has to select the correct
components.

Hysys™ and Unisim™ are completely separate products from Korf, and Korf does not provide any support for
this product or endorse it in any way. Korf will only respond to interface questions regarding this product.

EQUIPMENT DEFAULTS

The defaults for all equipment and fluid properties can be changed. All new equipment (for the current project)
created from then on will be initialized with the new default values.

These defaults are stored in the project data file only, not the korf.ini file, and thus applies to the current project
only.

Page 40 of 98

Template File

All dialog entries can be modified and stored in a template file that will be read by Korf during startup (since
version 3.5.2). The file must be named Template.kdf and stored in the Korf program folder.

This allows company specific defaults, a different pipe database and/or pseudo components to automatically be
used by all users with the template file.

Korf reads files in the following sequence:
  Korf.cfg (contains file locations)
  Korf.ini (data from dialogs with Save As Default button)
  Template.kdf (all simulation data)
  Data file (all simulation data, file opened by user)

Data in a latter file overrides data read earlier.

EQUIPMENT CALCULATIONS

This dialog provides a quick method for performing Pipe, Control Valve and Orifice calculations. The main
benefits are:

 Pipe 2-phase pressure drop methods are run simultaneously (for comparison).
 Control Valves and Orifices are sized without running a full simulation.

The equipment calculations are subject to the same limitations as in the main program (refer to the Pipes,
Control Valve or Orifices in Equipment section of the Help file). Additional points worth noting are:

Page 41 of 98

Input must be provided for all White cells. Grey cells are calculated.


 Less input error checking is done.
 For significant flashing across valves/orifices, use the average vapour and liquid flows, but inlet vapour

density (per equipment section in Help file).

 For Orifices the permanent, non-recoverable pressure drop must be input. The flange dP is calculated.
 The input/results cannot be printed directly. It is however stored in the data file and can be copied and

pasted to Excel, etc.

  The HEMOmega method is not supported on this dialog.

PIPE DATABASE

The default pipe data base is stored in the pipeid.lib file in the Korf library folder. The default data is only used
for new simulations, as the pipe data is also stored in the data file.

Use the dialog below to modify the pipe data.

Click OK to keep the changes only for the current simulation. Changes are stored in the data file.

Click Save to File to change the default pipe database, It is strongly recommended that changes to the pipe
database be kept to a minimum for the following reasons:

 Changes are permanent and cannot be undone. To revert back to the original data file, delete the

modified pipeid.lib and copy/rename the pipeid.org file to pipeid.lib.

 During future upgrades all changes will be lost. The user would have to manually transfer the data to



the new pipe database.
If a newer version is installed in the same directory as an older version, the existing pipe database will
be overwritten and the user will lose all changes.

Instead of modifying the pipe database, the following is recommended:

If only a few custom pipes are required, simply input them as IDs in the Pipe Dialog.

 Click OK (instead of Save to File) to save the changes only for the current simulation.

Page 42 of 98

Material identifies the pipe database that is displayed. Currently Steel, Ductile Iron and PVC are supported.
Please contact Korf on instruction how to add more databases.

 Steel is based on ASME B36.10M-2004 Welded And Seamless Wrought Steel Pipe. Table 1. The

default roughness is 0.0457 mm, based on Crane.

 Ductile Iron is based on ANSI/AWWA C150/A21.50-02. AWWA Standard For Thickness Design of

Ductile Iron Pipe. Table 5 and 15. The default roughness is 0.122 mm, based on the Ductile Iron Pipe
Research Association (from A.M. Friend, "Flow of Water in Pipelines").

 PVC is based on ASTM D1785 - 04a. Standard Specification for PVC Plastic Pipe, Schedules 40, 80,

and 120. Table 1 and 2. The default roughness is 0.001524 mm, based on Crane for smooth surfaces.

Roughness indicates the default absolute roughness for this material. This default roughness will be used if
nothing is entered for Pipe Roughness on the pipe dialog.

Non-standard sizes is a semi-colon separated list of non-standard nominal pipe sizes for this material. These
sizes will be ignored during the pipe sizing routines.

Sizing IDmax and Schedule. During pipe sizing, Korf selects a schedule based on the calculated ID of the pipe.
This list provides the schedule and corresponding maximum ID that will be used for this material.

Nominal/ID/Schedule Table. This table contains the ID and OD for all Nominal/Schedule combinations. Sizes
must be in ascending order and entries must exist for all pipes that can be selected during sizing (based on
Sizing IDmax and Sch).

COMPONENT DATABASE

This dialog allows viewing the component database, which is stored as propa.lib in the Korf library folder.

Changes to the default components are no longer allowed. Instead, create a pseudo component based on a
library component, change as required and use that in the simulation.

Page 43 of 98

The component database is based on The Properties of Gases and Liquids, Third Edition, Reid, et al, used with
permission (copyright The McGraw-Hill Companies, Inc). Missing or incorrect data was largely taken from the
Properties of Gases and Liquids, 4rd Edition, by Reid, et al. and the API Technical Data Book, 1997.

The Korf pure component database contains the entries listed below. Water is used as an example.
Name    = WATER
Formula = H2O
MW      = 18.015 (Molecular weight)
TFP(K)  = 273.2  (Freezing point in Kelvin)
TBP(K)  = 373.2  (Normal boiling point in Kelvin)
TC (K)  = 647.3  (Critical point in Kelvin)
PC(kPaa)= 22120  (Critical pressure in kPaa)
VC(m3/kmol)= 0.0571 (Critical volume in m3/mole)
ZC      = 0.235  (Critical compressibility)
Acc     = 0.344  (Accentric factor)
StdLiqDen(kg/m3)= 998 (Standard liquid density at 15 C)
LiqDen(kg/m3)= 998  (Liquid density in kg/m3 at temperature below)
LiqDen T(K)  = 293  (Temperature in Kelvin for liquid density above)
DipoleMoment = 1.8  (Dipole moment, not used currently)
CpA (kJ/ = 32.24255 (Ideal gas heat capacity in kJ/kmole/K and temperature in Kelvin)
CpB  kmol= 1.923835E-03 (Equation CP=A+(B*T)+(C*T^2)+(D*T^3)+(E*T^4))
CpC  K)  = 1.05549E-05
CpD      = -3.59646E-09
CpE      = 0
ViscType = 3         (Liquid viscosity equation type, 3 or 4)
ViscA(cP)= -24.71    (Equation 3: LN(V)=A+B/T+C*T+D*T^2 with visc in cP and temp in
K)
ViscB    = 4209      (Equation 4: LN(V)=A+B/T+C*LN(T)+D*T)
ViscC    = 0.04527
ViscD    = -3.376E-05
HVap(J/mol) = 40683  (Heat of vaporization at normal boiling point)
HFor(kJ/mol)= -242   (Standard heat of formation)

Page 44 of 98

AntA(kPaa)= 67.02455  (Antoine vapour pressure, Pres in kPaa and temp in K)
AntB      = -7276.391 (Equation: LN(P) = A + B/(T+C) + D*ln(T) + E*T^2)
AntC      = 0
AntD      = -7.342973
AntE      = 4.16191E-06
AntTMin(K)= 274.15    (Minimum temperature for Antoine equation)
AntTMax(K)= 647       (Maximum temperature for Antoine equation)

Page 45 of 98

PIPES

GENERAL

The main pipe dialog is accessed by:

 Double clicking on the pipe label,
 Right click on pipe label and selecting edit/edit fluid from the popup menu,
 Left click on pipe label to select it, and then edit it from the Equipment | Edit menu.

Pipe number

The pipe number must be unique. This is different from older revisions, and may prevent you from saving
changes to old problems without changing the pipe number.

Import from other pipe

Select the pipe from which to import pipe and fluid properties. This action cannot be undone. Selected
properties can also be copied to using the Equipment | Copy pipe menu command.

FLOWS

Specified flow rate

The flow rate specification is only visible for lines to and from Feeds, Products, Junctions, Vessels and
T-pieces. This is to prevent the user from entering the flow rate more than once in a series circuit.

Page 46 of 98

The mass flow rate can be specified as a value (or values for cases) or an E to use an equation. Using an
equation is convenient for linking the flow rate to that of another pipe (say to split the flow 50:50), or to the
pressure at an equipment. For more information, see help under Others-Equations.

Volumetric flow rates shown for vapor and liquid are at average pipe conditions.

Units button

The total flow rate must be in mass units, as other units lead to inconsistencies for 2-phase flow with different
properties at pipe inlet and outlet. The Units button allows the user to easily convert liquid or gas volumetric
flows to mass flows, which can be used as a specification.

Initially the density and molecular weight are set to the average calculated values which are only updated
during hydraulics calculation. The user has to ensure that the appropriate density and molecular weight are
used for the conversion.

Only the mass flow is transferred. Copy (Ctrl-C) and paste (Ctrl-V) the liquid fraction to the fluid dialog.

PIPE

Pipe material

Select the pipe material and database to use. The available nominal diameters, schedules and default pipes
roughness depend on the pipe material.

Pipe size

Known nominal diameter. Select the nominal pipes size and schedule. A valid combination will display an ID,
indicating that it is present in the pipe database.

Known ID. If a pipe material or size is not in the pipe database, the actual flowing and hydraulic ID of the pipe
can be input. To enable the ID input boxes, select ID as the Schedule.

If only the flowing ID is input, Korf will assume the pipe is cylindrical and the hydraulic ID equals the flowing ID.
For non-cylindrical flow areas (annulus, rectangular ducting, etc), enter the appropriate flowing and hydraulic
IDs.

Flowing ID is defined IDF := (4*FlowArea/pi)^0.5
Hydraulic ID is defined as IDH := 4*RH := 4*FlowArea / WettedPerimeter

For cylindrical pipes, IDF = IDH = ID.
For annuli, IDF = (IDo^2 - ODi^2)^0.5 and IDH = IDo - ODi

Unknown pipe size. If the pipe size is unknown, Korf will size it based on the criteria’s in the Pipe Sizing Dialog
(click on Sizing button).

Page 47 of 98

The pipe can be sized to a default Schedule Number or to an ID.

 To size to a default schedule number, select any Schedule number (say 40), and select a pipe size of
nothing (top entry). The schedule number selected is ignored, as Korf will default to schedule numbers
based on the material and size of the pipe. The maximum pipe size depends on the pipe database.

 To size to a specific ID, select ID as the Schedule number and delete the existing ID input. The

maximum allowable ID is 10m.

Pipe roughness

If the pipe roughness is not provided (leave empty), Korf will use the default pipe roughness in the pipe material
database. To use another pipe roughness, enter a value for pipe roughness.

Length and Fittings

Input the linear length. Korf uses this number without change, and does not check that the change in elevation
is more than the linear length.

Click on the Fittings button to display the Fittings Dialog. For all pipe fitting options, the user can enter a linear
length multiple (default is 1). This is intended as a method to estimate the total equivalent pipe length until
fittings are available.

Korf supports the L/D method, Crane resistance coefficient method and Hooper 2-K method (Chem Eng, 1981).
Select the appropriate method under Tools | Options | Hydraulics.

For entrance and exit losses, the user does not have to add one velocity head to account for the pressure to
velocity conversion, as Korf will include it automatically for all pipe leaving tanks and vessels.

A fitting can be selected and imported from the Fittings Database by clicking on one of the buttons with 3 dots.

The fittings database can be viewed in the application associated with comma separated files (CSV file, usually
Excel) by clicking on the Database button.

Page 48 of 98

MISCELLANEOUS

dP Design Factor

Korf multiplies all pressure drops and dP/length values with this factor. The default is 1.0, but the user can enter
a larger number (say 1.1-1.25) to account for uncertainties, pipe aging, etc.

Elevation dP

Be default the elevation pressure drop accounts for the atmospheric density based on the atmospheric
pressure (under Tools | Options) and ambient temperature (on the pipe Fluid dialog). Thus, Korf will calculate
the correct flow or pressures for stacks and flares. To ignore the atmospheric pressure and match older
version, edit the data file and change the DAMB entry for that pipe to zero ("DAMB",0,"kg/m3").

Omega 2-Phase Method

Click the Results button and Omega tab to display the input and results for the pipe Omega method. Please
note that the pipe Omega method requires that the outlet be 2-phase, and will fail to converge for sub cooled
choked flow.

2-Phase Flow Map

Select this option to display the horizontal, vertically up and vertically down 2-phase flow regime for the
selected pipe.

Surface tension is only used for the Dukler flow regime maps, and is inputted here (and not the Fluid Dialog).

Page 49 of 98

Most maps are self explanatory, except for the Horizontal Dukler map. This map actually consist of two maps in
one. Letters next to the operating point indicate which curve it apply to. For example, AD-S means it is either
Annular Dispersed or Stratified. Similarly, DB-I means it is either Dispersed Bubble or Intermittent.

Sum of elevations

The sum of uphill sections only apply to 2-phase flow. In 2 phase flow it is engineering practice to allow a
pressure drop for the up hill sections, but no pressure recovery for the down hill sections. The overall change
can be determined from the terminal elevations, but the sum of the internal up hill sections should be entered
here.

For example, assume a 2-phase pipe starts at grade, go up to the pipe rack (say 20 ft), then come down to
grade and finally go up to a vessel nozzle at say 30 ft. From the feed and vessel elevations Korf knows that the
elevation increase by 30 ft. Korf does not know that there is an internal elevation change of 20 ft must be
accounted for in 2-phase calculations. Thus, enter 20 ft for Sum of Elevations.

Equations

The flow rate in a pipe can be based on the flow of another pipe or the pressure at other equipment. Refer to
the section on Equations under Equipment for more details.

NOTES

Files

Korf can list and store up to 10 files associated with a pipe. Examples would be PIDs, Isometric drawings,
reference calculations, etc. The files will be opened with the application that is associated with that file

Page 50 of 98

extension.

Notes

Text area for user to add and store notes and comments.

ENGINEERING CALCULATIONS

Single phase (liquid)

Liquid phase pressure drops are calculated from the Darcy equations as presented in CRANE 410.

Single phase (gas)

Three models are available for gas phase pressure drop calculations.

Incompressible model. With this model, the pressure drop is calculated from the Darcy equations as presented
in CRANE 410. The average of the inlet and outlet density is used (based on calculated pressures). If the log
acceleration pressure drop is used, it will give identical results to the isothermal compressible method.

Isothermal compressible model. With this model, the pressure drop is calculated from the isothermal
compressible equations as presented in CRANE 410. Strictly speaking, this method must be combined with the
Isothermal sonic flow method (under Tools | Options) and Isothermal flash option (enter "T" for pipe duty).

HEMOmega model. With this model, the pressure drop is calculated from the modified Omega method and
should be combined with the HEMOmega sonic velocity method. It can be used for isothermal or adiabatic
compressible flow.

  For isothermal flow, use the same inlet and outlet pipe temperature or enter "T" for the duty if flash

calculations are done.

  For adiabatic flow, the only practical option is to combine it with flash calculations and enter a pipe duty

of zero.

Two-phase calculations (0.9999 > liquid fraction > .0001)

Pipe pressure drop is based on the average of the inlet and outlet properties and conditions. For pipes with
significant changes in liquid fraction or properties, this may lead to erroneous results, and the pipe should be
split into multiple pipes.

KORF supports 7 different methods for 2-phase pressure drop calculations.

 Homogeneous model (Dukler Case 1)

This method uses the Dukler Case 1 homogeneous (no slip) model (AIChE, 1964). Also refer to the
notes below.

 Dukler's constant slip model (Dukler Case 2)

This method uses the Dukler Case 2 constant slip model (AIChE, 1964). The liquid holdup can be
calculated from the Hughmark method (Chem Eng Prog, 1962 and Chem Eng, 1970) or graphs
presented in the GPSA manuals (10 th edition) and attributed to Dukler.

The user can use smooth pipe or rough pipe friction factors. In previous versions, the "GPSA" holdup
method was called the "Dukler" holdup method.

 Lockhart-Martinelli model

This method uses the empirical Lockhart-Martinelli model (Chem Eng Prog, 1949).

 Chisholm modification of the Lockhart-Martinelli equation

This method uses the semi-empirical modifications proposed by Chisholm (Int J Heat Mass Transfer,

Page 51 of 98

1967) to the Lockhart-Martinelli method.

 Chenoweth-Martin method

This method uses the empirical model presented by Chenoweth-Martin (Petroleum Refiner, 1955). The
graphs were extrapolated to cover a wider range.

 Beggs-Brill model

This method uses the Beggs and Brill model (J of Pet Tech, 1973/1991) for horizontal pipes. The user
can use smooth pipe or rough pipe friction factors.

  HEMOmega model

This method uses the modified Leung's Omega method (J of Fluid Eng, Sep 1994) for homogenous
equilibrium flow. It is a flexible and theoretically consistent method. Do not enter the vapour pressure
for pipes, as choked subcooled flow will fail to converge.

For all 2-phase methods the acceleration pressure drop is estimated based on the homogenous inlet and outlet
density.

Sonic velocity

Starting with Korf 3.0, velocities are limited to sonic velocity at Feeds/Products and Expanders. No attempt is
made to prevent velocities above sonic velocity at Vessels and Tees.

The HEMOmega sonic velocity method can be used for 2-phase or gas flow.

The Isothermal and Adiabatic sonic velocity methods are based on the vapour properties and should only be
used for gas flow.

Select the sonic flow velocity method under Tools | Options.

If choked flow exists at an outlet or expander, then the flow rate becomes independent of the outlet pressure.
This can cause a simulation to fail as specifications are no longer independent. If this happens, provide a
downstream pressure and Run the simulation from defaults (Hydraulics | Hydraulics | Run).

Pressure drop per length (for sizing)

The pressure drop per length (psi/100ft or kPa/100m) used for sizing excludes the pressure drop due to
acceleration (gases and 2-phase methods) for all methods except the isothermal compressible and
HEMOmega methods. For the isothermal compressible and HEMOmega methods the total density changed is
assumed to occur across 100 m.

Friction factor

The friction factor is calculated from the Chen equation (Chem Eng, 1987) for turbulent flow (Re>3000), and
from 64/Re for laminar flow (Re<2000). Linear interpolation is used in the transitional region.

For fittings the fully turbulent friction factor is based on the Van Karman equation (Daugherty et al).

The original Dukler and Beggs-Brill methods use smooth pipe friction factors, presumably because their
experimental data were based on smooth (plastic) pipe. However, some companies use these smooth pipe
equations for other pipes as well. In Korf (under Tools | Options) the user can select whether the normal or
smooth pipe friction factors are used for the Dukler and Beggs-Brill methods.

Page 52 of 98

FLUID

The operating conditions and physical properties are required for all pipes, without exception.

To access the fluid physical properties dialog:

 Click the Fluid button on the Pipe dialog,
 Right Click on pipe label and select Edit Fluid.

The conditions and properties can be:

 entered directly
copied from another pipe

 based on that of another pipe

 determined by a flash calculation

imported from a text file or Aspen/Hysys simulation

Outlet same as inlet

For pipes with constant temperature and liquid fraction, the user can select “Outlet same as inlet” and only
enter the inlet properties and conditions.

COMPOSITION

The composition is only required for the HMB, not for hydraulics. Only the components selected for the project
(under Process | Components menu) are displayed.

CONDITIONS

Page 53 of 98

For Hydraulics, the temperature, estimated pressure and liquid fraction are required.

For HMB, the inlet flash type and associated entries are required if the pipe is leaving a Feed and Vessel. The
values for all other pipes will be calculated by the HMB or Hydraulics.

In all cases, the pressure is determined from the Hydraulics, and the value provided will only be used as an
initial estimate.

Flash calculation

To perform a flash calculation on this dialog, the following steps are required:
 Firstly, select the method and components from the main menu.
 Secondly, enter the mol fractions under the Composition tab.
 Thirdly, select the flash type and enter required data for it.
 Lastly, click the Flash button.

The following flashes are supported (where applicable):
 TP – Temperature and pressure required
 PF – Pressure and liquid fraction required
 PH – Pressure and enthalpy required
 PS – Pressure and entropy required
 TF – Temperature and liquid fraction required. Can only be used if hydraulics is not run, as pressure

will be change.

Typically a TP or PF flash will be performed at the pipe inlet and a PH flash at the pipe outlet. To perform a PH
flash from this dialog, the user has to copy or input the enthalpy. After a successful flash, the calculated
physical properties are copied into the dialog for the current pipe.

Page 54 of 98

PROPERTIES

Inlet and outlet conditions can be provided, but the frictional and elevation pressure drop are based on the
average properties for the pipe.

The average liquid density, liquid viscosity and vapor viscosity are calculated as a simple arithmetic average
between inlet and outlet:

Prop = (Prop in + Prop out) / 2

The average vapor density is calculated from the average mole weight and average compressibility. They are in
turn calculated as a simple arithmetic average.

The homogenous, no-slip density and viscosity is calculated as the volume average (Dukler, 1964):

Prop = LVF * Prop Liq+ (1 – LVF) * Prop Vap
LVF = Liquid Volume Fraction

A pipe with significant vaporization or condensation should be split into multiple pipes to improve accuracy.

HEAT LOSS

If only the hydraulics are run, Korf uses the inlet and outlet temperatures provided and heat loss is not, and
cannot be, accounted for.

During heat and material balance calculations heat loss from pipes can be included. The user can specify the
heat loss using any of the following methods:
  Enter a specific duty for the pipe.
  Enter "T" for the duty to simulate isothermal pipe flow.
Page 55 of 98

  Delete the duty entry and enter an overall U value for the pipe. Korf will calculate the duty from the U

value and ambient temperature.

  Delete both the duty and U value. Korf will estimate the overall U value based on the process

coefficient, pipe resistance, insulation and outside air convection and radiation. The process coefficient
is based on the simplified Sieder-Tate equation. Pipe resistance is based on k=43 W/m/K. Edit the data
file to change it. The air convection coefficient is based on the modified Langmuir equation.

The Ambient Temperature on this dialog is also used to correct the elevation density change based on the
atmospheric density.

If the NTU heat loss method is used, a successful flash calculation is also required for the process fluid at this
temperature.

The pipe surface temperature assumes the inside temperature next to the wall is the same as the fluid bulk
temperature. This under estimate the surface temperature for high velocity gas where enthalpy includes the
kinetic energy impact.

IMPORTING DATA

Conditions and properties for this pipe only can be imported from:

 Text file (formatted)
 Aspen simulation
 Hysys/Unisim simulation

Import by clicking on the Import button. After importing text files, Korf generates a log file that lists the import
operation in detail.

The source (Hysys, Unisim, etc) and file name are set under the Option dialog (version 3.6.6).

Page 56 of 98

Lock stream
Select this check box to prevent these stream properties from being overwritten by imported data. This setting
also affects importing of text files from the File | Import menu.

Importing a text file

(a)   Create the formatted text file. Refer to File | Import menu for formatting details.
(b)   Select Text as simulator in the Options dialog.
(c)   Type in the stream number exactly as it appears in the text file. If nothing is entered, Korf assumes the
stream number in the text file is the same as in Korf. This setting also affects importing of text files from
the File | Import menu.

(d)   Enter (directly or by Browsing to it) the file name in the Data File name input empty.

Importing from Hysys/Unisim

(a)  Open the simulation in Hysys/Unisim. Ensure that it has a converged solution.
(b)  In Korf, select Hysys or Unisim as simulator in the Options dialog.
(c)  Type in the stream number exactly as it appears in the simulation. If nothing is entered, Korf assumes

the stream number in Hysys/Unisim is the same as in Korf.

(d)  Leave the Data File name input empty. If a file name is given, Korf will try to open it if it is not already
loaded. This is often a time consuming process and the user has no visual feedback than anything is
happening.

(e)  Select whether the conditions should be copied to the pipe inlet conditions, outlet conditions and/or

average fluid properties.

Importing from Aspen

(a)  Open the simulation in Aspen.
(b)  Create a Prop-Set (say “Korf”) detailing the properties and units that Korf imports. It must be in internal
units (as shown below) and it must be the first (or only) Prop-Set that is in use. Refer to the screen
shots below and the Aspen documentation.

(c)  Run the simulation and ensure that it has a converged solution.
(d)  In Korf, select Aspen as simulator in the Options dialog.
(e)  Type in the stream number exactly as it appears in the simulation. If nothing is entered, Korf assumes

the stream number in Aspen is the same as in Korf.

(f)  Enter (directly or by Browsing to it) the file name in the Data File name input empty. If it is not already

loaded, Korf will attempt to open it.

(g)  Select whether the conditions should be copied to the pipe inlet conditions, outlet conditions and/or

average fluid properties.

Page 57 of 98

Units
C
kPa absolute (Korf will deduct atmospheric pressure)

All the following properties must appear in the prop-set and must be in the units as show:
Property
TEMP
PRES
MASSVFRA
HMX
SMX
RHOMX
MUMX
MWMX
ZMX
CPCVMX
SIGMAMX
KMX

kJ/kg
kJ/kg-K
kg/cum
cP

dyne/cm
Watt/m-K

Under the Qualifiers tab, select Total, Vapor and Liquid.

Page 58 of 98

Under Setup | Reporting Options | Streams click on Property Sets and select this prop-set as the first or only
prop-set for that run.

Page 59 of 98

FEEDS AND PRODUCTS

Type
Feeds and Products can be represented by a pipe or a tank.

For hydraulics flows can be positive or negative.

For HMB flows must be positive, and pipes leaving Feeds must have defined compositions and flash
conditions.

Pipe
If a Feed/Product is represented by a pipe (arrow), the feed/product pressure refers to the static pressure (as
measured by a pressure gauge) on the flowing pipe. Enter 0 for the liquid level and pipe/nozzle relative
elevation.

Tank and Vessel
If a Feed/Product is represented by a tank or vessel, the feed/product pressure refers to the static pressure (as
measured by a pressure gauge) at the top of the tank above all fluid levels.

The static pressure at the inlet of a line leaving always differs from the tank pressure to account for the
increased velocity (equal to k=1). Thus, the user NEVER has to add an exit loss of k=1 to the fittings of any
pipe, as Korf automatically accounts for it.

The user should however add an entrance loss (of typically 0.5) to the line connected to a Feed tank to account
for inlet losses.

The net results of this is that the flows and total pressure drops are based on actual fittings specified. But, the
difference between the tank/vessels pressure and the leaving line inlet pressure is however always based on
an inlet loss of k=0.

The tank elevation is usually taken from grade to the bottom of the tank. The liquid level and pipe/nozzle
relative elevation is then the distance above (+) or below (-) the tank bottom.

By default the density inside the tank is the same as the density of the line leaving/entering. To use a different
density, change the Fluid Density drop down box from Line to nothing, and then manually enter the density of
the fluid inside the tank.

Inlet Pressure
The inlet pressure can be specified as a value (or values for cases) or an equation (enter an E). Using an
equation is convenient for simulating gas or liquid wells, or to link the pressure to another part of the simulation.
For more information, see help under Equipment-Equations.

Pressure drop
The pressure drop across the Feed/Product can be specified, and is intended for spray nozzles. This pressure
drop does not include inlet losses or velocity-to-pressure conversions.

Cases
Multiple case entries can be provided for the pressures and fluid levels.

Page 60 of 98

Page 61 of 98

VESSELS

Type
Vessels can be represented by:

 Vertical vessels with 2 inlets/outlets,
 Horizontal vessels with 3 inlets/oultets or
 Columns with 4 inlets/outlets.
 Tank with 2 inlets/outlets.

Apart from the drawing differences, all three are treated identically.

For hydraulics flows can be positive or negative. For HMB flows must be positive. Refer to the Process section
for other limitations.

Pressures
The vessel pressure refers to the static pressure (as measured by a pressure gauge) at the top of the vessel
above all fluid levels.

For each nozzle the user can enter the increase (+) or decrease (-) in pressure from the top of the vessel to the
nozzle to account for frictional pressure drop though internals such as trays. The relative elevation can also be
entered for each nozzle.

The static pressure at the inlet of a line leaving always differs from the vessel pressure to account for the
increased velocity (k=1). Thus, the user NEVER have to add an exit loss of k=1 to the fittings of any pipe, as
Korf automatically accounts for it.

The user should however add an entrance loss (of typically 0.5) to the line connected to the vessel to account
for actual inlet loss.

The net results of this is that the flows and total pressure drops are based on actual fittings specified. But, the
difference between the tank/vessels pressure and the leaving line inlet pressure is however always based on
an inlet loss of k=0.

Elevations and Levels
The vessel elevation is usually referred to the bottom tangent line. All 3 fluid levels as well as the nozzle relative
elevations are the distance above (+) or below (-) the bottom tangent (or other reference).

Enter 0 for the density to ignore a fluid level. In contrast, 0 for level indicates that the level is at the bottom
tangent (or other reference). Thus, the light fluid level must be more than the medium and heavy fluid level.

By default, the density for the fluid level is taken from that of a connecting piping. The user can select which
nozzle to use. In addition, the user can select nothing on the drop down box and then enter a density manually.

Cases
Multiple case entries can be provided for the pressure and fluid levels.

Phase split
By default Korf will not split the vessel phases into separate streams. Similar to mixers/splitters, the outlet flows
depend on the pressure drop calculations and the user has to provide the phase fraction and composition for
each line.

When only the hydraulics is run, Korf can split the fluid in the pipe connected to inlet nozzle 1 into vapour at
outlet nozzle 1 and liquid at outlet nozzle 2 (since version 3.6.5) by specifying Outlet Flows from: Nozzle 1. No
other connections are allowed, and flows must be positive.

When the HMB is run, the phase flows and compositions from a vessel depends on the flash calculations. The
user must select the Outlet Flows from: HMB specification on the vessel dialog when the HMB is run to ensure

Page 62 of 98

all specifications are correctly accounted for. All flows must be positive.

Both liquid phases (if present) will be combined into one liquid line if a three phase flash is performed with only
one liquid outlet line present.

The nozzle numbers for different arrangements are shown below:

Page 63 of 98

JUNCTIONS AND T-PIECES

JUNCTIONS

The Junction node is regarded as an ideal mixing or splitting of streams. Energy and momentum are NOT
conserved across a junction. This implies that the fluid entering the junction loses their kinetic energy without
gaining static pressure, and streams leaving the junction gain kinetic energy without losing static pressure. If
the Junction represents a vessel or tank, the user should add an entrance and exit loss (in the pipe dialog) for
the streams leaving the vessel. No need to add anything to the entering streams.

T-PIECES

The resistances (k values) of T-pieces are based on those presented by Idelchik and Smith and the correction
for manifolds are based on the work of Parr. The user can override the calculated k values if experimental or
proprietary methods are available. All k values are based on the flow and density of the fluid in the combined
branch.

The pressures and non-recoverable pressure drops (from combined line) are reported on the Pressures page.
Non-recoverable pressure drops are not used in the simulation, but is useful for estimating relief valve pipeline
losses.

Most T-piece correlations are subject to the following limitations:

 Single phase flow.
 Fluids with the same composition and temperature in all branches.
 Diameter of the straight section must stay constant. The branch can have a smaller diameter.

If a simulation oscillates, it is often due to the interaction between T-pieces and pipes. Enter 0 for the T-piece
k-values to see if a (simplified) solution is found.

Page 64 of 98

CONTROL VALVES

Type
Three valve types are supported. These types are used for drawing purposes only.

 Control valve
 Block valve
 Angle valve (relief valve)

The following valve characteristics are supported. The characteristic is used to convert the “% opening of
stroke”, to “% opening of Cv”.

 Linear
 Equal percentage
 Quick opening

Specifications
The user can specify any combination of the following:
Inlet pressure (back pressure controller)

 Outlet pressure (forward pressure controller)
 Pressure drop (flow control valve)
 Valve Cv (fixed size)

The Cv calculated or specified is the full open Cv. To specify the actual Cv, the user has to enter the full open
Cv as well as the % opening. If either is omitted, Korf will treat the actual Cv as a variable and calculate either
the full open Cv or % opening, depending on which is provided.

If the valve represents a normal globe or gate valve, a K-value may be specified instead of a Cv value. When
the problem is run, Korf immediately convert the K value to a Cv using Crane, and the rest of the calculations
are performed as if a Cv was specified. (Note - This is different from revisions prior to version 2.0).

Properties
The correct physical properties for both the inlet and outlet line are required (Note - This is different from
revisions prior to version 3.3). The following properties are used for valve Cv calculations:
Pipe ID, Density
Temperature
Pressure
Liquid fraction, Cp/Cv, Z, MW = Average of inlet and outlet    (prior to Version 3.3 flowing outlet was used).

= Flowing inlet and outlet
= Flowing inlet (prior to Version 2.0 flowing outlet was used).
= Flowing inlet

Choked flow

At choke flow, the outlet pressure is independent of the inlet pressure, and the user has to provide pressures
somewhere on the inlet and outlet side to ensure a unique solution. Converging systems that may oscillate
between critical and sub-critical flow is difficult, and often require that the user Run (Hydraulics | Hydraulics |
Run) the simulation, instead of Resuming it.

Calculations
Control valve calculations are based largely on the Masoneilan formulas, which are now similar to the ISA
formulas.

Korf does not support Reynolds number corrections.

Three options are supported for calculating 2-phase flow (refer to Tools | Options).

The Homogeneous and SumOfCv methods are appropriate for single phase and non-flashing 2-phase flow
only. Korf assumes that vapor only and vapor/liquid mixtures will choke at critical pressure drops according to
the Masoneilan/ISA gas equations. In addition, linear interpolation is used to limit the outlet vapour fraction to
roughly 70% of the inlet pressure.

Page 65 of 98

The HEMOmega method applies to all types of flow, including subcooled flashing choked flow. It is based on
the modified Omega method combined with the modified Diener-Schmidt non-equilibrium model and the
theoretical Buckingham equation. The main modifications are:

  Omega is calculated from the inlet and outlet properties, instead of the properties from an isentropic

flash at 70-90% of the inlet pressure. The user can however estimate omega separately and override
the calculated value.

  A custom curve fit based on the inlet vapour fraction and orifice length is used instead of the

Diener-Schmidt equation. A length of 100mm is assumed for control valves, but can be changed by
editing the data file.

The HEMOmega method assumes that xT = 0.84*FL^2. It also assumes the vapour pressure is equal to or
larger than the inlet pressure. The user can however override the default Omega and Vapour Pressure values.

The FL method for choked liquid flow requires the fluid critical pressure. The user must always enter this value
(in gauge pressure), even if the HMB is run.

The effect of reducers/expanders on the control valves is based on the non choked flow formula presented in
Masoneilan. This formula (Fp factor) uses the valve fluid density for the reducers/expanders as well. If this is
not acceptable, the user has to add a separate expander/reducer and select a line size valve. The Fp factor is
ignored if the valve is larger than the connecting pipe size.

The pressure recovery factor (FL) and gas choked flow pressure drop ratio (xT) are available from vendor
catalogues for the specific valve type, opening and flow direction (flow to open or flow to close). At full opening,
approximate values are:

Globe
Camflex
Ball
Butterfly
Typically, but not always, xT will increase with reduced valve opening. Korf does not correct xT for inlet/outlet
reducers.

xT
0.50-0.80
0.40-0.65
0.30
0.35

FL
0.80-0.95
0.70-0.90
0.60
0.65

dP Perm represents the non-recoverable inlet pressure drop for relief valves, from the inlet of the selected pipe
to the valve inlet. Two points worth noting:

  Using the pipe inlet as reference instead of the vessel itself make no difference as Korf only accounts

for recoverable pressure changes at vessel outlets.

  This calculations is based on the Bernoulli equation and assumes positive flow and constant fluid
density in all relevant pipes. If this is not the case, it will be more accurate to add up the individual
non-recoverable pressure drops.

Cases
Multiple case entries can be provided for the pressures and % valve opening.

Page 66 of 98

Page 67 of 98

ORIFICES

Type
The following flow meter types are supported:

 Thin plate square edge orifice
 Thick plate square edge orifice
 Perforated plates
 Quadrant edge orifice
 Nozzles
 Venturis

Specifications
The user can specify any combination of the following:

Inlet and/or outlet pressure

 Overall pressure drop (pipe taps)
 Close up pressure drop (close up taps)
 Bore diameter and number of holes
 Beta ratio

If C is entered as Beta ratio, the current calculated beta ratio is used as specification. Typically this is used in
cases, where the normal case is based on a pressure drop, and all subsequent cases use the same beta ratio.

Inlet and outlet pressures are based on pipe to pipe taps. The pressure drop for either the pipe or close-up
(flange) taps can be specified.

The beta ratio is based on the flowing inlet line size and is calculated from:
Beta = (No holes)^0.5 * Bore Dia / Pipe ID

The beta ratio for the discharge coefficient is based on the inlet pipe size, whereas the beta for pressure
recovery is based on the outlet pipe size. The outlet pipe size should be the same or larger than the inlet pipe
size.

Properties
The correct physical properties for both the inlet and outlet line are required (Note - This is different from
revisions prior to version 3.3). The following properties are used for orifice calculations:
Pipe ID, Density
Temperature
Pressure
Liquid fraction, Cp/Cv, Z, MW = Average of inlet and outlet    (prior to Version 3.3 flowing outlet was used).

= Flowing inlet and outlet
= Flowing inlet (prior to Version 2.0 flowing outlet was used).
= Flowing inlet

Calculations
The overall pressure drop is calculated in two steps. Firstly, the close-up pressure drop is calculated using the
discharge coefficient for close-up taps. Secondly, the overall pressure drop is calculated from the close-up
pressure drop

This approach is different from versions prior to Version 2.0, which only supported thin plate square edge
orifices and directly calculated the overall pressure drop. Both the discharge coefficient, C, and expansion
factor, Y, refer to close-up taps.

Discharge coefficients are based on:

 Square edge orifice – Equation in Spink. Correction for thickness per Kolodzie et al.
 Quadrant edge orifice – Equation in Miller.
 Nozzle – Equation in Miller for ASME long radius nozzle.
 Venturi – Equation/constant in Miller (C=0.985).

The gas expansion factor for orifice plates with a thickness to diameter ratio, t/d, between 0 and 0.5 is adjusted

Page 68 of 98

based on the data from Deckker and Chang (since version 3.6.3). Between a t/d of 0.5 and 1 the gas expansion
factor is prorated based on the orifice value at t/d=0.5 and the nozzle value at t/d=1.

The permanent (or overall) pressure drop is calculated from the close up pressure drop based on the equations
in Miller.

Three options are supported for calculating 2-phase flow (refer to Tools | Options).

The Homogeneous and SumOfArea methods are appropriate for single phase and non-flashing 2-phase flow
only. Korf assumes that vapor only and vapor/liquid mixtures can choke through all flow meters, except thin
plate orifices. In addition, linear interpolation is used to limit the outlet vapour fraction to roughly 70% of the inlet
pressure.

The HEMOmega method combines the modified Omega method with the modified Diener-Schmidt
non-equilibrium model and the theoretical Buckingham equation. It is applicable to short and long restrictions
with support for two phase flashing and non-flashing flow as well as bubble point and sub cooled flashing liquid
flow. The main modifications are:

  Omega is calculated from the inlet and outlet properties, instead of the properties from an isentropic

flash at 70-90% of the inlet pressure. The user can however estimate omega separately and override
the calculated value.

  A custom curve fit based on the inlet vapour fraction and orifice/nozzle length is used instead of the
Diener-Schmidt equation. A length of 0 meter results in the frozen model and a length above 1-2
meters results in the homogeneous equilibrium model. At 50-100 mm it matches the Diener-Schmidt
equation.

  At low liquid fractions the HEMOmega method does not match the Cunningham equation for orifice gas

flow.

  The HEMOmega method is adjusted to prevent a discontinuity at t/d=0.5, based on Deckker and

Chang (since version 3.6.3). Instead there is a smaller discontinuity at t/d=0.82.

The HEMOmega method assumes the vapour pressure is equal to or larger than the inlet pressure. The user
can however override the default Omega and Vapour Pressure values. Korf does NOT estimate the vapour
pressure during flash calculations.

To match API 520 using the HEMOmega method, enter the correct fluid properties in the connecting pipes and
select the following:

  Type = Nozzle
  Length = 1000 mm or greater
  C = Enter per API 520
  Omega = Estimate per API and enter
  Psat = Estimate using Hysys, etc and enter

Thin plate orifices at high gas phase pressure drops are based on a modification of the Cunningham method
(Trans ASME, 1951).

At choke flow, the outlet pressure is independent of the inlet pressure, and the user has to provide pressures
somewhere on the inlet and outlet side to ensue a unique solution. Converging systems that may oscillate
between critical and sub-critical flow is difficult, and often require that the user Run (Hydraulics | Hydraulics |
Run) the simulation, instead of Resuming it.

Cases
Multiple case entries can be provided for the pressures and beta ratio.

Information
Orifices are usually sized based on a “meter maximum” flow and corresponding standard dP range (typically
2,500 mmH2O or multiples of it). The method is summarized below:

Flow meter max  = Flow actual / (0.7 to 0.8)
dP actual
dP actual pipe

=    (0.7 to 0.8) ^ 2 * dPmeter max
= (1-Beta ^ 2) * dPactual flange

Page 69 of 98

= (1-Beta ^ 2) * (0.7 to 0.8) ^ 2 * dPmeter max flange
= 0.75 ^ 2 * (1-Beta ^ 2) * 2500              mmH20 typically
= 1000 mmH2O or 1.5 psi or 10 kPa    typically (dP spec in Korf)

Page 70 of 98

PUMPS

Type
The pump calculations are intended for centrifugal pumps only. Acceleration heads and pulsation due to
reciprocating pumps are not included.

Properties
The physical properties from the flowing inlet line are used.

Specifications
The user can specify any combination of the following:

Inlet pressure

 Outlet pressure
 Pressure increase (dP), value or from pump curve

Similar to other equipment, the pump head (dP) is based on the drawing outlet minus inlet pressure. Not the
actual flowing outlet minus inlet.

The power is calculated based on efficiencies provided. If no efficiency is provided, Korf will estimate it from the
pump type. Currently the pump type is only used to estimate the efficiencies.

The pressure head, efficiency and NPSH Required can be based on a user supplied head-flow curve. To use
the curves:

 Enter “C” as the dP to use the head curve,
 Enter “C” as Efficiency to use the efficiency curve,
 Enter “C” as NPSHR to use the NPSH Required curve.

Linear interpolation is used for all curves, and at least two points are required. The curve must cover the entire
range of flows required, and Korf does not extrapolate below/above the min/max flows. Use CTRL-C, CTRL-V
and CTRL-X to copy, paste and cut a range of cells between different pumps.

Note: Korf does not extrapolate the head/flow curve below/above the min/max flows.

All curves can be adjusted for different impeller diameters and speeds based on the fan laws. Results are
reported in detail in the report file.

The speed for variable speed drives can be estimated by selecting the VSD option on the Curves tab. At least
two pump curve points and the Curve RPM are required.

With appropriate pump curves the “blocked in” power can also be obtained. Enter a small number (1 kg/h) as
the flow rate, as a zero flow rate will result in almost zero power.

Korf also provides the ability to generate typical curves based on the current flow, head, efficiency and NPSHR.
This can be done manually (click Generate Curve Now) or every time Case 1 is run (select Generate Curve
Each Time for Case 1).

This is typically used to estimate different flow cases when the exact pump curve is not yet know, and is used
as follows:

 Case 1. Run the normal flow case (100%) without a pump dP specification and with a dP specification

across a downstream control valve.

 Generate a typical curve (manually or automatically for Case 1).
 Other cases. Specify the pump dP from the curve (“C” for dP, efficiency and/or NPSHR), and delete the

control valve dP specification.
In all cases the flow rates are specified (for example normal, rated, turndown flow).


 For example, the pump dP specification is “;C” and the control valve dP specification is “25;” and the

flow rate specification is “10000;11000;4000”.

Page 71 of 98

Advanced Tips:
The shape of the typical pump curves can be changed by editing the following entries in the project data file:

"\GEN",0,"PCURQ",0,20,40,60,80,90,100,110,120,130,"%"
"\GEN",0,"PCURH",120,119,118,115,110,105,100,95,88,80,"%"
"\GEN",0,"PCUREFF",0,40,65,85,95,98,100,98,95,90,"%"
"\GEN",0,"PCURNPSH",45,45,50,60,75,85,100,120,150,180,"%"

The respective head, efficiency and NPSH Required percentages must match the corresponding flow
percentage. Data must be provided for all 10 points.

Pumps and compressors with curves and unknown flow rates present a naturally divergent system and is
difficult to converge. Korf resolves this by fitting a special function though each point. The slope of this curve is
decreased (made more negative) to improve convergence, at the expense of more iterations. The default
change is –1 for pumps and –100 for compressors. If a pump or compressor does not converge, the user can
modify the slope change by editing the following entry in the project data file:

"\GEN",0,"MPCURV",-1,-100

Cases
Multiple case entries can be provided for the pressures, efficiency and NPSHR. If pump curves are employed,
different values for pressure/NPSH/efficiency can be used based on the case flow rate.

NPSH
Korf can calculate the NPSH Available and estimate the NPSH Required for a pump. Results are reported in

Page 72 of 98

detail in the report file.

NPSHA. Click on the NPSH button to enter the suction source and enable NPSHA calculations.

The source for NPSH calculations can only refer to Feeds or outlet lines from Vessels, and is thus limited to
lines with positive flow rates. In addition, the nozzle number is stored, not the connecting pipe, so the user need
to be caution when moving pipes to another vessel nozzle.

Vapor pressure can be entered as a credit, which equals the vessels pressure minus the vapor pressure, or the
absolute vapor pressure value.

NPSHR. The NPSH Required can be estimated based on the Suction Specific Speed, or from a user supplied
NPSH curve. Enter “C” as NPSHR to use the NPSH Required curve.

Care must be taken when entering the Suction Specific Speed (SSS), as this number is not the same as the
(impeller) Specific Speed and is not dimensionless. It is defined as:

SSS = rpm * (US gpm)^0.5 / NPSHR^0.75

Where the flow (gpm) is per suction (1/2 for double suction) and at best efficiency point. NPSHR is in ft.

Note: The Feed or Tank index is stored as reference. Prior to version 3.2 the equipment number was stored as
reference.

Shut Off Pressure

Page 73 of 98

The pump maximum suction pressure and shut off (dead head) pressure can be calculated as a separate case,
or directly from the input on the pump dialog. Use the latter only if the fluid density at the pump suction is the
same as in the upstream vessel.

The upstream vessel elevation and pressure drop inside the vessel are obtained from the vessel that is
selected for the NPSH calculation.

The vessel elevation is from grade to a reference line (typically bottom tangent) and the pressure drop inside
the vessel is from the vessel top to above the fluid level.

The maximum pressure at the top of the upstream vessel is typically the relief valve set pressure or vessel
design pressure. The maximum fluid level is from the vessel reference line (typically bottom tangent) to the
maximum fluid level (typically top of float or top tangent).

Pump pressure gain at zero flow can be based on the current calculated dP or the pump curve.

It is typically only based on the calculated pump dP for the rated case. Results for the other cases can be
ignored.

dP shut off = (dP Margin) * (dPshut off/dPcalc) * dP calculated

If it is based on the pump curve, the lowest point on the pump curve must be at zero flow.

dP shut off = (dP margin) * dP from curve at zero flow

dP Margin is to account for impeller variations and turbine speed variations.

Page 74 of 98

Page 75 of 98

COMPRESSORS

Compressors are similar to pumps (previous topic), with the following additional comments.

Properties
The physical properties from the flowing inlet line are used, but in general it is better to provide proper vapor
phase physical properties for both the inlet and outlet line.

These equations are more accurate if the ideal Cp/Cv value is used, instead of the actual Cp/Cv (this is true in
general and is not peculiar to Korf).

Specifications
The head and power are calculated based on adiabatic efficiencies. If no efficiency is provided, Korf will
estimate it from the compressor type. Currently the compressor type is only used to estimate the efficiencies.

The user can also specify the actual volumetric inlet flow rate (useful for reciprocating compressors) and the
pressure ratio. The pressure ratio is based on drawing outlet/inlet.

Compressor head and power are always based on the adiabatic compressible equations. When the HMB is
run, a Head Adjustment factor is calculated to ensure the adiabatic equations matches the isentropic flash
calculations (since version 3.6.3). The user can override this factor on the Curve tab.

The compressor equipment can also be used for expanders/turbines.

Advanced Tip:

Page 76 of 98

The shape of the typical compressor curve can be changed by editing the following entries in the project data
file:

"\GEN",0,"CCURQ",0,30,50,70,80,90,100,110,120,130,"%"
"\GEN",0,"CCURH",110,110,110,109,107,105,100,90,80,65,"%"
"\GEN",0,"CCUREFF",0,30,50,70,80,90,100,90,80,65,"%"

The respective head and efficiency percentages must match the corresponding flow percentage. Data must be
provided for all 10 points.

Page 77 of 98

EXCHANGERS

Type
Exchangers can be represented by a shell and tube exchanger, fired heater or air cooler. For shell and tube
exchangers the flow can be through the shell or tube side. The type and side are only used for drawing
purposes.

Specifications
Similar to other equipment, the exchanger pressure drop is based on the drawing inlet minus outlet pressure.
Not the actual flowing inlet minus outlet.

When a rating dP is specified, the pressure drop is assumed to be proportional to the mass flow^1.8 and
inversely proportional to the density. Density is the average of the inlet and outlet. Viscosity effects are currently
ignored. To enable the Rating dP slot, first delete the normal dP entry.

Inlet and outlet pressures include elevation effects, whereas specified and calculated dP's are due to friction
only.

Static head inside the exchanger is calculated from the average of the inlet and outlet total density.

Page 78 of 98

EXPANDERS AND REDUCERS

Reducers and Expanders

For subsonic flow the pressure change for expanders are based on the momentum equation. This equation is
valid for liquids, gases and 2-phase flows at angles above 45 deg. The input angle is not used for expanders,
and the K value is reported but not directly used by Korf.

Since version 3.0 Korf checks for isothermal choked flow at expanders, and increases the inlet pressure to
prevent supersonic velocities.

The pressure change for reducers are based on the nozzle equations followed by a K value based on the
flowing outlet pipe size and density. Choke flow should never occur through a reducer.

After running the simulation, the drawing will change to represent an expander, reducer or junction to match the
pipe size change.

The non-recoverable pressure drop is the irreversible loss through the reducer or expander (excluding the
effect of velocity change), and is useful for relief valve piping calculation. For expanders with gases or 2-phase
flow the non-recoverable loss is only approximate.

Page 79 of 98

MISCELLANEOUS EQUIPMENT

Miscellaneous Equipment
Similar to other equipment, the equipment pressure drop is based on the drawing inlet minus outlet pressure.
Not the actual flowing inlet minus outlet.

When a rating dP is specified, the pressure drop is assumed to be proportional to the mass flow^2 and
inversely proportional to the density. Density is the average of the inlet and outlet. Viscosity effects are ignored.
To enable the Rating dP slot, first delete the normal dP entry.

Inlet and outlet pressures include elevation effects, whereas specified and calculated dP's are due to friction
only.

Static head inside the equipment is calculated from the average of the inlet and outlet total density.

K and L/D values may be specified instead of a dP. The K and L/D values are based on the flowing inlet pipe
size and density (prior to Rev 2.0 drawing inlet size was used).

Typically a mass balance is performed across a Miscellaneous equipment. However, the user can select a
volume balance to simulate brine flow to, and hydrocarbon flow from, wells.

Typically the outlet and inlet mass flow is the same. The user can however change the Outlet flow/Inlet flow
ratio. This is very useful for relief headers, where the relief valve piping is based on the full open flow, while the
main headers are based on the required flow rate.

There is no pressure to velocity conversion for a change in pipe size across miscellaneous equipment and
check valves.

Page 80 of 98

EQUATIONS

General

Equations are a powerful feature that can be used in Feeds, Products and Pipes.

To use an equation:
- Enter an E as the specification. Entries that can accept an E are post fixed with a ^ (for example for pipes the
label is Flow rate*^).
- Select the equation type.
- Enter the equation equipment number and coefficients.

The equipment number in an equation must be unique (only used by one piece of equipment). Find all
equipment with that number from the Edit | Find menu.

The equipment number (and not the index) is stored. Changing equipment numbers (labels) do not
automatically update the equations.

All constants entered must be in internal units. These are t/h and kPag or kPaa (depending on equation).

An equation can reference the pipe/equipment it is associated with (since version 3.2).

Equations essentially manipulate the underlying matrices directly, and should be used with care.

Equation Types

The following equations are supported,

Equation 1: W = C1 + C2*W, with W=t/h, pipes only
This equation is used to specify the flow rate in a pipe based on the flow rate in another pipe.

For example, to specify pipe L2 to be 50% of L1:
- Enter E as the flow rate spec for pipe L2.
- Enter equation number = 1 for pipe L2.
- Enter equipment for W = L1 for pipe L2.
- Enter C1=0 and C2=0.5 for pipe L2.

Equation 2: P = C1 + C2*P, with P=kPag, equipment only
This equation is used to specify the pressure at a Feed or Product based on the pressure at another equipment.

Page 81 of 98

For example, to specify feed F1 pressure equal to control valve CV1 inlet pressure:
- Enter E as the pressure spec for feed F1.
- Enter equation number = 2 for feed F1.
- Enter equipment for P = CV1 and Inlet for feed F1.
- Enter C1=0 and C2=1 for feed F1.

Equation 3: P = C2*(1 - (W/C1)^C3), with W=t/h, P=kPaa
This equation is used to specify the pressure at an equipment based on the mass flow rate in a pipe. Typically
used for liquid wells, turbines or proprietary pressure drop equations.

Equation can be enter with a Pipe (and link to any equipment) or with a Feed/Product (and linked to any pipe).

The sign for C1 is maintained to enable the user to specify pressure drops and gains. Thus, the equation is
really P = C2*(1 - sign(C1)*(W/abs(C1))^C3)

For example, it is possible to simulate a custom nozzle as a product. Suppose the pressure drop (to atmospheric
of 100 kPaa) is 0 kPa at 0 t/h flow and 200 kPa at 100 t/h. The coefficients are calculated as follows:
- C3 = 2 assuming pressure drop proportional to flow squared.
- Rewrite equation to P - C2 = - C2/C1^2 * W^2.
- At W=0 equation yields P - C2 = 0, thus C2=100 kPaa (atmospheric).
- At W=100 equation yields 200 = - 100/C1^2 * 100^2, thus C1 = -70.7 t/h.
- C1 is negative as pressure drop, not pressure gain.

Equation 4: P = C2*(1 - (W/C1)^C3)^0.5, with W=t/h, P=kPaa
This equation is used to specify the pressure at an equipment based on the mass flow rate in a pipe. Typically
used for gas wells.

Page 82 of 98

Equation can be enter with a Pipe (and link to any equipment) or with a Feed/Product (and linked to any pipe).

The sign for C1 is maintained to enable the user to specify pressure drops and gains. Thus, the equation is
really P = C2*(1 - sign(C1)*(W/abs(C1))^C3)^0.5

Equation 5: dP = C1 + C2*W^2, with W=t/h, dP=kPa
This equation is used to specify the pressure drop at a Product outlet based on the mass flow rate in a pipe.
Typically used for spargers.

Equation can only be enter with a Product (and linked to any pipe).

Page 83 of 98

PIPE AND FITTING DATA

PIPES

  Pipe roughness.

Typical absolute pipe roughness values (from CRANE) are listed in the table below.

Material

Drawn Tubing
Commercial Steel
Asphalted Cast Iron
Galvanized Iron
Cast Iron
Wood Stave
Concrete
Riveted Steel

Absolute Roughness
(mm)
0.0015
0.0457 - 0.05
0.12
0.15
0.26
0.18 - 0.91
0.30 - 3.0
0.91 - 9.1

FITTINGS

Typical L/D and K values for pipe fittings can be found in CRANE and similar references. For completeness,
some of this data is given in the table below.

  Pipe Entrance

A flush entrance with an R/D=0 represent a sharp-edge entrance.

Type
Flush

Project in

R/D
0.00
0.02
0.04
0.06
0.10
+0.15
-

K
0.5
0.28
0.24
0.15
0.09
0.04
0.78

  Pipe Exit

Although the exit "loss" occurs at the exit of the pipe, the conversion of the static to the kinetic pressure
(equal to K=1) occurs at the inlet of the pipe. Thus, for feeds from tanks and vessels, the exit "loss"
should be added to the pipe leaving the Feed, and not the pipe entering the Product.

Type
All

K
1.0

  Valves

Type
Gate (full port)

Globe
Ball

Parameter
100 % open
75 % open
50 % open
25 % open
100 % open
Full port

Page 84 of 98

L/D
8
35 - 40
200 - 260
800 - 900
340
3

Butterfly

Angle
Check

Stop-Check
Plug
Plug-3 way

2"-8"
10"-14"
16"-24"
-
Swing-Screwed
Swing-Flanged
Lift-Globe
Lift-Angle
Tilt disk 5 deg
Tilt disk 15 deg

Straight
Straight
Branch

45
35
25
55-150
100
50
600
55
20 - 40
60 - 120
55 - 400
18
30
90

  Mitre Bends

Based on data from CRANE and data published by ASME.

Angle
0
15
30
45
60
75
90

L/D
2
4
8
15
25
40
58-60



90 deg Pipe Bends and Elbows

A short radius elbow is represented by an R/D of 1, whereas a long radius elbow is represented by an
R/D of 1.5.

R/D
1
1.5
2
3
4
6
8
10
12
14
16
20

L/D
20
14
12
12
14
17
24
30
34
38
42
50

Based on CRANE the resistance of bends greater than 90 degrees, (L/D)n, is calculated from the L/D
values for single 90 deg bends by,

where n is the number of 90 deg bends and L/D is from the table above.

(L/D)n    =    L/D + (n-1)(0.25*pi*R/D + 0.5*L/D)

  Standard Elbows (screwed)

Bend (deg)
90

L/D
30

Page 85 of 98

45
Close pattern
return

  Standard Tees (screwed)

All flow thru
straight run
branch

16

50

L/D
20
60

Page 86 of 98

FAQ

1) "The report file is all scrambled ?"

Usually two reasons for this:
(a) A line of text does not fit on a single line. To correct this, reduce the font size, reduce the page margins or
increase the paper size. This can be done in Korf (File | Page Setup) or in the word processor.
(b) The viewer (such as WordPad) has word wrap enabled. Disable word wrap in these viewers.

2) "How do I size a pipe ? "

In the pipe dialog, select the top most entry (blank) for pipe size.

3) "Line diameter goes to minimum or maximum ?"

This happens if the pipe diameter is unknown and you have specified (usually indirectly) a fixed pressure drop.
Changing the diameter then has no effect on the dP/100m.

4) "The simulation does not converge ?"

Firstly, if Korf fails on the first pass, it is usually due to poor initial estimates from the previous run. RUN the
simulation (from the menu bar), instead of RESUMING it.

Secondly, the best way to troubleshoot convergence issues is to set the number of iterations to 1 (default is 20)
and resume the hydraulic simulation. Then monitor the changes between runs to understand the problem
better.

Thirdly, often divergence is caused by certain specifications. Try the following if it does happen:

  Check your spec's. Make sure they make sense and are independent. Read the section on

"Specifications".

  Specify fixed flow rates when using pump/compressor curves, or specify the pump/compressor dP.

Pump and compressors with unknown flow rate and supplied pump curves    frequently fail to converge.

  Tees often cause convergence problems, usually due to pressure recovery or because the flow

direction through them changes between iteration.

  A calculated pressure is less than absolute zero. This is a frequent source of problems with

compressible flow. Change your specs and run problem again. Do not hit resume, as this will initialize
all properties from the diverged run.

  The outlet pressure from a control valve or orifice is undeterminable due to choke flow conditions.

Specify the outlet pressure or reduce the flow.

Lastly, if all else fails, contact the developers.

5) "Why is the pump curve ignored ?"

Korf only uses the head flow curve provided if “C” is entered as dP specification.

6) "Report does not change between runs ?"

Close current report (in Write/WordPad/MSWord) completely before performing the next simulation.

7) "I am having trouble connecting a pipe to an equipment ? "

Page 87 of 98

Flow can be positive or negative, but equipment has fixed inlet and outlets. Inlets are depicted with a small
vertical line. A pipe line can ONLY start at an equipment outlet, and end at an equipment inlet. When you are at
a valid inlet (to end a line) or outlet (to start a line), the mouse pointer will change to an up arrow. When the
mouse pointer changes to an up arrow, simply click (or release if dragging) the left mouse button.

8) "How do I disconnect a pipe line from an equipment ? "

Move the mouse to the end of the line you want to disconnect. The mouse pointer will change from a crosshair
to an arrow. Press the left mouse button and drag the line away from the equipment. Let go of the left button to
drop the line or connect it to other equipment. Note - if the equipment is dragged instead of the line end, then
the mouse was over the equipment instead of over the line end.

9) "The pipe looks connected, but when I run Korf, it says it isn't ? "

It is possible to have the pipe end and equipment inlet/outlet on top of one another without the line being
connected. To see if a line is connected, drag the equipment a short distance. If the line moves with the
equipment, it is connected to it.

10) "The specifications are not independent. Why does this happen and why can't Korf be more specific
? "

Overspecifying the circuit is often attributed to:

 Purely recycle circuits. Refer to the help file section on this issue.
 You have specified the flow rate more than once in a series circuit.
 Specifying the dP and Cv for a control valve fixes the flow rate, which will clash with a flow rate

specification. Similar for a orifice beta and dP.

 You have multiple inlet and outlet flows, and have specified the flow rates for all. Korf does a mass

balance across every piece of equipment, which results in an overall mass balance. Thus, you have to
leave at least one flow rate into or out of the circuit unspecified for Korf to vary to obtain an overall
mass balance.

Korf has no way of calculating why the specifications are independent. The user has to think through what data
is available and what must be calculated by Korf.

11) "Does Korf do flash calculations ? "

Yes, built-in support as well as using Hysys through an OLE link.

12) "I cannot change the flash method ? "

Korf support two flash methods, ie. Korf and Hysys. To change from the one to the other, you MUST first delete
all the currently selected components (Process | Components). This is necessary as they often use different
component names and Korf makes no attempt to convert between them. It is clear that you have to decide at
the start of the project which flash method you want to use, as changing later can entail significant work to
re-enter compositions.

13) "Can I access the fluid properties without opening the pipe dialog ? "

Yes. Right click on the pipe label and select Edit Fluid.

Page 88 of 98

14) "The Runlog contain many warnings and errors. Are the results correct ? "

It depends on where the warnings/errors appear in the Runlog.

If the warnings/errors appear during the beginning of the iterations and then disappear later, then the results
are correct. It implies the initial values used (from a previous run or initial defaults), are very wrong which
resulted in unrealistic initial/intermediate results.

If the warnings/errors appear at the end of the iterations/runlog, then the results are typically wrong. Especially
if the Runlog also states that the problem has not converged.

15) "The Expander/Reducer always looks like an Expander, even if the line reduces ? "

The representation of the Expander/Reducer is only used for the drawing. The actual function of the
Expander/Reducer is determined from the connecting line sizes. From version 3.0 the expander/reducer
changes based on the function it performs.

16) "Hydraulics won’t run – says No components are defined ? "

Korf can be run in 3 mode:

 Hydraulics only (black arrow on toolbar)
 Heat and mass balance only (from menu only)
 Hydraulics and Heat & Mass balance (two green arrows)

To run the Hydraulics only, you do not need to define components. Instead, physical fluid properties are
required for all pipes. If Korf report that no components are defined, the user accidentally tried to run the Heat
and Mass balance.

17) "Report file is empty ? "

Note that there are two toolbar buttons to view report files. One for the Hydraulic and one for the Process
Report file. If the report file is empty without reason, the user most likely selected to view the wrong one.

If the report file contains the words "End of file }", then the simulation was not run. Review the Runlog to identify
the cause of the problem.

18) "How can pressure increase through an expander ? "

Korf uses the momentum equation for sudden expansions as it applies to liquids, gases and 2-phase flow. For
liquids through sudden expanders the equations in Korf are exactly the same as in Crane. In fact, the Crane K
value is derived from the momentum equation.

The reason for the confusion is that Korf includes the pressure change due to velocity change, whereas the K
value only calculates the frictional, non-recoverable pressure drop.

For example, consider water at 100000 kg/h flowing from 4" to 8" using the Crane method.

Ks = (1-(0.1022604/0.2027174)^2)^2
    = 0.5558

P1-P2 = 6.254E-11 * W^2 / Den * (1/D2^4 - 1/D1^4) + 6.254E-11 * Ks * W^2 / Den / Ds^4
          = 6.254E-11*100000^2/1000*(1/0.2027174^4-1/0.1022604^4) +
                6.254E-11*0.5558*100000^2/1000/0.1022604^4
          = -5.349 + 3.179
          = -2.17 kPa which matches Korf exactly.

Page 89 of 98

19) "The Equivalent Length does not match the fittings L/D and varies with flow rate ? "

Equivalent length is not actually used in any calculations in Korf. It is simply calculated and reported and will
only match the entered L/D values for fittings if the Equivalent length method is used.

The equivalent length is back calculated from the sum of K values and sum of L/D values as follows:
Pipe_EL = Pipe_ID / Pipe_f * (Pipe_Ks + Pipe_fT * Pipe_L/Ds + Pipe_f * Pipe_L / Pipe_ID)

Essentially it says: What is the length of pipe required to match the pressure drop calculated. The confusion
occurs because fT does not depend on flow rate, but f does. This implies that the pipe equivalent length will
vary with flow rate (for Crane and 2K method).

Some companies calculate pressure drop using an equivalent length method, which has been supported in Korf
since version 3.4. In this method, the equivalent length is independent of flow rate.
.

  20) "Cannot select Mixer/Splitter while holding down Ctrl key ? "

Select the Mixer/Splitter before selecting any of the pipes connected to it. If pipes are already selected, use
Shift-Click to deselect the pipes. Then select the Mixer/Splitter and lastly reselect the connecting pipes.

Page 90 of 98

HISTORY

Revision 3.6
Scope - Significant changes.
Revision released – Mar 2023.
Beta testers – Ryan Waelz (Canada).

Graphical interface:
1) Allow selection by dragging the mouse.
2) Provide shortcuts for menu commands (Ctrl-S, etc).
3) Create an Excel report in addition to text reports.
4) Improved component search to include formula, CAS number and synonym.
5) Add additional NPSH and simulator data to report files.
6) Improve units of measure selection and display (3.5.3)

Engineering calculations:
1) Ability to enter a pipe length multiplier to represent fittings.
2) Ability to enter pump NPSH vapour pressure as absolute value or credit.
3) Add support for UniSim (3.5.1).
4) Allow import of all streams at once from Hysys and UniSim.
5) Allow use of a Hysys/UniSim case to support modified fluid packages, pseudo and assay components.
6) Improve Aspen import of a single streams.
7) Updated Hysys and UniSim pure components.
8) Add Air as a components for both Korf and Hysys/UniSim.

Others:
1) Reset number of specs and simulation file data on closing a file.
2) Store simulator view preference and units for standard volumetric vapour flow.
3) Fix incorrect reporting of <25mm ID pipes in report (3.5.3).
4) Ability to read template file for company specific defaults (3.5.3).
5) Remove non-functional EOS's from Hysys/UniSim list (3.5.3).
6) Correct dP shut off units on dialog (3.5.1).

Revision 3.5
Scope - Significant changes.
Revision released – Jan 2019.
Beta testers – Ryan Waelz (Canada) and Oscar Delgado (Canada).

Graphical interface:
1) Rewrite of the GUI to enable use of newer Windows styles.
        (a) Includes new icons, cursors, toolbar, statusbar, palette, tab control and tooltips.
        (b) Support more mouse controls (scrolling and zooming).
        (c) Revised subclassing.
2) Allow searching for chemical components.
3) Allow selection of an Arc similar to a Text box.
4) Report small compositions in HMB report.

Engineering calculations:
1) Add FL method for liquid choke flow through control valves.
2) Review and improve all ideal heat capacities.

Others:
1) Improve enthalpy for methane at low temperatures.
2) Fix problem with pipe duty that could only be stored once.
3) Fix liquid density error for light pseudo components.

Revision 3.4

Page 91 of 98

Scope - Moderate changes.
Revision released – Jan 2016.
Beta testers – Ryan Waelz (Canada).

Engineering calculations:
1) Add built in support for 3 phase flash calculations.
2) Add Equivalent length method for fittings.
3) Provide option to base Crane fitting fT on actual or steel roughness.
4) Add calculated valve travel for control valves.
5) Add pump shut off pressure.

Others:
1) Report frictional and acceleration pressure drops separately.
2) Fix missing U value units if file is double clicked.
3) Fix problem with zero flows using Hysys flash calculations.
4) Fix HMB issue with multiple vessels in series.
5) Prevent error using Omega method for zero length lines.
6) Allow Tee label to be hidden.

Revision 3.3
Scope - Moderate changes.
Revision released – Dec 2013.
Beta testers – Ryan Waelz (Canada).

Graphical interface:
1) Allow user to override density for levels in Feeds/Products/Vessels.
2) Do not make Tees red if manifold size changes. Keep error message.

Engineering calculations:
1) Include velocity in energy balance for flash calculations.
2) Include orifice and control valve pressures in dampening.
3) Include atmospheric density in elevation pressure gain/loss.
4) Add Omega method for orifices, nozzles, control valve and pipes.
5) Base Homogeneous and SumOfArea models on average fluid properties. Limit outlet vapour fraction.
6) Add Isothermal flash option for pipes.
7) Add option to change mass flow across Misc equipment.
8) Change critical property methods for pseudo components to support heavier compounds.
9) Add the NTU method for pipe heat loss calculation.

Others:
1) Fix error in flow regime routine if vapour exceeds liquid density.
2) Ensure compressibility factor is greater than 0.
3) Fix bug that prevented choked flow at expanders.
4) HWB only resets negative flows at Vessels and Products.
5) Correct font in some dialogs.

Revision 3.2
Scope - Moderate changes.
Revision released – Jan 2012.
Beta testers – Ryan Waelz (Canada) and Graham Moss (Canada).

Graphical interface:
1) Valve can be represented by a Control valve, Block Valve or Angle valve (relief valve).
2) Copy and paste using keyboard shortcuts (Ctl-C, Ctl-V).
3) Store equipment index (instead of number) for most reference equipment.
4) Click anywhere to deselect equipment.
5) Maintain reference equipment if multiple equipment is copied.
6) Show reference equipment and Re number on drawing.

Page 92 of 98

7) Improved help in Status bar.

Engineering calculations:
1) Add non-recoverable inlet loss for relief valves.
2) Allow pipe fluid properties to be based on that of another pipe (reference pipe).
3) Import surface tension from Hysys/Aspen.
4) Equations can reference the pipe/equipment it is associated with.
5) Simpler equation to represent spargers (for Products).
6) Allow dampening for flows and pumps/compressor pressures.
7) Heat loss calculation allows cooling (due to pressure drop) on heat input.

Others:
1) Fix bug to update displayed specs if edited through popup menu.
2) Fix bug to redraw drawing after saving file.
3) Fix minor convergence bug in TP flash routine.
4) Fix intermittent overflow errors in vapour pressure, compressor head and heat loss routines.

Revision 3.1
Scope - Significant changes.
Revision released – Jun 2010.
Beta testers – Alain Baillod (Switzerland).

Graphical interface:
1) Feed and Products can be represented by a Vessel.
2) Find option to search for and select all equip matching an equip number.
3) Default Product label changed from P to TK (to distinguish from Pumps)

Engineering calculations:
1) Add Equations to Feeds, Products and Pipes. Allow E as spec.
2) Add laminar to turbulent transition zone for friction factor to prevent oscillation.
3) Improve convergence for HMB with vessels. Allow V as vapor flow rate spec.
4) Add inlet vol flow and pressure ratio spec for compressors/turbines.
5) Revise Compressor to work for turbines/expanders.
6) Allow volume balance (instead of mass balance) for Misc equipment (for brine wells).
7) Report non-recoverable losses for Tees and Reducers (for relief valve calcs).
8) Use IF97 for entropy calcs if enthalpy method is WS97.
9) Add binary interaction coefficients for SRK equation.
10) Estimate overall U value for pipe heat loss calculations.
11) Estimate thermal conductivity and heat capacity.
12) Allow pipe sizes to 10m when sizing pipes.
13) Allow dampening of composition during flash calculations.
14) Add the Hooper 2-K fitting method.
15) Store pipe data in data file to improve portability.
16) Add pseudo components.

Others:
1) Prevent errors on " in text field.
2) Fix bug on importing stream with two liquid phases from Hysys.
3) Increase sensitivity to reduce premature convergence on HMB on recycle circuits with vessels.
4) Show calculated level for Feeds/Products.
5) Correctly show long pipe labels for pipes connected to vessels.
6) Correctly convert mass to mole composition for dialog flash.

Revision 3.0
Scope - Major revision, with emphasis on improving graphical routines.
Revision released – July 2008.

Page 93 of 98

Beta testers – Alain Baillod (Switzerland), Jerry Palmer (Ambitech Engineering), Jeffrey Weiss (Effective Project
Corporation).

Graphical interface:
1) Rewrite graphical routines.
2) Create new equipment by selecting and clicking on drawing, not dragging.
3) Allow selecting, dragging, copying and pasting multiple equipment.
4) Allow equipment to be properly rotated and flipped while connected.
5) Allow equipment labels/data to be relocated or hidden.
6) Allow user to add text, lines, arrows, boxes and circles to drawing.
7) Add support for snapping to grid.
8) Add support for custom paper sizes.
9) Allow user to show or hide default border.
10) Make Vista compatible.
11) Allow user to determine location of files.
12) Convert help file from hlp to html format.
13) Add support for mouse wheel on main form.
14) Add air cooler to exchanger and tank to vessels.
15) Allow expander/reducer symbol to match piping.
16) Option to disable case dialog on double click.

Engineering calculations:
1) Add Beggs-Brill method for horizontal pipes.
2) Add Dukler flow regime maps.
3) Add liquid surface tension to fluid properties.
4) Add momentum acceleration pressure drops.
5) Simplify pump default efficiency calculations.
6) Add option to use smooth pipe friction factors for Dukler and Beggs-Brill.
7) Critically review all Tee equations, modify some.
8) Provide option to fix or clear all pipe sizes.
9) Allow valve size to differ between cases.
10) Add Dukler flow regime maps for vertical and horizontal flow.
11) Modify equations used for expanders and reducers.
12) Support choke flow at Feeds/Products and Expanders.
13) Remove effect of area change for Misc equip and Check valve.

Others:
1) Fix entropy reference state.
2) Fix product elevation bug.
3) Prevent ID=0 error for some cases.
4) Change Dukler holdup name to GPSA.
5) Fix printing large paper sizes bug.

Revision 2.1
Scope - Maintenance release to incorporate customer requested changes.
Revision released – May 2006.
Beta testers – Colt, Canada.

1) Add Case Input Dialog.
2) Add pipes, control valves and orifices calculation tools.
3) Other minor changes and bug fixes.

Revision 2.0
Major revision released – December 2005.
Beta testers – Steve White (PCS, USA), Pat Cullen (BP, Canada), Alain Baillod (Switzerland).

Graphical interface:
1) New install/uninstall program.

Page 94 of 98

2) Use tab control on dialogs.
3) Use spreadsheet type property grid on dialogs.
4) Remove Print Form from most dialogs.
5) Line and equipment numbers must be unique. Names and numbers can be any length.
6) Change vessel nozzle assignments to support HMB. Old problems may looks strange.
7) Data file extension is kdf. Can associate Korf with it.

Engineering calculations:
1) Add flash calculations and Heat and Mole Balance.
2) Add steam tables.
3) Add report for HMB.
4) Add pipe heat loss and exchanger duty.
5) Remove support for PPP.
6) Add support for multiple cases.
7) Improve pump/compressor curves.
8) Add support for other flow meters types.
9) Can specify close up dP for flow meters.
10) Flow meter and control valves account for choked flow.
11) Add support for multiple pipe databases
12) Can ignore non-standard pipe sizes.
13) Rewrite significant parts of code.
14) Review and correct component database. Change some units.
15) Allow phase properties to be 0 if not used.
16) Initialize density elevation on resume.
17) Add dP to Feeds and Products (for spargers).
18) Add support for non-cylindrical pipes.

Others:
1) Use license files instead of registration numbers, renew yearly.
2) Fix Clearview bug.
3) Prevent crash on certain zoom operations.
4) Reposition T/Junctions/Vessels on File | Open and View | Redraw.
5) Correct saving/opening of files using different locale settings (comma as decimal).

Revision 1.5
Scope - Maintenance release to incorporate customer requested changes.
Revision released – Dec 2004.
Beta testers – Linde, Germany.

1) Significantly improve stream importing capabilities.
2) Import single stream from text file, or all streams.
3) Lock certain streams, and ability to override stream numbers.
4) Generate Runlog to show importing results.

Revision 1.4
Scope - Maintenance release to incorporate customer requested changes.
Revision released – Feb 2004.
Beta testers – SNC, Canada.

1) Changes to report. Improve formatting, add header/footers, etc.
2) Modify Hughmark holdup calculation.
3) Calc dP/100ft and velocity for pipe size smaller and larger.
4) Add flow regime to report.

Revision 1.3
Scope - Maintenance release to incorporate customer requested changes.
Revision released – Jan 2003.
Beta testers – PCS, USA.

Page 95 of 98

1) Minor changes to report file.
2) Add more elevation density options.
3) Handle compressor curves similar to pump curves.
4) Correct know bugs

Revision 1.2
Major revision released - April 2001.
Beta testers – Graham Moss, Canada and Tinus Erasmus, South Africa.

Graphical interface:
1) Most equipment can now be rotated through 0, 90, 180 and 270 degrees.
2) All equipment defaults can now be edited.
3) Completely new file save/open format.
4) Drawing now has border, title block and can be in color.
5) Exchangers can be represented as exchangers or fired heaters.
6) Feed/Products can be represented by pipes or tanks.
7) RunLog with all errors is generate during hydraulic simulation.
8) Can view selected properties on drawing.
9) Can import pipe fluid properties from text file or Hysys/Aspen simulation.
10) Report is in rich text format.

Engineering calculations:
1) Change Reducer/Expander calculation to largely eliminate effect of different inlet/outlet line densities.
2) Add acceleration pressure drop to all single and two phase methods.
3) Add T-pieces.
4) Add Vessels.
5) Prevent pressures below zero absolute.
6) Pipe diameter search start at 36" instead of 4" to improve convergence.
7) All fittings can now have a K and/or a L/D value.
8) Pipes from Tanks or Vessels automatically account for the loss in static pressure due to the increase in
velocity.
9) The % opening for control valves is optional. If a full open Cv is provided, Korf will determine the required
valve opening.
10) The flange to flange pressure drop is also reported for orifices.
11) Link with PPP or Hysys for flash calculations.
12) NPSH calculations for pumps.

Bugs fixed:
1) Valve K values is now based on the flowing inlet line density at the valve (not the line average).
2) Rating dP's are now based on the average of equipment inlet/outlet densities, instead of line average
densities.
3) Pump and compressor actual inlet volumes is now based on density at equipment inlet, and not the inlet line
average density.
4) If a pipe is copied to another, the total K and L/D values are updated. Total K and L/D values are also check
before performing the hydraulic calculations.

Revision 1.1
Scope - Maintenance release to incorporate customer requested changes.
Revision released - February 2000.
Beta tester - Roberto Peron, Prode, Italy.

Changes to graphical interface and calculations:
1) Feed and Product nodes are separated from line. Now treated the same as other equipment.
2) Replace Mixer/Splitter node with ideal Junction. As ideal Junction only has one pressure (not inlet and
outlet), any outlet pressure or pressure drop specification for Mixer/Splitter is lost when importing a file from
previous versions.
3) The number of specifications are limited to those typically encountered to make Korf easier to use (limited

Page 96 of 98

Spec options as set under Options|Defaults).
4) All the available specifications (for limited Spec option) can be displayed on the drawing to aid the user in
deciding what to specify. Click on the toolbar button showing "S ?".
5) Flow rates are now specified with Feed, Products or Junctions, and NOT pipes.
6) Specifications shown on the drawing equals the number of Specifications shown in the status bar.
7) Default units can be customize.
8) A 32 bit version is available.
9) Change Pipe Report to vertical format.

Bugs fixed:
1) Double click at equipment outlet with Spec/Results View turned on caused lines to be draw to top left corner.
2) Flow rates are not converted to British units on printing the drawing.
3) Selected box does not change on changing line label length, except if Spec/Results View is turned on.
4) Prevent double quote ("") in names/numbers. Causes file open/save problems.
5) Prevent scrolling during line drawing.
6) Correct Landscape printing in 32 bit version.

Revision 1.0
Major revision released - February 1999.
Beta tester - Elizbe du Toit, Suprachem, South Africa.

Changes to graphical interface:
1) Equipment can now be selected by the mouse and edited from the menu.
2) Drawing can be disabled.
3) By default the flow can only be specified for lines leaving feed or splitter nodes.
4) Reports now include pipe ID, if ID is requested instead of standard pipe size.
5) Re number, friction factors, etc. are now also displayed.

Changes to engineering calculations:
1) Add support for isothermal compressible flow.
2) Add support for several two phase pressure drop (and elevation) methods.
3) Provide graphical representation of two phase flow regime.
4) Only one method (old method 3) is available for solving the circuit(s).
5) Least square solution no longer supported. Number of specs must equal number of variables.
6) Extend line sizing criteria to dP/length, velocity or velocity coefficient. Can be min or max.
7) The standard pipe data is stored in a separate file that can be edited from the menu.
8) Add horsepower calculation (incl. default efficiencies) to pumps and compressors.
9) Improve orifice beta determination convergence.
10) Add support for reducers and expanders with control valves.
11) Add valve opening for control valves.
12) Change viscosity calculation for homogeneous two phase model.
13) Add pure component physical property database.

Bugs fixed:
1) Bug that sometimes caused the pipe properties to be reset when a bend is added.
2) Bug that sometimes caused a unrecoverable error when dragging line bends.
3) Bug that caused valves to be deleted when a orifice is delete (unrecoverable error).

Other changes:
1) Educational version is also marketed by CACHE.
2) Evaluation version is not "crippled" in any way. Other versions do not require a hardware dongle.

Revision 0.1
Maintenance released - June 1998.

Changes:
1) Reset equipment in and outlet pressure before starting new run.
2) Prevent equipment being drag and dropped behind the toolbar.

Page 97 of 98

3) Remove some of the limitations of the evaluation version.

Revision 0
Released - November 1997.
Beta tester Elizbe du Toit, Suprachem, South Africa.

Page 98 of 98

