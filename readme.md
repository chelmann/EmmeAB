Start of the Emme to DaySim Python code

As of December 7th, 2012

The first step of this code is to get all the necessary matrices into Emme via the Python Code and set an assignment to run.

In order to utilize faster movement of matrices from Emme to DaySim, Inro has provided us with some very nice binary transfer api's that exist in a version of Emme that we now use (Emme Desktop test-4.0.3-MatrixBinaryFormat).  These API's will make it into future versions of Emme.

Code right now launches an instance of Emme using the GUI.  Path to a project file is hard coded for now, but we should change this soon.

Assignment Specifications are currently set to work for a 11 class assignment but these need to be changed for the 21 classes need for DaySim.  The 21 classes are:

	1. SOV Toll Income Level 1
	2. SOV Toll Income Level 2
	3. SOV Toll Income Level 3
	4. SOV No Toll Income Level 1
	5. SOV No Toll Income Level 2
	6. SOV No Toll Income Level 3
	7. HOV 2 Toll Income Level 1
	8. HOV 2 Toll Income Level 2
	9. HOV 2 Toll Income Level 3
	10. HOV 2 No Toll Income Level 1
	11. HOV 2 No Toll Income Level 2
	12. HOV 2 No Toll Income Level 3
	13. HOV 3 Toll Income Level 1
	14. HOV 3 Toll Income Level 2
	15. HOV 3 Toll Income Level 3
	16. HOV 3 No Toll Income Level 1
	17. HOV 3 No Toll Income Level 2
	18. HOV 3 No Toll Income Level 3
	19. Light Trucks
	20. Medium Trucks
	21. Heavy Trucks

The code uses the Emme Tool for creating matrices to create the 84 total demand and skim matrices needed for the model run.  The code overwrites any exisitng matrices as DaySim will be feeding new demand each time it access Emme for skimming and the skims should change due to the new demand.  There are 21 demand trip tables and 63 total skim tables being created right now (time, cost and distance).

Each skim matrix is being first converted to an integer before it is output to the binary file (note - right now, the binary file still appears to be a float even though the numbers in it are integers).  This is accomplished by multiplying the skim by 100 and using Emme's nInt function to round it to an integer.  The original skims are left as floats in Emme and the conversion occurs via a temporary matrix before outputting.

Once the network is configured to allow 21 classes to use it, the assignment specification will be changed to work with 21 classes and the skim procedures will be added.
