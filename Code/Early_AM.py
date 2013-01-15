import array as _array
import inro.emme.desktop.app as app
import inro.modeller as _m
import inro.emme.matrix as ematrix
import inro.emme.database.matrix
import json
import numpy as np
import time
import os
import h5py

# Start an instance of Emme - for now this is using the GUI
start_of_run = time.time()
my_desktop = app.start_dedicated(False, "cth", 'C:\Users\craig\Documents\ABM\ABM.emp')
my_modeller = _m.Modeller(my_desktop)

# Emme and Modeller Tools we use for the assignment and skimming processes
manage_vdfs = _m.Modeller().tool("inro.emme.data.function.function_transaction")
create_matrix = _m.Modeller().tool("inro.emme.data.matrix.create_matrix")
assign_extras = _m.Modeller().tool("inro.emme.traffic_assignment.set_extra_function_parameters")
assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.path_based_traffic_assignment")
skim_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.path_based_traffic_analysis")
network_calc = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
create_extras = _m.Modeller().tool("inro.emme.data.extra_attribute.create_extra_attribute")
delete_extras = _m.Modeller().tool("inro.emme.data.extra_attribute.delete_extra_attribute")
import_attrs = _m.Modeller().tool("inro.emme.data.network.import_attribute_values")
import_csv = _m.Modeller().tool("inro.emme.data.matrix.import_matrix_from_csv")

# Assignment Convergence Criteria
max_iter = 50
b_rel_gap = 0.0001

# Define what our scenario and bank we are working in and import basic data like Volume Delay Functions
current_scenario = _m.Modeller().desktop.data_explorer().primary_scenario.core_scenario.ref
early_am = current_scenario.emmebank
default_path = os.path.dirname(_m.Modeller().emmebank.path).replace("\\","/")
function_file = os.path.join(default_path,"Inputs/VDFs/early_am_vdfs.in").replace("\\","/")
manage_vdfs(transaction_file = function_file,throw_on_error = True)

#Function to Define Truck Model
def truck_generation(bank, path, current_scenario):

    start_truck_generation = time.time()

    #Create the necessary vectors and read in the employment data
    
    truck_matrix_file = os.path.join(path,"Inputs/Freight/truck_matrices.txt").replace("\\","/")
    truck_matrices = json.load(open(truck_matrix_file))  
    
    #Create the Origin Input Matrices and Read the Values in from the CSV Files
    for x in range(0,len(truck_matrices['origin_inputs'])):
        truck_matrix_name = truck_matrices["origin_inputs"][x]["mat_name"]
        create_matrix(matrix_id=truck_matrices["origin_inputs"][x]["mat_id"],
                      matrix_name=truck_matrix_name,
                      matrix_description=truck_matrices["origin_inputs"][x]["mat_desc"],
                      default_value=0,
                      overwrite=True,
                      scenario=current_scenario)
        import_csv(matrix=truck_matrices["origin_inputs"][x]["mat_id"],
                   file_path=os.path.join(os.path.dirname(bank.path), 'Inputs/Freight/'+truck_matrix_name+'.csv'),
                   scenario=current_scenario)
    
    #Create the Destination Matrices and Read the Values in from the CSV Files
    for x in range(0,len(truck_matrices['destination_inputs'])):
        truck_matrix_name = truck_matrices["destination_inputs"][x]["mat_name"]
        create_matrix(matrix_id=truck_matrices["destination_inputs"][x]["mat_id"],
                      matrix_name=truck_matrix_name,
                      matrix_description=truck_matrices["destination_inputs"][x]["mat_desc"],
                      default_value=0,
                      overwrite=True,
                      scenario=current_scenario)
        import_csv(matrix=truck_matrices["destination_inputs"][x]["mat_id"],
                   file_path=os.path.join(os.path.dirname(bank.path), 'Inputs/Freight/'+truck_matrix_name+'.csv'),
                   scenario=current_scenario)

    #Create the Origin Output Matrices
    for x in range(0,len(truck_matrices['origin_outputs'])):
        truck_matrix_name = truck_matrices["origin_outputs"][x]["mat_name"]
        create_matrix(matrix_id=truck_matrices["origin_outputs"][x]["mat_id"],
                      matrix_name=truck_matrix_name,
                      matrix_description=truck_matrices["origin_outputs"][x]["mat_desc"],
                      default_value=0,
                      overwrite=True,
                      scenario=current_scenario)

    end_truck_generation = time.time()
    print 'It took', (end_truck_generation-start_truck_generation), 'seconds to generate truck trips.'

#Function to Calculate Arterial Network Delay

def arterial_delay_calc(bank, link_calculator, node_calculator):
    
    start_arterial_calc = time.time()
    
    # Create the temporary attributes needed for the signal delay calculations
    t1 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@tmpl1",extra_attribute_description="temp link calc 1",overwrite=True) 
    t2 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@tmpl2",extra_attribute_description="temp link calc 2",overwrite=True) 
    t3 = create_extras(extra_attribute_type="NODE",extra_attribute_name="@tmpn1",extra_attribute_description="temp node calc 1",overwrite=True) 
    t4 = create_extras(extra_attribute_type="NODE",extra_attribute_name="@tmpn2",extra_attribute_description="temp node calc 2",overwrite=True) 
    t5 = create_extras(extra_attribute_type="NODE",extra_attribute_name="@cycle",extra_attribute_description="Cycle Length",overwrite=True) 
    t6 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@red",extra_attribute_description="Red Time",overwrite=True) 
    
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
    print 'It took', (end_arterial_calc-start_arterial_calc), 'seconds to calculate Signal Delay.'

def extra_attr(bank):
    
    start_extra_attr = time.time()
    
    # Create the link extra attributes to store volume results
    t1 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@svtl1",extra_attribute_description="SOV Toll Class #1 Volume",overwrite=True) 
    t2 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@svtl2",extra_attribute_description="SOV Toll Class #2 Volume",overwrite=True) 
    t3 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@svtl3",extra_attribute_description="SOV Toll Class #3 Volume",overwrite=True) 
    t4 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@svnt1",extra_attribute_description="SOV No Toll Class #1 Volume",overwrite=True) 
    t5 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@svnt2",extra_attribute_description="SOV No Toll Class #2 Volume",overwrite=True) 
    t6 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@svnt3",extra_attribute_description="SOV No Toll Class #3 Volume",overwrite=True) 
    t7 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@h2tl1",extra_attribute_description="HOV 2 Toll Class #1 Volume",overwrite=True) 
    t8 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@h2tl2",extra_attribute_description="HOV 2 Toll Class #2 Volume",overwrite=True) 
    t9 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@h2tl3",extra_attribute_description="HOV 2 Toll Class #3 Volume",overwrite=True) 
    t10 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@h2nt1",extra_attribute_description="HOV 2 No Toll Class #1 Volume",overwrite=True) 
    t11 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@h2nt2",extra_attribute_description="HOV 2 No Toll Class #2 Volume",overwrite=True) 
    t12 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@h2nt3",extra_attribute_description="HOV 2 No Toll Class #3 Volume",overwrite=True) 
    t13 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@h3tl1",extra_attribute_description="HOV 3 Toll Class #1 Volume",overwrite=True) 
    t14 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@h3tl2",extra_attribute_description="HOV 3 Toll Class #2 Volume",overwrite=True) 
    t15 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@h3tl3",extra_attribute_description="HOV 3 Toll Class #3 Volume",overwrite=True) 
    t16 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@h3nt1",extra_attribute_description="HOV 3 No Toll Class #1 Volume",overwrite=True) 
    t17 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@h3nt2",extra_attribute_description="HOV 3 No Toll Class #2 Volume",overwrite=True) 
    t18 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@h3nt3",extra_attribute_description="HOV 3 No Toll Class #3 Volume",overwrite=True) 
    t19 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@lttrk",extra_attribute_description="Light Truck Volume",overwrite=True) 
    t20 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@mdtrk",extra_attribute_description="Medium Truck Volume",overwrite=True) 
    t21 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@hvtrk",extra_attribute_description="Heavy Truck Volume",overwrite=True) 
    
    # Create the link extra attributes to store the auto equivalent of bus vehicles
    t22 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@trnv3",extra_attribute_description="Transit Vehicles",overwrite=True)
    
    # Create the link extra attributes to store the toll rates in
    t23 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@toll1",extra_attribute_description="SOV Tolls",overwrite=True)  
    t24 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@toll2",extra_attribute_description="HOV 2 Tolls",overwrite=True)  
    t25 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@toll3",extra_attribute_description="HOV 3+ Tolls",overwrite=True)  
    t26 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@trkc1",extra_attribute_description="Light Truck Tolls",overwrite=True)  
    t27 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@trkc2",extra_attribute_description="Medium Truck Tolls",overwrite=True)  
    t28 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@trkc3",extra_attribute_description="Heavy Truck Tolls",overwrite=True) 
    
    # Create the link extra attribute to store the arterial delay in
    t29 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@rdly",extra_attribute_description="Intersection Delay",overwrite=True)  

    end_extra_attr = time.time()
    print 'It took', (end_extra_attr-start_extra_attr), 'seconds to generate all necessary extra attributes for the model run.'

def extra_attr_import(bank):

    start_extra_attr_import = time.time()

    current_scenario = _m.Modeller().desktop.data_explorer().primary_scenario.core_scenario.ref
    default_path = os.path.dirname(_m.Modeller().emmebank.path).replace("\\","/")
    attr_file = os.path.join(default_path,"Inputs/Tolls/early_am_tolls.in").replace("\\","/")

    import_attrs(attr_file, scenario = current_scenario,
              column_labels={0: "inode", 
                             1: "jnode", 
                             2: "@toll1", 
                             3: "@toll2", 
                             4: "@toll3", 
                             5: "@trkc1", 
                             6: "@trkc2", 
                             7: "@trkc3"},
              revert_on_error=True)

    end_extra_attr_import = time.time()

    print 'It took', (end_extra_attr_import-start_extra_attr_import), 'seconds to read in the Attributes from Text File for the model run.'
    
# Function to run our Standard Emme Path Based Traffic Assignment 
def traffic_assignment(bank, assignment_specifications):
    
    start_traffic_assignment = time.time()

    # Modify the Assignment Specifications for the Closure Criteria and Perception Factors
    mod_assign = assignment_specifications
    mod_assign["stopping_criteria"]["max_iterations"]= max_iter
    mod_assign["stopping_criteria"]["best_relative_gap"]= b_rel_gap
    
    for x in range (0, len(mod_assign["classes"])):
        mod_assign["classes"][x]["generalized_cost"]["perception_factor"] = vot_categories["classes"][x]["vot"]
        mod_assign["classes"][x]["demand"] = "mf"+ emme_matrices["Demand"][x]["mat_name"]
    
    assign_extras(el1 = "@rdly", el2 = "@trnv3")
    assign_traffic(mod_assign)

    end_traffic_assignment = time.time()
    print 'It took', (end_traffic_assignment-start_traffic_assignment)/60, 'minutes to run the assignment.'

# Function to skim network for Travel Time
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
    mod_skim = skim_specification
    for x in range (0, len(mod_skim["classes"])):
        mod_skim["classes"][x]["analysis"]["results"]["od_values"] = emme_matrices["Time Skims"][x]["mat_id"]
    mod_skim["path_analysis"]["link_component"] = "@timau"
    skim_traffic(mod_skim)

    #delete the temporary extra attributes
    delete_extras(t1)

    end_time_skim = time.time()
    print 'It took', (end_time_skim-start_time_skim)/60, 'minutes to calculate the time skims.'


# Function to skim network for Generalized Cost
def gc_skims(bank, skim_specification):
    
    start_gc_skim = time.time()

    mod_skim = skim_specification
    for x in range (0, len(mod_skim["classes"])):
        mod_skim["classes"][x]["results"]["od_travel_times"]["shortest_paths"] = emme_matrices["Cost Skims"][x]["mat_id"]
    skim_traffic(mod_skim)

    end_gc_skim = time.time()
    print 'It took', (end_gc_skim-start_gc_skim)/60, 'minutes to calculate the generalized cost skims.'

# Function to skim network for Volume
def volume_skims(bank, skim_specification):
    
    start_vol_skim = time.time()

    mod_skim = skim_specification
    for x in range (0, len(mod_skim["classes"])):
        mod_skim["classes"][x]["results"]["link_volumes"] = emme_matrices["Demand"][x]["attr_name"]
    skim_traffic(mod_skim)

    end_vol_skim = time.time()
    print 'It took', (end_vol_skim-start_vol_skim), 'seconds to calculate the generalized cost skims.'

# Function to skim network for Distance
def distance_skims(bank, skim_specification, link_calculator):

    start_distance_skim = time.time()

    # Create the temporary attributes needed for the skim calculations
    t1 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@dist",extra_attribute_description="copy of length",overwrite=True) 
    
    # Store timau (auto time on links) into an extra attribute so we can skim for it
    mod_calcs = json.loads(link_calculator)
    mod_calcs["result"] = "@dist"
    mod_calcs["expression"] = "length"
    network_calc(mod_calcs)

    # Modify Skim Specification to use @dist and run ditance skim
    mod_skim = skim_specification
    for x in range (0, len(mod_skim["classes"])):
        mod_skim["classes"][x]["analysis"]["results"]["od_values"] = emme_matrices["Distance Skims"][x]["mat_id"]
    mod_skim["path_analysis"]["link_component"] = "@dist"
    skim_traffic(mod_skim)

    #delete the temporary extra attributes
    delete_extras(t1)

    end_distance_skim = time.time()
    print 'It took', (end_distance_skim-start_distance_skim)/60, 'minutes to calculate the distance skims.'

    # Function to Export Skims using Binary Format
def export_skims(bank):

    start_export_skims = time.time()

    for x in range (1, 85):
        skim_matrix_id = bank.matrix("mf"+`x`)
        skim_mat_name = bank.matrix(skim_matrix_id).name
        skim_mat_val = inro.emme.database.matrix.FullMatrix.get_data(skim_matrix_id,current_scenario)
        skim_filename = os.path.join(os.path.dirname(bank.path), 'Skims\\'+skim_mat_name+'.out')
        inro.emme.matrix.MatrixData.save(skim_mat_val,skim_filename)

    end_export_skims = time.time()
    print 'It took', (end_export_skims-start_export_skims)/60, 'minutes to export all skims.'

def create_hdf5_emme_container(bank,my_groups):
    
    default_path = os.path.dirname(_m.Modeller().emmebank.path).replace("\\","/")

    hdf_filename = os.path.join(os.path.dirname(bank.path), 'Skims\\Early_AM.hdf5')
    my_store=h5py.File(hdf_filename, "w")

    #Create Groups for all Matrix Types in Matrix Library with teh exception of Temporary Matrices
    for x in my_groups:

        if x !="Temporary Matrices":
            my_store.create_group(x)

    return my_store
    

def emme_to_hdf5(bank,my_groups):

    start_export_hdf5 = time.time()

    #Create the HDF5 Container using group Names Matching Emme Matix Library
    my_store = create_hdf5_emme_container(bank, my_groups)

    # First Store a Dataset containing the Indicices for the Array to Matrix (any matrix will do)
    mat_id=bank.matrix("mf01")
    em_val=inro.emme.database.matrix.FullMatrix.get_data(mat_id,current_scenario)
    my_store.create_dataset("indices", data=em_val.indices)

    # Loop through the Subgroups in the HDF5 Container
    for x in my_groups:

        if x !="Temporary Matrices":
            
            # Now Loop through the Emme Trip Tables in HDF5, multiply by 100 (except demand) and convert to Integers
            for y in range (0, len(my_groups[x])):
                matrix_id= my_groups[x][y]["mat_id"]
                if x=="Demand":
                    matrix_value = np.matrix(bank.matrix(matrix_id).raw_data)
                else:
                    matrix_value = np.matrix(bank.matrix(matrix_id).raw_data)*100 
            
                my_store[x].create_dataset(bank.matrix(matrix_id).name, data=matrix_value.astype(int))

    my_store.close()

    end_export_hdf5 = time.time()

    print 'It took', (end_export_hdf5-start_export_hdf5)/60, 'minutes to export all skims to the HDF5 File.'

def hdf5_to_emme(bank,my_groups):

    start_import_hdf5 = time.time()
    default_path = os.path.dirname(_m.Modeller().emmebank.path).replace("\\","/")

    hdf_filename = os.path.join(os.path.dirname(bank.path), 'Skims/Early_AM.hdf5')

    current_scenario = _m.Modeller().desktop.data_explorer().primary_scenario.core_scenario.ref
    bank = current_scenario.emmebank

    zones=current_scenario.zone_numbers

    for x in my_groups:

        if x =="Demand":
            
            # Now Loop through the Emme Trip Tables in HDF5, multiply by 100 (except demand) and convert to Integers
            for y in range (0, len(my_groups[x])):
                matrix_id= my_groups[x][y]["mat_id"]
                if x=="Demand":
                    em_mat_id= my_groups[x][y]["mat_id"]
                    em_mat_name = my_groups[x][y]["mat_name"]
                    hdf_matrix = hdf_file[x][em_mat_name]
                    np_matrix = np.matrix(hdf_matrix)
                    np_matrix = np_matrix.astype(float) / 100
                    np_array = np.squeeze(np.asarray(np_matrix))
                    emme_matrix = ematrix.MatrixData(indices=[zones,zones],type='f')
                    emme_matrix.raw_data=[_array.array('f',row) for row in np_array]
                    bank.matrix(em_mat_id).set_data(emme_matrix,current_scenario)

    end_import_hdf5 = time.time()

    print 'It took', (end_import_hdf5-start_import_hdf5)/60, 'minutes to import matrices to Emme.'

def emme_matrix_initial(bank,my_dict):

    start_emme_initial = time.time()

    current_scenario = _m.Modeller().desktop.data_explorer().primary_scenario.core_scenario.ref

    for x in my_dict:

        for y in range (0, len(my_dict[x])):
            create_matrix(matrix_id= my_dict[x][y]["mat_id"],
                          matrix_name= my_dict[x][y]["mat_name"],
                          matrix_description= my_dict[x][y]["mat_desc"],
                          default_value=0,
                          overwrite=True,
                          scenario=current_scenario)

    end_emme_initial = time.time()

    print 'It took', (end_emme_initial-start_emme_initial), 'seconds to intialize matrices in Emme.'

# Load various dictionaries from text files
vot_file = os.path.join(default_path,"Inputs/early_am_vot.txt").replace("\\","/")
vot_categories = json.load(open(vot_file))

matrix_file = os.path.join(default_path,"Inputs/early_am_matrices.txt").replace("\\","/")
emme_matrices = json.load(open(matrix_file))  

path_assign_file = os.path.join(default_path,"Inputs/general_path_based_assignment.txt").replace("\\","/")
path_assign_spec = json.load(open(path_assign_file))

gc_skim_file = os.path.join(default_path,"Inputs/general_generalized_cost_skim.txt").replace("\\","/")
gc_skim_spec = json.load(open(gc_skim_file))

attr_skim_file = os.path.join(default_path,"Inputs/general_atrribute_based_skim.txt").replace("\\","/")
attr_skim_spec = json.load(open(attr_skim_file))

volume_skim_file = os.path.join(default_path,"Inputs/general_path_based_volume.txt").replace("\\","/")
volume_skim_spec = json.load(open(volume_skim_file))
         
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



# Run Assignments and Skims
emme_matrix_initial(early_am,emme_matrices)
hdf5_to_emme(early_am,emme_matrices)
extra_attr(early_am)
extra_attr_import(early_am)
arterial_delay_calc(early_am, link_calc_spec, node_calc_spec)
#truck_generation(early_am,default_path,current_scenario)
traffic_assignment(early_am, path_assign_spec)
time_skims(early_am,attr_skim_spec,link_calc_spec)
gc_skims(early_am,gc_skim_spec)
distance_skims(early_am,attr_skim_spec,link_calc_spec)
volume_skims(early_am,volume_skim_spec)
emme_to_hdf5(early_am,emme_matrices)

my_desktop.close()
end_of_run = time.time()

print 'The Total Time for all processes took', (end_of_run-start_of_run)/60, 'minutes to execute.'
