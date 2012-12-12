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

# Value of Time Categories by Vehicle Type for Assignments
percept_factors = {"classes": [{'name': "SOV Toll Income Level 1",'vot': 0.3000},
                  {'name': "SOV Toll Income Level 2",'vot': 0.0750},
                  {'name': "SOV Toll Income Level 3",'vot': 0.0300},
                  {'name': "SOV No Toll Income Level 1",'vot': 0.3000},
                  {'name': "SOV No Toll Income Level 2",'vot': 0.0750},
                  {'name': "SOV No Toll Income Level 3",'vot': 0.0300},
                  {'name': "HOV 2 Toll Income Level 1",'vot': 0.1500},
                  {'name': "HOV 2 Toll Income Level 2",'vot': 0.0375},
                  {'name': "HOV 2 Toll Income Level 3",'vot': 0.0150},
                  {'name': "HOV 2 No Toll Income Level 1",'vot': 0.1500},
                  {'name': "HOV 2 No Toll Income Level 2",'vot': 0.0375},
                  {'name': "HOV 2 No Toll Income Level 3",'vot': 0.0150},
                  {'name': "HOV 3 Toll Income Level 1",'vot': 0.1000},
                  {'name': "HOV 3 Toll Income Level 2",'vot': 0.0250},
                  {'name': "HOV 3 Toll Income Level 3",'vot': 0.0100},
                  {'name': "HOV 3 No Toll Income Level 1",'vot': 0.1000},
                  {'name': "HOV 3 No Toll Income Level 2",'vot': 0.0250},
                  {'name': "HOV 3 No Toll Income Level 3",'vot': 0.0100},
                  {'name': "Light Trucks",'vot': 0.0150},
                  {'name': "Medium Trucks",'vot': 0.0133},
                  {'name': "Heavy Trucks",'vot': 0.0120}
                               ]
}  

# Demand, Time, Cost and and Distance Matrices needed in Emme model to run assignments and store skims
emme_matrices = {"classes": [{'mat_id': "mf1",'mat_name': "svtl1v",'mat_desc': "SOV Toll Income Level 1 Demand"},
                             {'mat_id': "mf2",'mat_name': "svtl2v",'mat_desc': "SOV Toll Income Level 2 Demand"},
                             {'mat_id': "mf3",'mat_name': "svtl3v",'mat_desc': "SOV Toll Income Level 3 Demand"},
                             {'mat_id': "mf4",'mat_name': "svnt1v",'mat_desc': "SOV No Toll Income Level 1 Demand"},
                             {'mat_id': "mf5",'mat_name': "svnt2v",'mat_desc': "SOV No Toll Income Level 2 Demand"},
                             {'mat_id': "mf6",'mat_name': "svnt3v",'mat_desc': "SOV No Toll Income Level 3 Demand"},
                             {'mat_id': "mf7",'mat_name': "h2tl1v",'mat_desc': "HOV 2 Toll Income Level 1 Demand"},
                             {'mat_id': "mf8",'mat_name': "h2tl2v",'mat_desc': "HOV 2 Toll Income Level 2 Demand"},
                             {'mat_id': "mf9",'mat_name': "h2tl3v",'mat_desc': "HOV 2 Toll Income Level 3 Demand"},
                             {'mat_id': "mf10",'mat_name': "h2nt1v",'mat_desc': "HOV 2 No Toll Income Level 1 Demand"},
                             {'mat_id': "mf11",'mat_name': "h2nt2v",'mat_desc': "HOV 2 No Toll Income Level 2 Demand"},
                             {'mat_id': "mf12",'mat_name': "h2nt3v",'mat_desc': "HOV 2 No Toll Income Level 3 Demand"},
                             {'mat_id': "mf13",'mat_name': "h3tl1v",'mat_desc': "HOV 3 Toll Income Level 1 Demand"},
                             {'mat_id': "mf14",'mat_name': "h3tl2v",'mat_desc': "HOV 3 Toll Income Level 2 Demand"},
                             {'mat_id': "mf15",'mat_name': "h3tl3v",'mat_desc': "HOV 3 Toll Income Level 3 Demand"},
                             {'mat_id': "mf16",'mat_name': "h3nt1v",'mat_desc': "HOV 3 No Toll Income Level 1 Demand"},
                             {'mat_id': "mf17",'mat_name': "h3nt2v",'mat_desc': "HOV 3 No Toll Income Level 2 Demand"},
                             {'mat_id': "mf18",'mat_name': "h3nt3v",'mat_desc': "HOV 3 No Toll Income Level 3 Demand"},
                             {'mat_id': "mf19",'mat_name': "lttrkv",'mat_desc': "Light Truck Demand"},
                             {'mat_id': "mf20",'mat_name': "mdtrkv",'mat_desc': "Medium Truck Demand"},
                             {'mat_id': "mf21",'mat_name': "hvtrkv",'mat_desc': "Heavy Truck Demand"},
                             {'mat_id': "mf22",'mat_name': "svtl1t",'mat_desc': "SOV Toll Income Level 1 Time"},
                             {'mat_id': "mf23",'mat_name': "svtl2t",'mat_desc': "SOV Toll Income Level 2 Time"},
                             {'mat_id': "mf24",'mat_name': "svtl3t",'mat_desc': "SOV Toll Income Level 3 Time"},
                             {'mat_id': "mf25",'mat_name': "svnt1t",'mat_desc': "SOV No Toll Income Level 1 Time"},
                             {'mat_id': "mf26",'mat_name': "svnt2t",'mat_desc': "SOV No Toll Income Level 2 Time"},
                             {'mat_id': "mf27",'mat_name': "svnt3t",'mat_desc': "SOV No Toll Income Level 3 Time"},
                             {'mat_id': "mf28",'mat_name': "h2tl1t",'mat_desc': "HOV 2 Toll Income Level 1 Time"},
                             {'mat_id': "mf29",'mat_name': "h2tl2t",'mat_desc': "HOV 2 Toll Income Level 2 Time"},
                             {'mat_id': "mf30",'mat_name': "h2tl3t",'mat_desc': "HOV 2 Toll Income Level 3 Time"},
                             {'mat_id': "mf31",'mat_name': "h2nt1t",'mat_desc': "HOV 2 No Toll Income Level 1 Time"},
                             {'mat_id': "mf32",'mat_name': "h2nt2t",'mat_desc': "HOV 2 No Toll Income Level 2 Time"},
                             {'mat_id': "mf33",'mat_name': "h2nt3t",'mat_desc': "HOV 2 No Toll Income Level 3 Time"},
                             {'mat_id': "mf34",'mat_name': "h3tl1t",'mat_desc': "HOV 3 Toll Income Level 1 Time"},
                             {'mat_id': "mf35",'mat_name': "h3tl2t",'mat_desc': "HOV 3 Toll Income Level 2 Time"},
                             {'mat_id': "mf36",'mat_name': "h3tl3t",'mat_desc': "HOV 3 Toll Income Level 3 Time"},
                             {'mat_id': "mf37",'mat_name': "h3nt1t",'mat_desc': "HOV 3 No Toll Income Level 1 Time"},
                             {'mat_id': "mf38",'mat_name': "h3nt2t",'mat_desc': "HOV 3 No Toll Income Level 2 Time"},
                             {'mat_id': "mf39",'mat_name': "h3nt3t",'mat_desc': "HOV 3 No Toll Income Level 3 Time"},
                             {'mat_id': "mf40",'mat_name': "lttrkt",'mat_desc': "Light Truck Time"},
                             {'mat_id': "mf41",'mat_name': "mdtrkt",'mat_desc': "Medium Truck Time"},
                             {'mat_id': "mf42",'mat_name': "hvtrkt",'mat_desc': "Heavy Truck Time"},
                             {'mat_id': "mf43",'mat_name': "svtl1c",'mat_desc': "SOV Toll Income Level 1 Cost"},
                             {'mat_id': "mf44",'mat_name': "svtl2c",'mat_desc': "SOV Toll Income Level 2 Cost"},
                             {'mat_id': "mf45",'mat_name': "svtl3c",'mat_desc': "SOV Toll Income Level 3 Cost"},
                             {'mat_id': "mf46",'mat_name': "svnt1c",'mat_desc': "SOV No Toll Income Level 1 Cost"},
                             {'mat_id': "mf47",'mat_name': "svnt2c",'mat_desc': "SOV No Toll Income Level 2 Cost"},
                             {'mat_id': "mf48",'mat_name': "svnt3c",'mat_desc': "SOV No Toll Income Level 3 Cost"},
                             {'mat_id': "mf49",'mat_name': "h2tl1c",'mat_desc': "HOV 2 Toll Income Level 1 Cost"},
                             {'mat_id': "mf50",'mat_name': "h2tl2c",'mat_desc': "HOV 2 Toll Income Level 2 Cost"},
                             {'mat_id': "mf51",'mat_name': "h2tl3c",'mat_desc': "HOV 2 Toll Income Level 3 Cost"},
                             {'mat_id': "mf52",'mat_name': "h2nt1c",'mat_desc': "HOV 2 No Toll Income Level 1 Cost"},
                             {'mat_id': "mf53",'mat_name': "h2nt2c",'mat_desc': "HOV 2 No Toll Income Level 2 Cost"},
                             {'mat_id': "mf54",'mat_name': "h2nt3c",'mat_desc': "HOV 2 No Toll Income Level 3 Cost"},
                             {'mat_id': "mf55",'mat_name': "h3tl1c",'mat_desc': "HOV 3 Toll Income Level 1 Cost"},
                             {'mat_id': "mf56",'mat_name': "h3tl2c",'mat_desc': "HOV 3 Toll Income Level 2 Cost"},
                             {'mat_id': "mf57",'mat_name': "h3tl3c",'mat_desc': "HOV 3 Toll Income Level 3 Cost"},
                             {'mat_id': "mf58",'mat_name': "h3nt1c",'mat_desc': "HOV 3 No Toll Income Level 1 Cost"},
                             {'mat_id': "mf59",'mat_name': "h3nt2c",'mat_desc': "HOV 3 No Toll Income Level 2 Cost"},
                             {'mat_id': "mf60",'mat_name': "h3nt3c",'mat_desc': "HOV 3 No Toll Income Level 3 Cost"},
                             {'mat_id': "mf61",'mat_name': "lttrkc",'mat_desc': "Light Truck Cost"},
                             {'mat_id': "mf62",'mat_name': "mdtrkc",'mat_desc': "Medium Truck Cost"},
                             {'mat_id': "mf63",'mat_name': "hvtrkc",'mat_desc': "Heavy Truck Cost"},
                             {'mat_id': "mf64",'mat_name': "svtl1d",'mat_desc': "SOV Toll Income Level 1 Distance"},
                             {'mat_id': "mf65",'mat_name': "svtl2d",'mat_desc': "SOV Toll Income Level 2 Distance"},
                             {'mat_id': "mf66",'mat_name': "svtl3d",'mat_desc': "SOV Toll Income Level 3 Distance"},
                             {'mat_id': "mf67",'mat_name': "svnt1d",'mat_desc': "SOV No Toll Income Level 1 Distance"},
                             {'mat_id': "mf68",'mat_name': "svnt2d",'mat_desc': "SOV No Toll Income Level 2 Distance"},
                             {'mat_id': "mf69",'mat_name': "svnt3d",'mat_desc': "SOV No Toll Income Level 3 Distance"},
                             {'mat_id': "mf70",'mat_name': "h2tl1d",'mat_desc': "HOV 2 Toll Income Level 1 Distance"},
                             {'mat_id': "mf71",'mat_name': "h2tl2d",'mat_desc': "HOV 2 Toll Income Level 2 Distance"},
                             {'mat_id': "mf72",'mat_name': "h2tl3d",'mat_desc': "HOV 2 Toll Income Level 3 Distance"},
                             {'mat_id': "mf73",'mat_name': "h2nt1d",'mat_desc': "HOV 2 No Toll Income Level 1 Distance"},
                             {'mat_id': "mf74",'mat_name': "h2nt2d",'mat_desc': "HOV 2 No Toll Income Level 2 Distance"},
                             {'mat_id': "mf75",'mat_name': "h2nt3d",'mat_desc': "HOV 2 No Toll Income Level 3 Distance"},
                             {'mat_id': "mf76",'mat_name': "h3tl1d",'mat_desc': "HOV 3 Toll Income Level 1 Distance"},
                             {'mat_id': "mf77",'mat_name': "h3tl2d",'mat_desc': "HOV 3 Toll Income Level 2 Distance"},
                             {'mat_id': "mf78",'mat_name': "h3tl3d",'mat_desc': "HOV 3 Toll Income Level 3 Distance"},
                             {'mat_id': "mf79",'mat_name': "h3nt1d",'mat_desc': "HOV 3 No Toll Income Level 1 Distance"},
                             {'mat_id': "mf80",'mat_name': "h3nt2d",'mat_desc': "HOV 3 No Toll Income Level 2 Distance"},
                             {'mat_id': "mf81",'mat_name': "h3nt3d",'mat_desc': "HOV 3 No Toll Income Level 3 Distance"},
                             {'mat_id': "mf82",'mat_name': "lttrkd",'mat_desc': "Light Truck Distance"},
                             {'mat_id': "mf83",'mat_name': "mdtrkd",'mat_desc': "Medium Truck Distance"},
                             {'mat_id': "mf84",'mat_name': "hvtrkd",'mat_desc': "Heavy Truck Distance"},
                             {'mat_id': "mf101",'mat_name': "temp01",'mat_desc': "Temporary Calculation Matrix #1"}                             
                             ]
}                  

# Assignment Convergence Criteria
max_iter = 5
b_rel_gap = 0.0001

#Define Standard Path Based Assignment from Modeller
# this is the specification for an 11 class path based auto assignemnt from Modeller

assign_spec = """{
    "type": "PATH_BASED_TRAFFIC_ASSIGNMENT",
    "classes": [
        {
            "mode": "e",
            "demand": "mfsvtl1v",
            "generalized_cost": {
                "link_costs": "@toll1",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "e",
            "demand": "mfsvtl2v",
            "generalized_cost": {
                "link_costs": "@toll1",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "e",
            "demand": "mfsvtl3v",
            "generalized_cost": {
                "link_costs": "@toll1",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "s",
            "demand": "mfsvnt1v",
            "generalized_cost": {
                "link_costs": "@toll1",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "s",
            "demand": "mfsvnt2v",
            "generalized_cost": {
                "link_costs": "@toll1",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "s",
            "demand": "mfsvnt3v",
            "generalized_cost": {
                "link_costs": "@toll1",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "h",
            "demand": "mfh2tl1v",
            "generalized_cost": {
                "link_costs": "@toll2",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "h",
            "demand": "mfh2tl2v",
            "generalized_cost": {
                "link_costs": "@toll2",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "h",
            "demand": "mfh2tl3v",
            "generalized_cost": {
                "link_costs": "@toll2",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "d",
            "demand": "mfh2nt1v",
            "generalized_cost": {
                "link_costs": "@toll2",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "d",
            "demand": "mfh2nt2v",
            "generalized_cost": {
                "link_costs": "@toll2",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "d",
            "demand": "mfh2nt3v",
            "generalized_cost": {
                "link_costs": "@toll2",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "i",
            "demand": "mfh3tl1v",
            "generalized_cost": {
                "link_costs": "@toll3",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "i",
            "demand": "mfh3tl2v",
            "generalized_cost": {
                "link_costs": "@toll3",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "i",
            "demand": "mfh3tl3v",
            "generalized_cost": {
                "link_costs": "@toll3",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "m",
            "demand": "mfh3nt1v",
            "generalized_cost": {
                "link_costs": "@toll3",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "m",
            "demand": "mfh3nt2v",
            "generalized_cost": {
                "link_costs": "@toll3",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "m",
            "demand": "mfh3nt3v",
            "generalized_cost": {
                "link_costs": "@toll3",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "v",
            "demand": "mflttrkv",
            "generalized_cost": {
                "link_costs": "@trkc1",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "u",
            "demand": "mfmdtrkv",
            "generalized_cost": {
                "link_costs": "@trkc2",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "t",
            "demand": "mfhvtrkv",
            "generalized_cost": {
                "link_costs": "@trkc3",
                "perception_factor": 1.0
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

# Create the Matrices in Emme Using the Emme Matrices Dictionary 
for x in range(0, 85):
    create_matrix(matrix_id=emme_matrices["classes"][x]["mat_id"],
                  matrix_name=emme_matrices["classes"][x]["mat_name"],
                  matrix_description=emme_matrices["classes"][x]["mat_desc"],
                  default_value=0,
                  overwrite=True,
                  scenario=current_scenario)

# Items to run an assignment,  First we modify the generic spec to work for our time period
# Modify the Assignment Specifications for the Closure Criteria and Perception Factors
mod_assign_spec = json.loads(assign_spec)
mod_assign_spec["stopping_criteria"]["max_iterations"]= max_iter
mod_assign_spec["stopping_criteria"]["best_relative_gap"]= b_rel_gap
for x in range(0, 21):
    mod_assign_spec["classes"][x]["generalized_cost"]["perception_factor"] = percept_factors["classes"][x]["vot"]
    mod_assign_spec["classes"][x]["demand"] = "mf"+ emme_matrices["classes"][x]["mat_name"]

# Now we call the Emme Path Based Assignment using our modified spec.
assign_traffic(mod_assign_spec)
skim_traffic(cost_skim_spec)

# Write out All the Skim Files to a Binary format, looping through all of the skim matrices (currently Matrices 22 - 84).
for x in range (22, 85):
    skim_matrix_id = emmebank.matrix("mf"+`x`)
    #output_matrix_id = emmebank.matrix("mftemp01")
    #mod_mat_spec = json.loads(matrix_calc_spec)
    #mat_calc = "nint(mf"+`x`+"*100)"
    #mod_mat_spec["result"]="mftemp01"
    #mod_mat_spec["expression"]=mat_calc
    #calculate_matrix(mod_mat_spec)
    skim_mat_name = emmebank.matrix(skim_matrix_id).name
    skim_mat_val = inro.emme.database.matrix.FullMatrix.get_data(skim_matrix_id,current_scenario)
    skim_filename = os.path.join(os.path.dirname(emmebank.path), 'Skims\\'+skim_mat_name+'.out')
    inro.emme.matrix.MatrixData.save(skim_mat_val,skim_filename)
    
#convert_to_csv(matrices=["mf1","mf2","mf3","mf4","mf5"])

my_desktop.close()

