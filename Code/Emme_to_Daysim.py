import inro.emme.desktop.app as app
import inro.modeller as _m
import inro.emme.matrix
import inro.emme.database.matrix
import json
import array as _array
import numpy as _np
import os

# Start an instance of Emme - for now this is using the GUI
my_desktop = app.start_dedicated(False, "cth", 'C:\Users\craig\Documents\ABM\ABM.emp')
my_modeller = _m.Modeller(my_desktop)

# Define a few Emme Tools we will be using
copy_matrix = my_modeller.tool("inro.emme.data.matrix.copy_matrix")
delete_matrix = my_modeller.tool("inro.emme.data.matrix.delete_matrix")
balance_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_balancing")
calculate_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")
assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.path_based_traffic_assignment")
skim_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.path_based_statistics")
convert_to_csv = _m.Modeller().tool("inro.emme.data.matrix.export_matrix_to_csv")
init_matrix = _m.Modeller().tool("inro.emme.data.matrix.init_matrix")
create_matrix = _m.Modeller().tool("inro.emme.data.matrix.create_matrix")

# Define what our scenario and bank we are working in
current_scenario = _m.Modeller().desktop.data_explorer().primary_scenario.core_scenario.ref
emmebank = current_scenario.emmebank

# These are the variable for the Perception Factor's Used in The assignment (representation of the VOT for each vehicle class expressed in minutes / dollar)
pf_1 = 0.0383
pf_2 = 0.0199
pf_3 = 0.0158
pf_4 = 0.0059
pf_5 = 0.0627
pf_6 = 0.034
pf_7 = 0.0233
pf_8 = 0.018
pf_9 = 0.015
pf_10 = 0.0133
pf_11 = 0.012
max_iter = 5
b_rel_gap = 0.0001

#Define Standard Path Based Assignment from Modeller
# this is the specification for an 11 class path based auto assignemnt from Modeller

assign_spec = """{
    "type": "PATH_BASED_TRAFFIC_ASSIGNMENT",
    "classes": [
        {
            "mode": "s",
            "demand": "mfavehda",
            "generalized_cost": {
                "link_costs": "@toll1",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "h",
            "demand": "mfavehs2",
            "generalized_cost": {
                "link_costs": "@toll2",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "i",
            "demand": "mfavehs3",
            "generalized_cost": {
                "link_costs": "@toll3",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "j",
            "demand": "mfavpool",
            "generalized_cost": {
                "link_costs": "@toll4",
                "perception_factor": 0.0059
            }
        },
        {
            "mode": "s",
            "demand": "mfahbw1v",
            "generalized_cost": {
                "link_costs": "@toll1",
                "perception_factor": 0.0627
            }
        },
        {
            "mode": "s",
            "demand": "mfahbw2v",
            "generalized_cost": {
                "link_costs": "@toll1",
                "perception_factor": 0.034
            }
        },
        {
            "mode": "s",
            "demand": "mfahbw3v",
            "generalized_cost": {
                "link_costs": "@toll1",
                "perception_factor": 0.0233
            }
        },
        {
            "mode": "s",
            "demand": "mfahbw4v",
            "generalized_cost": {
                "link_costs": "@toll1",
                "perception_factor": 0.018
            }
        },
        {
            "mode": "v",
            "demand": "mfalttrk",
            "generalized_cost": {
                "link_costs": "@trkc1",
                "perception_factor": 0.015
            }
        },
        {
            "mode": "u",
            "demand": "mfamdtrk",
            "generalized_cost": {
                "link_costs": "@trkc2",
                "perception_factor": 0.0133
            }
        },
        {
            "mode": "t",
            "demand": "mfahvtrk",
            "generalized_cost": {
                "link_costs": "@trkc3",
                "perception_factor": 0.012
            }
        }
    ],
    "performance_settings": {
        "max_path_memory": 3000,
        "gap_computation_freq": 5,
        "path_cost_equality_tolerance": {
            "initial_proportion": 0.001,
            "refinement_iteration": 30,
            "refined_proportion": 0.00001
        }
    },
    "background_traffic": null,
    "stopping_criteria": {
        "max_iterations": 10,
        "best_relative_gap": 0.05,
        "relative_gap": 0.01,
        "normalized_gap": 0.01
    }
}"""

#Define Standard Matrix Calculation Specification from Modeller

matrix_calc_spec = """{
    "expression": "nint(mf1*100)",
    "result": "mftemp",
    "constraint": {
        "by_value": null,
        "by_zone": null
    },
    "aggregation": {
        "origins": null,
        "destinations": null
    },
    "type": "MATRIX_CALCULATION"
}"""

# Create and Initialize all of the SOV Demand matrices to be zero (overwrite any that already exist)
mf1 = create_matrix(matrix_id="mf1",matrix_name="svtl1v",matrix_description="SOV Toll Income Level 1 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf2 = create_matrix(matrix_id="mf2",matrix_name="svtl2v",matrix_description="SOV Toll Income Level 2 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf3 = create_matrix(matrix_id="mf3",matrix_name="svtl3v",matrix_description="SOV Toll Income Level 3 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf4 = create_matrix(matrix_id="mf4",matrix_name="svnt1v",matrix_description="SOV No Toll Income Level 1 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf5 = create_matrix(matrix_id="mf5",matrix_name="svnt2v",matrix_description="SOV No Toll Income Level 2 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf6 = create_matrix(matrix_id="mf6",matrix_name="svnt3v",matrix_description="SOV No Toll Income Level 3 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
# Create and Initialize all of the HOV 2 Demand matrices to be zero (overwrite any that already exist)
mf7 = create_matrix(matrix_id="mf7",matrix_name="h2tl1v",matrix_description="HOV 2 Toll Income Level 1 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf8 = create_matrix(matrix_id="mf8",matrix_name="h2tl2v",matrix_description="HOV 2 Toll Income Level 2 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf9 = create_matrix(matrix_id="mf9",matrix_name="h2tl3v",matrix_description="HOV 2 Toll Income Level 3 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf10 = create_matrix(matrix_id="mf10",matrix_name="h2nt1v",matrix_description="HOV 2 No Toll Income Level 1 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf11 = create_matrix(matrix_id="mf11",matrix_name="h2nt2v",matrix_description="HOV 2 No Toll Income Level 2 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf12 = create_matrix(matrix_id="mf12",matrix_name="h2nt3v",matrix_description="HOV 2 No Toll Income Level 3 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
# Create and Initialize all of the HOV 3+ Demand matrices to be zero (overwrite any that already exist)
mf13 = create_matrix(matrix_id="mf13",matrix_name="s3tl1v",matrix_description="HOV 3+ Toll Income Level 1 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf14 = create_matrix(matrix_id="mf14",matrix_name="s3tl2v",matrix_description="HOV 3+ Toll Income Level 2 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf15 = create_matrix(matrix_id="mf15",matrix_name="s3tl3v",matrix_description="HOV 3+ Toll Income Level 3 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf16 = create_matrix(matrix_id="mf16",matrix_name="s3nt1v",matrix_description="HOV 3+ No Toll Income Level 1 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf17 = create_matrix(matrix_id="mf17",matrix_name="s3nt2v",matrix_description="HOV 3+ No Toll Income Level 2 Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf18 = create_matrix(matrix_id="mf18",matrix_name="s3nt3v",matrix_description="HOV 3+ No Toll Income Level 3 Demand",default_value=0,overwrite=True,scenario=current_scenario)
# Create and Initialize all of the Truck Demand matrices to be zero (overwrite any that already exist)
mf19 = create_matrix(matrix_id="mf19",matrix_name="lttrkv",matrix_description="Light Truck Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf20 = create_matrix(matrix_id="mf20",matrix_name="mdtrkv",matrix_description="Medium Truck Demand",default_value=0,overwrite=True,scenario=current_scenario) 
mf21 = create_matrix(matrix_id="mf21",matrix_name="hvtrkv",matrix_description="Heavy Truck Demand",default_value=0,overwrite=True,scenario=current_scenario) 
# Create and Initialize all of the SOV Time Skim matrices to be zero (overwrite any that already exist)
mf22 = create_matrix(matrix_id="mf22",matrix_name="svtl1t",matrix_description="SOV Toll Income Level 1 Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf23 = create_matrix(matrix_id="mf23",matrix_name="svtl2t",matrix_description="SOV Toll Income Level 2 Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf24 = create_matrix(matrix_id="mf24",matrix_name="svtl3t",matrix_description="SOV Toll Income Level 3 Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf25 = create_matrix(matrix_id="mf25",matrix_name="svnt1t",matrix_description="SOV No Toll Income Level 1 Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf26 = create_matrix(matrix_id="mf26",matrix_name="svnt2t",matrix_description="SOV No Toll Income Level 2 Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf27 = create_matrix(matrix_id="mf27",matrix_name="svnt3t",matrix_description="SOV No Toll Income Level 3 Time",default_value=0,overwrite=True,scenario=current_scenario)
# Create and Initialize all of the SOV Cost Skim matrices to be zero (overwrite any that already exist)
mf28 = create_matrix(matrix_id="mf28",matrix_name="svtl1c",matrix_description="SOV Toll Income Level 1 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf29 = create_matrix(matrix_id="mf29",matrix_name="svtl2c",matrix_description="SOV Toll Income Level 2 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf30 = create_matrix(matrix_id="mf30",matrix_name="svtl3c",matrix_description="SOV Toll Income Level 3 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf31 = create_matrix(matrix_id="mf31",matrix_name="svnt1c",matrix_description="SOV No Toll Income Level 1 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf32 = create_matrix(matrix_id="mf32",matrix_name="svnt2c",matrix_description="SOV No Toll Income Level 2 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf33 = create_matrix(matrix_id="mf33",matrix_name="svnt3c",matrix_description="SOV No Toll Income Level 3 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
# Create and Initialize all of the SOV Distance Skim matrices to be zero (overwrite any that already exist)
mf34 = create_matrix(matrix_id="mf34",matrix_name="svtl1d",matrix_description="SOV Toll Income Level 1 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf35 = create_matrix(matrix_id="mf35",matrix_name="svtl2d",matrix_description="SOV Toll Income Level 2 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf36 = create_matrix(matrix_id="mf36",matrix_name="svtl3d",matrix_description="SOV Toll Income Level 3 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf37 = create_matrix(matrix_id="mf37",matrix_name="svnt1d",matrix_description="SOV No Toll Income Level 1 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf38 = create_matrix(matrix_id="mf38",matrix_name="svnt2d",matrix_description="SOV No Toll Income Level 2 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf39 = create_matrix(matrix_id="mf39",matrix_name="svnt3d",matrix_description="SOV No Toll Income Level 3 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
# Create and Initialize all of the HOV 2 Time Skim matrices matrices to be zero (overwrite any that already exist)
mf40 = create_matrix(matrix_id="mf40",matrix_name="h2tl1t",matrix_description="HOV 2 Toll Income Level 1 Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf41 = create_matrix(matrix_id="mf41",matrix_name="h2tl2t",matrix_description="HOV 2 Toll Income Level 2 Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf42 = create_matrix(matrix_id="mf42",matrix_name="h2tl3t",matrix_description="HOV 2 Toll Income Level 3 Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf43 = create_matrix(matrix_id="mf43",matrix_name="h2nt1t",matrix_description="HOV 2 No Toll Income Level 1 Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf44 = create_matrix(matrix_id="mf44",matrix_name="h2nt2t",matrix_description="HOV 2 No Toll Income Level 2 Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf45 = create_matrix(matrix_id="mf45",matrix_name="h2nt3t",matrix_description="HOV 2 No Toll Income Level 3 Time",default_value=0,overwrite=True,scenario=current_scenario) 
# Create and Initialize all of the HOV 2 Cost Skim matrices matrices to be zero (overwrite any that already exist)
mf46 = create_matrix(matrix_id="mf46",matrix_name="h2tl1c",matrix_description="HOV 2 Toll Income Level 1 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf47 = create_matrix(matrix_id="mf47",matrix_name="h2tl2c",matrix_description="HOV 2 Toll Income Level 2 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf48 = create_matrix(matrix_id="mf48",matrix_name="h2tl3c",matrix_description="HOV 2 Toll Income Level 3 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf49 = create_matrix(matrix_id="mf49",matrix_name="h2nt1c",matrix_description="HOV 2 No Toll Income Level 1 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf50 = create_matrix(matrix_id="mf50",matrix_name="h2nt2c",matrix_description="HOV 2 No Toll Income Level 2 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf51 = create_matrix(matrix_id="mf51",matrix_name="h2nt3c",matrix_description="HOV 2 No Toll Income Level 3 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
# Create and Initialize all of the HOV 2 Distance Skim matrices matrices to be zero (overwrite any that already exist)
mf52 = create_matrix(matrix_id="mf52",matrix_name="h2tl1d",matrix_description="HOV 2 Toll Income Level 1 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf53 = create_matrix(matrix_id="mf53",matrix_name="h2tl2d",matrix_description="HOV 2 Toll Income Level 2 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf54 = create_matrix(matrix_id="mf54",matrix_name="h2tl3d",matrix_description="HOV 2 Toll Income Level 3 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf55 = create_matrix(matrix_id="mf55",matrix_name="h2nt1d",matrix_description="HOV 2 No Toll Income Level 1 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf56 = create_matrix(matrix_id="mf56",matrix_name="h2nt2d",matrix_description="HOV 2 No Toll Income Level 2 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf57 = create_matrix(matrix_id="mf57",matrix_name="h2nt3d",matrix_description="HOV 2 No Toll Income Level 3 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
# Create and Initialize all of the HOV 3+ Time Skim matrices matrices to be zero (overwrite any that already exist)
mf58 = create_matrix(matrix_id="mf58",matrix_name="s3tl1t",matrix_description="HOV 3+ Toll Income Level 1 Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf59 = create_matrix(matrix_id="mf59",matrix_name="s3tl2t",matrix_description="HOV 3+ Toll Income Level 2 Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf60 = create_matrix(matrix_id="mf60",matrix_name="s3tl3t",matrix_description="HOV 3+ Toll Income Level 3 Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf61 = create_matrix(matrix_id="mf61",matrix_name="s3nt1t",matrix_description="HOV 3+ No Toll Income Level 1 Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf62 = create_matrix(matrix_id="mf62",matrix_name="s3nt2t",matrix_description="HOV 3+ No Toll Income Level 2 Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf63 = create_matrix(matrix_id="mf63",matrix_name="s3nt3t",matrix_description="HOV 3+ No Toll Income Level 3 Time",default_value=0,overwrite=True,scenario=current_scenario)
# Create and Initialize all of the HOV 3+ Cost Skim matrices matrices to be zero (overwrite any that already exist)
mf64 = create_matrix(matrix_id="mf64",matrix_name="s3tl1c",matrix_description="HOV 3+ Toll Income Level 1 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf65 = create_matrix(matrix_id="mf65",matrix_name="s3tl2c",matrix_description="HOV 3+ Toll Income Level 2 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf66 = create_matrix(matrix_id="mf66",matrix_name="s3tl3c",matrix_description="HOV 3+ Toll Income Level 3 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf67 = create_matrix(matrix_id="mf67",matrix_name="s3nt1c",matrix_description="HOV 3+ No Toll Income Level 1 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf68 = create_matrix(matrix_id="mf68",matrix_name="s3nt2c",matrix_description="HOV 3+ No Toll Income Level 2 Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf69 = create_matrix(matrix_id="mf69",matrix_name="s3nt3c",matrix_description="HOV 3+ No Toll Income Level 3 Cost",default_value=0,overwrite=True,scenario=current_scenario)
# Create and Initialize all of the HOV 3+ Distance Skim matrices matrices to be zero (overwrite any that already exist)
mf70 = create_matrix(matrix_id="mf70",matrix_name="s3tl1d",matrix_description="HOV 3+ Toll Income Level 1 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf71 = create_matrix(matrix_id="mf71",matrix_name="s3tl2d",matrix_description="HOV 3+ Toll Income Level 2 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf72 = create_matrix(matrix_id="mf72",matrix_name="s3tl3d",matrix_description="HOV 3+ Toll Income Level 3 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf73 = create_matrix(matrix_id="mf73",matrix_name="s3nt1d",matrix_description="HOV 3+ No Toll Income Level 1 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf74 = create_matrix(matrix_id="mf74",matrix_name="s3nt2d",matrix_description="HOV 3+ No Toll Income Level 2 Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf75 = create_matrix(matrix_id="mf75",matrix_name="s3nt3d",matrix_description="HOV 3+ No Toll Income Level 3 Distance",default_value=0,overwrite=True,scenario=current_scenario)
# Create and Initialize all of the Truck Time Skim matrices matrices to be zero (overwrite any that already exist)
mf76 = create_matrix(matrix_id="mf76",matrix_name="lttrkt",matrix_description="Light Truck Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf77 = create_matrix(matrix_id="mf77",matrix_name="mdtrkt",matrix_description="Medium Truck Time",default_value=0,overwrite=True,scenario=current_scenario) 
mf78 = create_matrix(matrix_id="mf78",matrix_name="hvtrkt",matrix_description="Heavy Truck Time",default_value=0,overwrite=True,scenario=current_scenario) 
# Create and Initialize all of the Truck Cost Skim matrices matrices to be zero (overwrite any that already exist)
mf79 = create_matrix(matrix_id="mf79",matrix_name="lttrkc",matrix_description="Light Truck Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf80 = create_matrix(matrix_id="mf80",matrix_name="mdtrkc",matrix_description="Medium Truck Cost",default_value=0,overwrite=True,scenario=current_scenario) 
mf81 = create_matrix(matrix_id="mf81",matrix_name="hvtrkc",matrix_description="Heavy Truck Cost",default_value=0,overwrite=True,scenario=current_scenario) 
# Create and Initialize all of the Truck Distance Skim matrices matrices to be zero (overwrite any that already exist)
mf82 = create_matrix(matrix_id="mf82",matrix_name="lttrkd",matrix_description="Light Truck Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf83 = create_matrix(matrix_id="mf83",matrix_name="mdtrkd",matrix_description="Medium Truck Distance",default_value=0,overwrite=True,scenario=current_scenario) 
mf84 = create_matrix(matrix_id="mf84",matrix_name="hvtrkd",matrix_description="Heavy Truck Distance",default_value=0,overwrite=True,scenario=current_scenario) 
# Create and Initialize all of the Temporary matrices to be zero (overwrite any that already exist)
mf101 = create_matrix(matrix_id="mf101",matrix_name="temp01",matrix_description="Temporary Calculation Matrix 1",default_value=0,overwrite=True,scenario=current_scenario) 
mf102 = create_matrix(matrix_id="mf102",matrix_name="temp02",matrix_description="Temporary Calculation Matrix 2",default_value=0,overwrite=True,scenario=current_scenario) 
mf103 = create_matrix(matrix_id="mf103",matrix_name="temp03",matrix_description="Temporary Calculation Matrix 3",default_value=0,overwrite=True,scenario=current_scenario) 
mf104 = create_matrix(matrix_id="mf104",matrix_name="temp04",matrix_description="Temporary Calculation Matrix 4",default_value=0,overwrite=True,scenario=current_scenario) 
mf105 = create_matrix(matrix_id="mf105",matrix_name="temp05",matrix_description="Temporary Calculation Matrix 5",default_value=0,overwrite=True,scenario=current_scenario) 
mf106 = create_matrix(matrix_id="mf106",matrix_name="temp06",matrix_description="Temporary Calculation Matrix 6",default_value=0,overwrite=True,scenario=current_scenario) 
mf107 = create_matrix(matrix_id="mf107",matrix_name="temp07",matrix_description="Temporary Calculation Matrix 7",default_value=0,overwrite=True,scenario=current_scenario) 
mf108 = create_matrix(matrix_id="mf108",matrix_name="temp08",matrix_description="Temporary Calculation Matrix 8",default_value=0,overwrite=True,scenario=current_scenario) 
mf109 = create_matrix(matrix_id="mf109",matrix_name="temp09",matrix_description="Temporary Calculation Matrix 9",default_value=0,overwrite=True,scenario=current_scenario) 
mf110 = create_matrix(matrix_id="mf110",matrix_name="temp10",matrix_description="Temporary Calculation Matrix 10",default_value=0,overwrite=True,scenario=current_scenario) 

# Items to run an assignment,  First we modify the generic spec to work for our time period
# Modify the Assignment Specifications for the Closure Criteria and Perception Factors
mod_assign_spec = json.loads(assign_spec)
mod_assign_spec["stopping_criteria"]["max_iterations"]= max_iter
mod_assign_spec["stopping_criteria"]["best_relative_gap"]= b_rel_gap
for x in range(0, 10):
    mod_assign_spec["classes"][x]["generalized_cost"]["perception_factor"] = "pf_"+ `x+1`

# Now we call the Emme Path Based Assignment using our modified spec.
#assign_traffic(mod_assign_spec)

# Write out All the Skim Files to a Binary format, looping through all of the skim matrices (currently Matrices 22 - 84).
# Mulitplies each skim by 100 and stores as a integer into Temporary Matrix #1 for easier storage for DaySim
for x in range (22, 85):
    skim_matrix_id = emmebank.matrix("mf"+`x`)
    output_matrix_id = emmebank.matrix("mftemp01")
    mod_mat_spec = json.loads(matrix_calc_spec)
    mat_calc = "nint(mf"+`x`+"*100)"
    mod_mat_spec["result"]="mftemp01"
    mod_mat_spec["expression"]=mat_calc
    calculate_matrix(mod_mat_spec)
    skim_mat_name = emmebank.matrix(skim_matrix_id).name
    skim_mat_val = inro.emme.database.matrix.FullMatrix.get_data(output_matrix_id,current_scenario)
    skim_filename = os.path.join(os.path.dirname(emmebank.path), 'Skims\\'+skim_mat_name+'.out')
    inro.emme.matrix.MatrixData.save(skim_mat_val,skim_filename)
    
#convert_to_csv(matrices=["mf1","mf2","mf3","mf4","mf5"])

my_desktop.close()
