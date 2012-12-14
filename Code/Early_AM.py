import array as _array
import inro.emme.desktop.app as app
import inro.modeller as _m
import inro.emme.matrix
import inro.emme.database.matrix
import json
import numpy as _np
import time
import timeit
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
create_extras = _m.Modeller().tool("inro.emme.data.extra_attribute.create_extra_attribute")
delete_extras = _m.Modeller().tool("inro.emme.data.extra_attribute.delete_extra_attribute")

# Define what our scenario and bank we are working in and import basic data like Volume Delay Functions
current_scenario = _m.Modeller().desktop.data_explorer().primary_scenario.core_scenario.ref
early_am_bank = current_scenario.emmebank
default_path = os.path.dirname(_m.Modeller().emmebank.path).replace("\\","/")
function_file = os.path.join(default_path,"Inputs/VDFs/early_am_vdfs.in").replace("\\","/")
manage_vdfs(transaction_file = function_file,throw_on_error = True)

# Function to Calculate Arterial Network Delay
def arterial_delay_calc(bank, link_calculator, node_calculator):
    
    start_arterial_calc = time.time()
    
    # Create the temporary attributes needed for the signal delay calculations
    t1 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@tmpl1",extra_attribute_description="temp link calc 1",overwrite=True) 
    t2 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@tmpl2",extra_attribute_description="temp link calc 2",overwrite=True) 
    t3 = create_extras(extra_attribute_type="NODE",extra_attribute_name="@tmpn1",extra_attribute_description="temp node calc 1",overwrite=True) 
    t4 = create_extras(extra_attribute_type="NODE",extra_attribute_name="@tmpn2",extra_attribute_description="temp node calc 2",overwrite=True) 
    t5 = create_extras(extra_attribute_type="NODE",extra_attribute_name="@cycle",extra_attribute_description="Cycle Length",overwrite=True) 
    t6 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@red",extra_attribute_description="Red Time",overwrite=True) 
    int_delay = create_extras(extra_attribute_type="LINK",extra_attribute_name="@rdly",extra_attribute_description="Intersection Delay",overwrite=True) 
    
    # Set Temporary Link Attribute #1 to 1 for arterial links (ul3 .ne. 1,2) 
    # Exclude links that intersect with centroid connectors
    mod_calc = json.loads(link_calculator)
    mod_calc["result"] = "@tmpl1"  
    mod_calc["expression"] = "1"
    mod_calc["selections"]["link"] = "mod=a and i=4001,9999999 and j=4001,9999999 and ul3=3,99"
    network_calc(mod_calc)    

    # Set Temporary Link Attribute #2 to the minimum of lanes+2 or 5
    # for arterial links (ul3 .ne. 1,2)  - tmpl2 will equal either 3,4,5 
    # Exclude links that intersect with centroid connectors
    mod_calc = json.loads(link_calculator)
    mod_calc["result"] = "@tmpl2"
    mod_calc["expression"] = "(lanes+2).min.5"
    mod_calc["selections"]["link"] = "mod=a and i=4001,9999999 and j=4001,9999999 and ul3=3,99"
    network_calc(mod_calc)     

    # Set Temporary Node Attribute #1 to sum of intersecting arterial links (@tmpl1)
    mod_calc = json.loads(link_calculator)
    mod_calc["result"] = "@tmpn1"
    mod_calc["expression"] = "@tmpl1"
    mod_calc["aggregation"] = "+"
    network_calc(mod_calc)
    
    # Set Temporary Node Attribute #2 to sum of intersecting arterial links (@tmpl2)
    mod_calc = json.loads(link_calculator)
    mod_calc["result"] = "@tmpn2"
    mod_calc["expression"] = "@tmpl2"
    mod_calc["aggregation"] = "+"
    network_calc(mod_calc)       
    
    # Cycle Time at Every I-Node
    mod_calc = json.loads(node_calculator)
    mod_calc["result"] = "@cycle"
    mod_calc["expression"] = "(1+(@tmpn2/8)*(@tmpn1/4))*(@tmpn1.gt.2)"
    network_calc(mod_calc)  

    # Red Time at Every J-Node
    mod_calc = json.loads(link_calculator)
    mod_calc["result"] = "@red"
    mod_calc["expression"] = "1.2*@cyclej*(1-(@tmpn1j*@tmpl2)/(2*@tmpn2j))"
    mod_calc["selections"]["link"] = "mod=a and i=4001,9999999 and j=4001,9999999 and ul3=3,99 and @cyclej=0.01,999999"
    network_calc(mod_calc) 

    # Calculate intersection delay factor for every link with a cycle time exceeding zero
    mod_calc = json.loads(link_calculator)
    mod_calc["result"] = "@rdly"
    mod_calc["expression"] = "((@red*@red)/(2*@cyclej).max.0.2).min.1.0"
    mod_calc["selections"]["link"] = "@cyclej=0.01,999999"
    network_calc(mod_calc) 

    # Set intersection delay factor to 0 for links of 0.01 mile lenght or less
    mod_calc = json.loads(link_calculator)
    mod_calc["result"] = "@rdly"
    mod_calc["expression"] = "0"
    mod_calc["selections"]["link"] = "length=0,0.01"
    network_calc(mod_calc)

    #delete the temporary extra attributes
    delete_extras(t1)
    delete_extras(t2)
    delete_extras(t3)
    delete_extras(t4)
    delete_extras(t5)
    delete_extras(t6)
    
    end_arterial_calc = time.time()
    print 'It took', (end_arterial_calc-start_arterial_calc)/60, 'minutes to calculate Signal Delay.'

# Function to run our Standard Emme Path Based Traffic Assignment using 21 Vehicle Classes
def traffic_assignment(bank, assignment_specifications):
    
    start_traffic_assignment = time.time()

    # Modify the Assignment Specifications for the Closure Criteria and Perception Factors
    mod_assign = json.loads(assignment_specifications)
    mod_assign["stopping_criteria"]["max_iterations"]= max_iter
    mod_assign["stopping_criteria"]["best_relative_gap"]= b_rel_gap
    
    for x in range(0, 21):
        mod_assign["classes"][x]["generalized_cost"]["perception_factor"] = percept_factors["classes"][x]["vot"]
        mod_assign["classes"][x]["demand"] = "mf"+ emme_matrices["classes"][x]["mat_name"]
    
    assign_extras(el1 = "@rdly", el2 = "@trnv3")
    assign_traffic(mod_assign)

    end_traffic_assignment = time.time()
    print 'It took', (end_traffic_assignment-start_traffic_assignment)/60, 'minutes to run the assignment.'

# Function to skim network for travel time for 21 vehicle classes
def time_skims(bank, skim_specification, link_calculator):

    start_time_skim = time.time()

    # Create the temporary attributes needed for the skim calculations
    t1 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@timau",extra_attribute_description="copy of auto time",overwrite=True) 
    
    # Store timau (auto time on links) into an extra attribute so we can skim for it
    mod_calcs = json.loads(link_calculator)
    mod_calcs["result"] = "@timau"
    mod_calcs["expression"] = "timau"
    network_calc(mod_calcs)

    # Modify Skim Specification to use @timau and run pure time skim
    mod_skim = json.loads(skim_specification)
    for x in range(0, 21):
        mod_skim["classes"][x]["analysis"]["results"]["od_values"] = emme_matrices["classes"][x+21]["mat_id"]
    mod_skim["path_analysis"]["link_component"] = "@timau"
    skim_traffic(mod_skim)

    #delete the temporary extra attributes
    delete_extras(t1)

    end_time_skim = time.time()
    print 'It took', (end_time_skim-start_time_skim)/60, 'minutes to calculate the time skims.'


# Function to skim network for generalized cost for 21 vehicle classes
def gc_skims(bank, skim_specification):
    
    start_gc_skim = time.time()

    mod_skim = json.loads(skim_specification)
    for x in range(0, 21):
        mod_skim["classes"][x]["results"]["od_travel_times"]["shortest_paths"] = emme_matrices["classes"][x+42]["mat_id"]
    skim_traffic(mod_skim)

    end_gc_skim = time.time()
    print 'It took', (end_gc_skim-start_gc_skim)/60, 'minutes to calculate the generalized cost skims.'

# Function to skim network for distance for 21 vehicle classes
def distance_skims(bank, skim_specification, link_calculator):

    start_distance_skim = time.time()

    # Create the temporary attributes needed for the skim calculations
    t1 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@dist",extra_attribute_description="copy of length",overwrite=True) 
    
    # Store timau (auto time on links) into an extra attribute so we can skim for it
    mod_calcs = json.loads(link_calculator)
    mod_calcs["result"] = "@dist"
    mod_calcs["expression"] = "length"
    network_calc(mod_calcs)

    # Modify Skim Specification to use @timau and run pure time skim
    mod_skim = json.loads(skim_specification)
    for x in range(0, 21):
        mod_skim["classes"][x]["analysis"]["results"]["od_values"] = emme_matrices["classes"][x+63]["mat_id"]
    mod_skim["path_analysis"]["link_component"] = "@dist"
    skim_traffic(mod_skim)

    #delete the temporary extra attributes
    delete_extras(t1)

    end_distance_skim = time.time()
    print 'It took', (end_distance_skim-start_distance_skim)/60, 'minutes to calculate the distance skims.'

    # Function to Export Skims
def export_skims(bank):

    start_export_skims = time.time()

    for x in range (22, 85):
        skim_matrix_id = bank.matrix("mf"+`x`)
        skim_mat_name = bank.matrix(skim_matrix_id).name
        skim_mat_val = inro.emme.database.matrix.FullMatrix.get_data(skim_matrix_id,current_scenario)
        skim_filename = os.path.join(os.path.dirname(bank.path), 'Skims\\'+skim_mat_name+'.out')
        inro.emme.matrix.MatrixData.save(skim_mat_val,skim_filename)

    end_export_skims = time.time()
    print 'It took', (end_export_skims-start_export_skims)/60, 'minutes to export all skims.'

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
gc_skim_spec = """{
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
link_calc_spec = """{
    "result": "@timau",
    "expression": "0",
    "aggregation": null,
    "selections": {
        "link": "all"
    },
    "type": "NETWORK_CALCULATION"
}"""

node_calc_spec = """{
    "result": "@timau",
    "expression": "0",
    "aggregation": null,
    "selections": {
        "node": "all"
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

# Run Assignments and Skims
arterial_delay_calc(early_am_bank, link_calc_spec, node_calc_spec)
traffic_assignment(early_am_bank, assign_spec)
time_skims(early_am_bank,attr_skim_spec,link_calc_spec)
gc_skims(early_am_bank,gc_skim_spec)
distance_skims(early_am_bank,attr_skim_spec,link_calc_spec)
export_skims(early_am_bank)

my_desktop.close()
end_of_run = time.time()

print 'The Total Time for all processes took', (end_of_run-start_of_run)/60, 'minutes to execute.'
