Start of the Emme to DaySim Python code

As of December 11th, 2012

The first step of this code is to get all the necessary matrices into Emme via the Python Code and set an assignment to run.

In order to utilize faster movement of matrices from Emme to DaySim, Inro has provided us with some very nice binary transfer api's that exist in a version of Emme that we now use (Emme Desktop test-4.0.3-MatrixBinaryFormat).  These API's will make it into future versions of Emme.

Code right now launches an instance of Emme using the GUI.  Path to a project file is hard coded for now, but we should change this soon.

Assignment Specifications are currently set to work for a 21 class assignment as needed by DaySim.  The 21 classes are:

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

The value of time categories used the assignment are coming from DaySim and are:

	Class	$ per Hour		
		Cat #1	Cat #2	Cat #3
	SOV		$2.00	$8.00	$20.00
	HOV 2	$4.00	$16.00	$40.00
	HOV 3+	$6.00	$24.00	$60.00
	Trucks	$40.00	$45.00	$50.00		

	Class	minutes per cent		
		Cat #1	Cat #2	Cat #3
	SOV		0.3000	0.0750	0.0300
	HOV 2	0.1500	0.0375	0.0150
	HOV 3+	0.1000	0.0250	0.0100
	Trucks	0.0150	0.0133	0.0120

The code uses the Emme Tool for creating matrices to create the 84 total demand and skim matrices needed for the model run.  The code overwrites any existing matrices as DaySim will be feeding new demand each time it access Emme for skimming and the skims should change due to the new demand.  There are 21 demand trip tables and 63 total skim tables being created for auto modes (time, cost and distance).  

Naming convention is: class (2 characters), toll/notoll(2 characters), income (1 number), type (1 character)

	1. svtl1v - SOV Toll Income Level 1 Demand
	2. svtl2v - SOV Toll Income Level 1 Demand
	3. svtl3v - SOV Toll Income Level 1 Demand
	4. svnt1v - SOV No Toll Income Level 1 Demand
	5. svnt2v - SOV No Toll Income Level 1 Demand
	6. svnt3v - SOV No Toll Income Level 1 Demand
	7. h2tl1v - HOV 2 Toll Income Level 1 Demand
	8. h2tl2v - HOV 2 Toll Income Level 1 Demand
	9. h2tl3v - HOV 2 Toll Income Level 1 Demand
	10. h2nt1v - HOV 2 No Toll Income Level 1 Demand
	11. h2nt2v - HOV 2 No Toll Income Level 1 Demand
	12. h2nt3v - HOV 2 No Toll Income Level 1 Demand
	13. h3tl1v - HOV 3+ Toll Income Level 1 Demand
	14. h3tl2v - HOV 3+ Toll Income Level 1 Demand
	15. h3tl3v - HOV 3+ Toll Income Level 1 Demand
	16. h3nt1v - HOV 3+ No Toll Income Level 1 Demand
	17. h3nt2v - HOV 3+ No Toll Income Level 1 Demand
	18. h3nt3v - HOV 3+ No Toll Income 
	19. lttrkv - Light Truck Demand
	20. mdtrkv - Medium Truck Demand
	21. hvtrkv - Heavy Truck Demand
	22. svtl1t - SOV Toll Income Level 1 Time
	23. svtl2t - SOV Toll Income Level 1 Time
	24. svtl3t - SOV Toll Income Level 1 Time
	25. svnt1t - SOV No Toll Income Level 1 Time
	26. svnt2t - SOV No Toll Income Level 1 Time
	27. svnt3t - SOV No Toll Income Level 1 Time
	28. h2tl1t - HOV 2 Toll Income Level 1 Time
	29. h2tl2t - HOV 2 Toll Income Level 1 Time
	30. h2tl3t - HOV 2 Toll Income Level 1 Time
	31. h2nt1t - HOV 2 No Toll Income Level 1 Time
	32. h2nt2t - HOV 2 No Toll Income Level 1 Time
	33. h2nt3t - HOV 2 No Toll Income Level 1 Time
	34. h3tl1t - HOV 3+ Toll Income Level 1 Time
	35. h3tl2t - HOV 3+ Toll Income Level 1 Time
	36. h3tl3t - HOV 3+ Toll Income Level 1 Time
	37. h3nt1t - HOV 3+ No Toll Income Level 1 Time
	38. h3nt2t - HOV 3+ No Toll Income Level 1 Time
	39. h3nt3t - HOV 3+ No Toll Income 
	40. lttrkt - Light Truck Time
	41. mdtrkt - Medium Truck Time
	42. hvtrkt - Heavy Truck Time
	43. svtl1c - SOV Toll Income Level 1 Cost
	44. svtl2c - SOV Toll Income Level 1 Cost
	45. svtl3c - SOV Toll Income Level 1 Cost
	46. svnt1c - SOV No Toll Income Level 1 Cost
	47. svnt2c - SOV No Toll Income Level 1 Cost
	48. svnt3c - SOV No Toll Income Level 1 Cost
	49. h2cl1c - HOV 2 Toll Income Level 1 Cost
	50. h2cl2c - HOV 2 Toll Income Level 1 Cost
	51. h2cl3c - HOV 2 Toll Income Level 1 Cost
	52. h2nt1c - HOV 2 No Toll Income Level 1 Cost
	53. h2nt2c - HOV 2 No Toll Income Level 1 Cost
	54. h2nt3c - HOV 2 No Toll Income Level 1 Cost
	55. h3cl1c - HOV 3+ Toll Income Level 1 Cost
	56. h3cl2c - HOV 3+ Toll Income Level 1 Cost
	57. h3cl3c - HOV 3+ Toll Income Level 1 Cost
	58. h3nt1c - HOV 3+ No Toll Income Level 1 Cost
	59. h3nt2c - HOV 3+ No Toll Income Level 1 Cost
	60. h3nt3c - HOV 3+ No Toll Income 
	61. lttrkc - Light Truck Cost
	62. mdtrkc - Medium Truck Cost
	63. hvtrkc - Heavy Truck Cost
	64. svtl1d - SOV Toll Income Level 1 Distance
	65. svtl2d - SOV Toll Income Level 1 Distance
	66. svtl3d - SOV Toll Income Level 1 Distance
	67. svnt1d - SOV No Toll Income Level 1 Distance
	68. svnt2d - SOV No Toll Income Level 1 Distance
	69. svnt3d - SOV No Toll Income Level 1 Distance
	70. h2dl1d - HOV 2 Toll Income Level 1 Distance
	71. h2dl2d - HOV 2 Toll Income Level 1 Distance
	72. h2dl3d - HOV 2 Toll Income Level 1 Distance
	73. h2nt1d - HOV 2 No Toll Income Level 1 Distance
	74. h2nt2d - HOV 2 No Toll Income Level 1 Distance
	75. h2nt3d - HOV 2 No Toll Income Level 1 Distance
	76. h3dl1d - HOV 3+ Toll Income Level 1 Distance
	77. h3dl2d - HOV 3+ Toll Income Level 1 Distance
	78. h3dl3d - HOV 3+ Toll Income Level 1 Distance
	79. h3nt1d - HOV 3+ No Toll Income Level 1 Distance
	80. h3nt2d - HOV 3+ No Toll Income Level 1 Distance
	81. h3nt3d - HOV 3+ No Toll Income 
	82. lttrkc - Light Truck Distance
	83. mdtrkc - Medium Truck Distance
	84. hvtrkc - Heavy Truck Distance


Each skim matrix is being first converted to an integer before it is output to the binary file (note - right now, the binary file still appears to be a float even though the numbers in it are integers).  This is accomplished by multiplying the skim by 100 and using Emme's nInt function to round it to an integer.  The original skims are left as floats in Emme and the conversion occurs via a temporary matrix before outputting.

The next step is to implement the skimming procedures for time, cost and distancwe
