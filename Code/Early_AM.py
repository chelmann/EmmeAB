import array as _array
import inro.emme.desktop.app as app
import inro.modeller as _m
import inro.emme.matrix
import inro.emme.database.matrix
import json
import numpy as _np
import time
import os

# Start an instance of Emme - for now this is using the GUI
start_of_run = time.time()
my_desktop = app.start_dedicated(False, "cth", 'C:\Users\craig\Documents\ABM\ABM.emp')
my_modeller = _m.Modeller(my_desktop)

# Emme and Modeller Tools we used for the assignment and skimming processes
manage_vdfs = _m.Modeller().tool("inro.emme.data.function.function_transaction")
create_matrix = _m.Modeller().tool("inro.emme.data.matrix.create_matrix")
assign_extras = _m.Modeller().tool("inro.emme.traffic_assignment.set_extra_function_parameters")
assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.path_based_traffic_assignment")
skim_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.path_based_traffic_analysis")
network_calc = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")

# Define what our scenario and bank we are working in and import basic data like Volume Delay Functions
current_scenario = _m.Modeller().desktop.data_explorer().primary_scenario.core_scenario.ref
emmebank = current_scenario.emmebank
default_path = os.path.dirname(_m.Modeller().emmebank.path).replace("\\","/")
function_file = os.path.join(default_path,"Inputs/VDFs/early_am_vdfs.in").replace("\\","/")
manage_vdfs(transaction_file = function_file,throw_on_error = True)

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
assignment_spec = """{
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
            "mode": "d",
            "demand": "mfh2tl1v",
            "generalized_cost": {
                "link_costs": "@toll2",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "d",
            "demand": "mfh2tl2v",
            "generalized_cost": {
                "link_costs": "@toll2",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "d",
            "demand": "mfh2tl3v",
            "generalized_cost": {
                "link_costs": "@toll2",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "h",
            "demand": "mfh2nt1v",
            "generalized_cost": {
                "link_costs": "@toll2",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "h",
            "demand": "mfh2nt2v",
            "generalized_cost": {
                "link_costs": "@toll2",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "h",
            "demand": "mfh2nt3v",
            "generalized_cost": {
                "link_costs": "@toll2",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "m",
            "demand": "mfh3tl1v",
            "generalized_cost": {
                "link_costs": "@toll3",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "m",
            "demand": "mfh3tl2v",
            "generalized_cost": {
                "link_costs": "@toll3",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "m",
            "demand": "mfh3tl3v",
            "generalized_cost": {
                "link_costs": "@toll3",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "i",
            "demand": "mfh3nt1v",
            "generalized_cost": {
                "link_costs": "@toll3",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "i",
            "demand": "mfh3nt2v",
            "generalized_cost": {
                "link_costs": "@toll3",
                "perception_factor": 1.0
            }
        },
        {
            "mode": "i",
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

#Define Standard Generalized Cost Skimming Specification from Modeller
cost_skim_spec = """{
    "type": "PATH_BASED_TRAFFIC_ANALYSIS",
    "classes": [
        {
            "results": {
                "od_travel_times": {
                    "minimums": null,
                    "maximums": null,
                    "averages": null,
                    "shortest_paths": "mf43"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf44"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf45"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf46"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf47"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf48"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf49"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf50"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf51"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf52"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf53"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf54"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf55"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf56"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf57"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf58"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf59"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf60"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf61"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf62"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        },
        {
            "results": {
                "od_travel_times": {
                    "shortest_paths": "mf63"
                },
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": null
        }
    ],
    "path_analysis": null,
    "cutoff_analysis": null
}"""

#Define Standard Link Based Attribute (such as time or distance) Skimming Specification from Modeller
attr_skim_spec = """{
    "type": "PATH_BASED_TRAFFIC_ANALYSIS",
    "classes": [
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf64"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf65"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf66"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf67"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf68"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf69"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf70"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf71"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf72"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf73"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf74"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf75"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf76"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf77"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf78"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf79"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf80"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf81"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf82"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf83"
                }
            }
        },
        {
            "results": {
                "od_travel_times": null,
                "link_volumes": null,
                "turn_volumes": null
            },
            "analysis": {
                "results": {
                    "selected_link_volumes": null,
                    "selected_turn_volumes": null,
                    "od_values": "mf84"
                }
            }
        }
    ],
    "path_analysis": {
        "link_component": "length",
        "turn_component": null,
        "operator": "+",
        "selection_threshold": {
            "lower": 0,
            "upper": 999999
        },
        "path_to_od_composition": {
            "considered_paths": "ALL",
            "operator": "average"
        }
    },
    "cutoff_analysis": null
}"""

#Define Network Calculator from Modeller
net_calc_spec = """{
    "result": "@timau",
    "expression": "0",
    "aggregation": null,
    "selections": {
        "link": "all"
    },
    "type": "NETWORK_CALCULATION"
}"""


# Create/Initialize all the necessary Matrices in Emme
for x in range(0, 85):
    create_matrix(matrix_id=emme_matrices["classes"][x]["mat_id"],
                  matrix_name=emme_matrices["classes"][x]["mat_name"],
                  matrix_description=emme_matrices["classes"][x]["mat_desc"],
                  default_value=0,
                  overwrite=True,
                  scenario=current_scenario)

# Modify the Assignment Specifications for the Closure Criteria and Perception Factors and Run Emme Path Based Assignment
mod_assign_spec = json.loads(assignment_spec)
mod_assign_spec["stopping_criteria"]["max_iterations"]= max_iter
mod_assign_spec["stopping_criteria"]["best_relative_gap"]= b_rel_gap
for x in range(0, 21):
    mod_assign_spec["classes"][x]["generalized_cost"]["perception_factor"] = percept_factors["classes"][x]["vot"]
    mod_assign_spec["classes"][x]["demand"] = "mf"+ emme_matrices["classes"][x]["mat_name"]
assign_extras(el1 = "@rdly", el2 = "@trnv3")
assign_traffic(mod_assign_spec)

# Calculate the Pure Time Skims
mod_net_calc_spec = json.loads(net_calc_spec)
mod_net_calc_spec["result"] = "@timau"
mod_net_calc_spec["expression"] = "timau"
network_calc(mod_net_calc_spec)
mod_time_skim_spec = json.loads(attr_skim_spec)
for x in range(0, 21):
    mod_time_skim_spec["classes"][x]["analysis"]["results"]["od_values"] = emme_matrices["classes"][x+21]["mat_id"]
mod_time_skim_spec["path_analysis"]["link_component"] = "@timau"
skim_traffic(mod_time_skim_spec)

# Calculate the Cost Skims
mod_cost_skim_spec = json.loads(cost_skim_spec)
for x in range(0, 21):
    mod_cost_skim_spec["classes"][x]["results"]["od_travel_times"]["shortest_paths"] = emme_matrices["classes"][x+42]["mat_id"]
skim_traffic(mod_cost_skim_spec)

# Calculate the Distance Skims
mod_dist_skim_spec = json.loads(attr_skim_spec)
for x in range(0, 21):
    mod_dist_skim_spec["classes"][x]["analysis"]["results"]["od_values"] = emme_matrices["classes"][x+63]["mat_id"]
mod_dist_skim_spec["path_analysis"]["link_component"] = "length"
skim_traffic(mod_dist_skim_spec)

# Write out All the Skim Files to the new Binary format (currently Matrices 22 - 84).
for x in range (22, 85):
    skim_matrix_id = emmebank.matrix("mf"+`x`)
    skim_mat_name = emmebank.matrix(skim_matrix_id).name
    skim_mat_val = inro.emme.database.matrix.FullMatrix.get_data(skim_matrix_id,current_scenario)
    skim_filename = os.path.join(os.path.dirname(emmebank.path), 'Skims\\'+skim_mat_name+'.out')
    inro.emme.matrix.MatrixData.save(skim_mat_val,skim_filename)

my_desktop.close()

print 'This assignment and skim creation took', (time.time()-start_of_run)/60, 'minutes to execute.'
