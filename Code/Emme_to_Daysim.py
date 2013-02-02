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
import Tkinter, tkFileDialog
import multiprocessing as mp
from multiprocessing import Pool

# Assignment Convergence Criteria
max_iter = 50
b_rel_gap = 0.0001

hdf5_subgroups=["Vehicle Class Demand","Vehicle Class Time Skims","Vehicle Class Distance Skims","Vehicle Class Toll Cost Skims"]
matrix_designation=['v','t','d','c']

#Function to Define Truck Model
def truck_generation(my_bank, my_path, my_scenario):

    start_truck_generation = time.time()

    freight_path = os.path.join(input_path, 'Freight').replace("\\","/")
    hdf_filename = os.path.join(freight_path, 'Truck_Generation.hdf5').replace("\\","/")
    my_hdf5=h5py.File(hdf_filename, "w")

    truck_matrix_file = os.path.join(freight_path,'truck_matrices.txt').replace("\\","/")
    truck_matrices = json.load(open(truck_matrix_file))

    for x in range(0,len(truck_matrices['origin_inputs'])):
        mat_name = truck_matrices["origin_inputs"][x]["mat_name"]
        csv_filename = freight_path+'/'+mat_name+'.csv'
        csv_data = np.genfromtxt(csv_filename, dtype=('f4'), comments='#', delimiter=',')
        my_hdf5.create_dataset(mat_name, data=csv_data)
    
    my_hdf5.close()

    end_truck_generation = time.time()
    print 'It took', round((end_truck_generation-start_truck_generation),2), 'seconds to generate truck trips.'

def open_emme_project(my_project):

    #Open the Time Period Specific Project passed to the function and load the Input Dictionary
    my_desktop = app.start_dedicated(True, "cth", my_project)
    my_modeller = _m.Modeller(my_desktop)

    return(my_modeller)

def load_dictionary(my_project,my_attribute):

    #Determine the Path to the input files and load them
    input_filename = os.path.join(os.path.dirname(my_project.emmebank.path),"Inputs",my_attribute+'.txt').replace("\\","/")
    my_dictionary = json.load(open(input_filename))

    return(my_dictionary)

def vdf_initial(my_project):

    start_vdf_initial = time.time()

    #Define the Emme Tools used in this function
    manage_vdfs = my_project.tool("inro.emme.data.function.function_transaction")

    #Point to input file for the VDF's and Read them in
    function_file = os.path.join(os.path.dirname(my_project.emmebank.path),"Inputs/vdfs.txt").replace("\\","/")
    manage_vdfs(transaction_file = function_file,throw_on_error = True)

    end_vdf_initial = time.time()

    print 'It took', round((end_vdf_initial-start_vdf_initial)/60,2), 'minutes to intialize Volume Delay Functions in Emme.'

def delete_matrices(my_project,matrix_type):

    start_delete_matrices = time.time()

    #Define the Emme Tools used in this function
    delete_matrix = my_project.tool("inro.emme.data.matrix.delete_matrix")

    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
    my_bank = current_scenario.emmebank

    number_of_matrices = my_bank.min_dimensions[matrix_type]

    for x in range (0,number_of_matrices):

        try:
            mat_id = my_project.emmebank.ref.matrices().next().id

        except StopIteration:
            mat_id = 'None'
        
        if mat_id !='None':
            em_mat=my_bank.matrix(mat_id)
            delete_matrix(matrix = em_mat)

    end_delete_matrices = time.time()

    print 'It took', round((end_delete_matrices-start_delete_matrices)/60,2), 'minutes to delete all '+matrix_type+' in Emme.'

def define_matrices(my_project):

    start_define_matrices = time.time()

    #Define the Emme Tools used in this function
    create_matrix = my_project.tool("inro.emme.data.matrix.create_matrix")
            
    #Load in the necessary Dictionaries
    matrix_dict = load_dictionary(my_project,"user_classes")

    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
    my_bank = current_scenario.emmebank

    # Create the Full Matrices in Emme
    matrix_designation=['v','t','c','d']
    
    for x in range (0, len(my_matrix_designation)):

        for y in range (0, len(matrix_dict["Vehicle User Class"])):
            create_matrix(matrix_id= my_bank.available_matrix_identifier("FULL"),
                          matrix_name= matrix_dict["Vehicle User Class"][y]["Name"]+matrix_designation[x],
                          matrix_description= matrix_dict["Vehicle User Class"][y]["Description"],
                          default_value=0,
                          overwrite=True,
                          scenario=current_scenario)

    end_define_matrices = time.time()

    print 'It took', round((end_define_matrices-start_define_matrices)/60,2), 'minutes to define all matrices in Emme.'

def intitial_extra_attributes(my_project):

    start_extra_attr = time.time()

    #Define the Emme Tools used in this function
    create_extras = my_project.tool("inro.emme.data.extra_attribute.create_extra_attribute")
       
    #Load in the necessary Dictionaries
    matrix_dict = load_dictionary(my_project,"user_classes")
    
    # Create the link extra attributes to store volume results
    for x in range (0, len(matrix_dict["Vehicle User Class"])):
        create_extras(extra_attribute_type="LINK",
                      extra_attribute_name= "@"+matrix_dict["Vehicle User Class"][x]["Name"],
                      extra_attribute_description= matrix_dict["Vehicle User Class"][x]["Description"],
                      overwrite=True)
    
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

    print 'It took', round((end_extra_attr-start_extra_attr)/60,2), 'minutes to generate all necessary extra attributes for the model run.'

def import_extra_attributes(my_project):

    start_extra_attr_import = time.time()

    #Define the Emme Tools used in this function
    import_attributes = my_project.tool("inro.emme.data.network.import_attribute_values")
    
    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
    attr_file = os.path.join(os.path.dirname(my_project.emmebank.path),"Inputs/tolls.txt").replace("\\","/")

    import_attributes(attr_file, scenario = current_scenario,
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

    print 'It took', round((end_extra_attr_import-start_extra_attr_import)/60,2), 'minutes to read in the Attributes from Text File for the model run.'

def arterial_delay_calc(my_project):
    
    start_arterial_calc = time.time()
    
    #Define the Emme Tools used in this function
    create_extras = my_project.tool("inro.emme.data.extra_attribute.create_extra_attribute")
    network_calc = my_project.tool("inro.emme.network_calculation.network_calculator")
    delete_extras = my_project.tool("inro.emme.data.extra_attribute.delete_extra_attribute")

    #Load in the necessary Dictionaries
    link_calculator = load_dictionary(my_project,"link_calculation")
    node_calculator = load_dictionary(my_project,"node_calculation")
       
    # Create the temporary attributes needed for the signal delay calculations
    t1 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@tmpl1",extra_attribute_description="temp link calc 1",overwrite=True) 
    t2 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@tmpl2",extra_attribute_description="temp link calc 2",overwrite=True) 
    t3 = create_extras(extra_attribute_type="NODE",extra_attribute_name="@tmpn1",extra_attribute_description="temp node calc 1",overwrite=True) 
    t4 = create_extras(extra_attribute_type="NODE",extra_attribute_name="@tmpn2",extra_attribute_description="temp node calc 2",overwrite=True) 
    t5 = create_extras(extra_attribute_type="NODE",extra_attribute_name="@cycle",extra_attribute_description="Cycle Length",overwrite=True) 
    t6 = create_extras(extra_attribute_type="LINK",extra_attribute_name="@red",extra_attribute_description="Red Time",overwrite=True) 
    
    # Set Temporary Link Attribute #1 to 1 for arterial links (ul3 .ne. 1,2) 
    # Exclude links that intersect with centroid connectors
    mod_calc = link_calculator
    mod_calc["result"] = "@tmpl1"  
    mod_calc["expression"] = "1"
    mod_calc["selections"]["link"] = "mod=a and i=4001,9999999 and j=4001,9999999 and ul3=3,99"
    network_calc(mod_calc)    

    # Set Temporary Link Attribute #2 to the minimum of lanes+2 or 5
    # for arterial links (ul3 .ne. 1,2)  - tmpl2 will equal either 3,4,5 
    # Exclude links that intersect with centroid connectors
    mod_calc = link_calculator
    mod_calc["result"] = "@tmpl2"
    mod_calc["expression"] = "(lanes+2).min.5"
    mod_calc["selections"]["link"] = "mod=a and i=4001,9999999 and j=4001,9999999 and ul3=3,99"
    network_calc(mod_calc)     

    # Set Temporary Node Attribute #1 to sum of intersecting arterial links (@tmpl1)
    mod_calc = link_calculator
    mod_calc["result"] = "@tmpn1"
    mod_calc["expression"] = "@tmpl1"
    mod_calc["aggregation"] = "+"
    network_calc(mod_calc)
    
    # Set Temporary Node Attribute #2 to sum of intersecting arterial links (@tmpl2)
    mod_calc = link_calculator
    mod_calc["result"] = "@tmpn2"
    mod_calc["expression"] = "@tmpl2"
    mod_calc["aggregation"] = "+"
    network_calc(mod_calc)       
    
    # Cycle Time at Every I-Node
    mod_calc = node_calculator
    mod_calc["result"] = "@cycle"
    mod_calc["expression"] = "(1+(@tmpn2/8)*(@tmpn1/4))*(@tmpn1.gt.2)"
    network_calc(mod_calc)  

    link_calculator = load_dictionary(my_project,"link_calculation")

    # Red Time at Every J-Node
    mod_calc = link_calculator
    mod_calc["result"] = "@red"
    mod_calc["expression"] = "1.2*@cyclej*(1-(@tmpn1j*@tmpl2)/(2*@tmpn2j))"
    mod_calc["selections"]["link"] = "mod=a and i=4001,9999999 and j=4001,9999999 and ul3=3,99 and @cyclej=0.01,999999"
    network_calc(mod_calc) 

    # Calculate intersection delay factor for every link with a cycle time exceeding zero
    mod_calc = link_calculator
    mod_calc["result"] = "@rdly"
    mod_calc["expression"] = "((@red*@red)/(2*@cyclej).max.0.2).min.1.0"
    mod_calc["selections"]["link"] = "@cyclej=0.01,999999"
    network_calc(mod_calc) 

    # Set intersection delay factor to 0 for links of 0.01 mile lenght or less
    mod_calc = link_calculator
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

    print 'It took', round((end_arterial_calc-start_arterial_calc)/60,2), 'minutes to calculate Signal Delay.'
    
def traffic_assignment(my_project):
    
    start_traffic_assignment = time.time()

    #Define the Emme Tools used in this function
    assign_extras = my_project.tool("inro.emme.traffic_assignment.set_extra_function_parameters")
    assign_traffic = my_project.tool("inro.emme.traffic_assignment.path_based_traffic_assignment")

    #Load in the necessary Dictionaries
    assignment_specification = load_dictionary(my_project,"general_path_based_assignment")
    my_user_classes= load_dictionary(my_project,"user_classes")

    # Modify the Assignment Specifications for the Closure Criteria and Perception Factors
    mod_assign = assignment_specification
    mod_assign["stopping_criteria"]["max_iterations"]= max_iter
    mod_assign["stopping_criteria"]["best_relative_gap"]= b_rel_gap
    
    for x in range (0, len(mod_assign["classes"])):
        vot = ((1/float(my_user_classes["Vehicle User Class"][x]["Value of Time"]))*60)
        mod_assign["classes"][x]["generalized_cost"]["perception_factor"] = vot
        mod_assign["classes"][x]["generalized_cost"]["link_costs"] = my_user_classes["Vehicle User Class"][x]["Toll"]
        mod_assign["classes"][x]["demand"] = "mf"+ my_user_classes["Vehicle User Class"][x]["Name"]+"v"
        mod_assign["classes"][x]["mode"] = my_user_classes["Vehicle User Class"][x]["Mode"]
    
    assign_extras(el1 = "@rdly", el2 = "@trnv3")
    assign_traffic(mod_assign)

    end_traffic_assignment = time.time()

    print 'It took', round((end_traffic_assignment-start_traffic_assignment)/60,2), 'minutes to run the assignment.'

def attribute_based_skims(my_project,my_skim_attribute):

    start_time_skim = time.time()

    #Define the Emme Tools used in this function
    create_extras = my_project.tool("inro.emme.data.extra_attribute.create_extra_attribute")
    network_calc = my_project.tool("inro.emme.network_calculation.network_calculator")
    skim_traffic = my_project.tool("inro.emme.traffic_assignment.path_based_traffic_analysis")
    delete_extras = my_project.tool("inro.emme.data.extra_attribute.delete_extra_attribute")

    #Load in the necessary Dictionaries
    skim_specification = load_dictionary(my_project,"general_attribute_based_skim")
    link_calculator = load_dictionary(my_project,"link_calculation")
    my_user_classes = load_dictionary(my_project,"user_classes")

    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
    my_bank = current_scenario.emmebank

    #Figure out what skim matrices to use based on attribute (either time or length)
    if my_skim_attribute =="Time":
        my_attribute = "timau"
        my_extra = "@timau"
        skim_type = "Time Skims"
        skim_desig = "t"
        
        #Create the Extra Attribute
        t1 = create_extras(extra_attribute_type="LINK",extra_attribute_name=my_extra,extra_attribute_description="copy of "+my_attribute,overwrite=True) 

        # Store timau (auto time on links) into an extra attribute so we can skim for it
        mod_calcs = link_calculator
        mod_calcs["result"] = my_extra
        mod_calcs["expression"] = my_attribute
        mod_calcs["selections"]["link"] = "all"
        network_calc(mod_calcs)

    if my_skim_attribute =="Distance":
        my_attribute = "length"
        my_extra = "@dist"
        skim_type = "Distance Skims"
        skim_desig = "d"
        #Create the Extra Attribute
        t1 = create_extras(extra_attribute_type="LINK",extra_attribute_name=my_extra,extra_attribute_description="copy of "+my_attribute,overwrite=True) 

        # Store Length (auto distance on links) into an extra attribute so we can skim for it
        mod_calcs = link_calculator
        mod_calcs["result"] = my_extra
        mod_calcs["expression"] = my_attribute
        mod_calcs["selections"]["link"] = "all"
        network_calc(mod_calcs)

    mod_skim = skim_specification
    
    for x in range (0, len(mod_skim["classes"])):
        
        my_extra = my_user_classes["Vehicle User Class"][x][my_skim_attribute]
        matrix_name= my_user_classes["Vehicle User Class"][x]["Name"]+skim_desig
        matrix_id = my_bank.matrix(matrix_name).id
        mod_skim["classes"][x]["analysis"]["results"]["od_values"] = matrix_id
        mod_skim["path_analysis"]["link_component"] = my_extra
        
    skim_traffic(mod_skim)

    #delete the temporary extra attributes
    delete_extras(t1)

    end_time_skim = time.time()

    print 'It took', round((end_time_skim-start_time_skim)/60,2), 'minutes to calculate the ' +skim_type+'.'

def cost_skims(my_project):
    
    start_gc_skim = time.time()

    #Define the Emme Tools used in this function
    skim_traffic = my_project.tool("inro.emme.traffic_assignment.path_based_traffic_analysis")
    
    #Load in the necessary Dictionaries
    skim_specification = load_dictionary(my_project,"general_generalized_cost_skim")
    my_user_classes = load_dictionary(my_project,"user_classes")

    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
    my_bank = current_scenario.emmebank

    mod_skim = skim_specification
    for x in range (0, len(mod_skim["classes"])):
        matrix_name= 'mf'+my_user_classes["Vehicle User Class"][x]["Name"]+'c'        
        mod_skim["classes"][x]["results"]["od_travel_times"]["shortest_paths"] = matrix_name
    skim_traffic(mod_skim)

    end_gc_skim = time.time()

    print 'It took', round((end_gc_skim-start_gc_skim)/60,2), 'minutes to calculate the generalized cost skims.'

def class_specific_volumes(my_project):
    
    start_vol_skim = time.time()

    #Define the Emme Tools used in this function
    skim_traffic = my_project.tool("inro.emme.traffic_assignment.path_based_traffic_analysis")
    
    #Load in the necessary Dictionaries
    skim_specification = load_dictionary(my_project,"general_path_based_volume")
    my_user_classes = load_dictionary(my_project,"user_classes")

    mod_skim = skim_specification
    for x in range (0, len(mod_skim["classes"])):
        mod_skim["classes"][x]["results"]["link_volumes"] = "@"+my_user_classes["Vehicle User Class"][x]["Name"] 
    skim_traffic(mod_skim)

    end_vol_skim = time.time()

    print 'It took', round((end_vol_skim-start_vol_skim),2), 'seconds to generate class specific volumes.'
 
def create_hdf5_container(my_project):
   
    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
    my_bank = current_scenario.emmebank

    #Create the HDF5 Container with subgroups (only creates it if one does not already exist using "w-")
    #Currently uses the subgroups as shown in the "hdf5_subgroups" list hardcoded below, this could be read from a control file.
    
    hdf_filename = os.path.join(os.path.dirname(my_bank.path), 'Skims/Emme_Skims.hdf5').replace("\\","/")

    #IOError will occur if file already exists with "w-", so in this case just open the current file and pass the filename out
    #IF file does not exist, opens new hdf5 file and create groups based on the subgroup list above.
    try:
        my_store=h5py.File(hdf_filename, "w-")
        for y in range (0, len(hdf5_subgroups)):
            my_store.create_group(hdf5_subgroups[y])

    except IOError:
        my_store=h5py.File(hdf_filename, "r")
     
    my_store.close()
    return hdf_filename
       
def emme_to_hdf5(my_project):

    start_export_hdf5 = time.time()
 
    #Determine the Path and Scenario File
    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
    my_bank = current_scenario.emmebank

    #Load in the necessary Dictionaries
    my_user_classes = load_dictionary(my_project,"user_classes")

    #Create the HDF5 Container if needed and open it in read/write mode using "r+"
    hdf_filename = create_hdf5_container(my_project)
    my_store=h5py.File(hdf_filename, "r+")

    # First Store a Dataset containing the Indicices for the Array to Matrix using mf01
    mat_id=my_bank.matrix("mf01")
    em_val=inro.emme.database.matrix.FullMatrix.get_data(mat_id,current_scenario)
    my_store.create_dataset("indices", data=em_val.indices)

    # Loop through the Subgroups in the HDF5 Container
    for x in range (0, len(hdf5_subgroups)):
        my_group = hdf5_subgroups[x]

        for y in range (0, len(my_user_classes["Vehicle User Class"])):
            matrix_name= my_user_classes["Vehicle User Class"][y]["Name"]+matrix_designation[x]
            matrix_id = my_bank.matrix(matrix_name).id

            if matrix_designation[x]=="v":
                matrix_value = np.matrix(my_bank.matrix(matrix_id).raw_data)

            else:
                matrix_value = np.matrix(my_bank.matrix(matrix_id).raw_data)*100

            my_store[my_group].create_dataset(matrix_name, data=matrix_value.astype(int))
        
    my_store.close()
    end_export_hdf5 = time.time()

    print 'It took', round((end_export_hdf5-start_export_hdf5)/60,2), 'minutes to export all skims to the HDF5 File.'

def hdf5_to_emme(my_project):

    start_import_hdf5 = time.time()
 
    #Determine the Path and Scenario File and Zone indicies that go with it
    current_scenario = my_project.desktop.data_explorer().primary_scenario.core_scenario.ref
    my_bank = current_scenario.emmebank
    zones=current_scenario.zone_numbers

    #Load in the necessary Dictionaries
    my_user_classes = load_dictionary(my_project,"user_classes")

    #Open the HDF5 Container in read only mode using "r"
    hdf_filename = os.path.join(os.path.dirname(my_bank.path), 'Skims/Emme_Skims.hdf5').replace("\\","/")
    hdf_file = h5py.File(hdf_filename, "r") 

    #Delimiter of a Demand Matrix in Emme - this could be part of a control file but hardcoded for now
    matrix_designation = 'v'

    for x in range (0, len(my_user_classes["Vehicle User Class"])):
        matrix_name= my_user_classes["Vehicle User Class"][x]["Name"]+matrix_designation
        matrix_id = my_bank.matrix(matrix_name).id

        try:
            hdf_matrix = hdf_file['Vehicle Class Demand'][matrix_name]
            np_matrix = np.matrix(hdf_matrix)
            np_matrix = np_matrix.astype(float)
            np_array = np.squeeze(np.asarray(np_matrix))
            emme_matrix = ematrix.MatrixData(indices=[zones,zones],type='f')
            emme_matrix.raw_data=[_array.array('f',row) for row in np_array]
            my_bank.matrix(matrix_id).set_data(emme_matrix,current_scenario)

        #If the HDF5 File does not have a matirx of that name
        except KeyError:

            print matrix_id+' does not exist in the HDF5 container - no matrix was imported' 
  
    hdf_file.close()
    end_import_hdf5 = time.time()

    print 'It took', round((end_import_hdf5-start_import_hdf5)/60,2), 'minutes to import matrices to Emme.'
         
def main():
    
    start_of_run = time.time()

    project_name = 'C:/ABM/Projects/AM1/AM1.emp'
    emme_project = open_emme_project(project_name)
    vdf_initial(emme_project)
    delete_matrices(emme_project,'full_matrices')
    define_matrices(emme_project)
    create_hdf5_container(emme_project)
    hdf5_to_emme(emme_project)
    intitial_extra_attributes(emme_project)
    import_extra_attributes(emme_project)
    arterial_delay_calc(emme_project)
    traffic_assignment(emme_project)
    attribute_based_skims(emme_project,"Time")
    attribute_based_skims(emme_project,"Distance")
    cost_skims(emme_project)
    class_specific_volumes(emme_project)
    emme_to_hdf5(emme_project)

    #pool = Pool(processes=4)
    #project_list=['C:/ABM/Projects/AM1/AM1.emp','C:/ABM/Projects/AM2/AM2.emp','C:/ABM/Projects/AM3/AM3.emp','C:/ABM/Projects/AM4/AM4.emp']
    #pool.map(intitial_extra_attributes,project_list)

    end_of_run = time.time()

    print "Emme Skim Creation and Export to HDF5 completed normally"
    print 'The Total Time for all processes took', round((end_of_run-start_of_run)/60,2), 'minutes to execute.'

if __name__ == "__main__":
    main()

