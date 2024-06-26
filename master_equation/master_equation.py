#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 17 11:56:22 2018

@author: carly
"""
import numpy as np
import copy
import pandas as pd
import re

class Master_Equation(object):
    def __init__(self,T_P_min_max_dict = {}):
        self.matrix = None
        self.T_P_min_max_dict = T_P_min_max_dict
        


    def multiply_by_sensitivites(self,array1,array_of_sensitivities,pressure_and_temp_array,reaction):
        
        # print(pressure_and_temp_array)
        
        sensitivity_multiplied_array = np.zeros((array_of_sensitivities.shape[0],array_of_sensitivities.shape[1],pressure_and_temp_array.shape[0]))
        tuple_list = []
        for ix,iy in np.ndindex(array_of_sensitivities.shape):
            tuple_list.append((ix,iy))
        counter = 0    
        for sensitivity in np.nditer(array_of_sensitivities,order='C'):
            #i,j= np.where(array_of_sensitivities == sensitivity)
            i = tuple_list[counter][0]
            j= tuple_list[counter][1]
            temp_coef = []
            pres_coef = []
            counter +=1
            
            for p,value in enumerate(pressure_and_temp_array['temperature']):
                
                #should we have default T_min and T_max that can be passed in ?
                t_coef = self.chebyshev_specific_poly(i,self.calc_reduced_T(value,reaction,self.T_P_min_max_dict))
                temp_coef.append(t_coef)
                p_coef = self.chebyshev_specific_poly(j,self.calc_reduced_P(np.array(pressure_and_temp_array['pressure'])[p],reaction,self.T_P_min_max_dict))
                pres_coef.append(p_coef)
                
                    
            temp_coef = np.array(temp_coef)
            temp_coef = temp_coef.reshape((temp_coef.shape[0],1))
            pres_coef = np.array(pres_coef)
            pres_coef = pres_coef.reshape((pres_coef.shape[0],1))
            
            mapped_array = np.multiply(pres_coef,temp_coef)
            mapped_array = np.multiply(mapped_array,array1) 
            #stub
            mapped_array = mapped_array*(1)
            #stub
            sensitivity_multiplied_array[i,j,:] = mapped_array.flatten()
        return sensitivity_multiplied_array
    

    
    def array_reshape(self,three_d_array):
        temp_array = []
        for row in range(three_d_array.shape[0]):
            for column in range(three_d_array.shape[1]):
                alpha = three_d_array[row,column,:]
                alpha = alpha.reshape((alpha.shape[0],1))
                temp_array.append(alpha)
        temp_array = np.hstack((temp_array))
        return temp_array

    
    def chebyshev_specific_poly(self,order_needed,value):
        #this function starts indexing at 1 
        if order_needed ==0:
            x=1
            y=0
        else:
            order_needed  = order_needed + 1 
            coef = [1 for value in range(order_needed)]
            
            x = np.polynomial.chebyshev.chebval(value,
                                           coef,
                                           tensor = False)
            
            y = np.polynomial.chebyshev.chebval(value,
                                           coef[0:-1],
                                           tensor = False)  
        return x-y
    #changed this to force it ot be a flaot 
    def calc_reduced_T(self,T,reaction,T_P_min_max_dict):
        #print(self.T_P_min_max_dict)
        T_min = T_P_min_max_dict[reaction]['T_min']
        T_max = T_P_min_max_dict[reaction]['T_max']
        
       
        numerator = (2*(float(T)**-1))-((float(T_min))**-1) - ((float(T_max))**-1)
        denominator = ((float(T_max))**-1) - ((float(T_min))**-1)
        T_reduced = np.divide(numerator,denominator)        
       

        return T_reduced
        
    def calc_reduced_P(self,P,reaction,T_P_min_max_dict):
        
        P_min = T_P_min_max_dict[reaction]['P_min']
        P_max = T_P_min_max_dict[reaction]['P_max']

        
        numerator = 2*np.log10(P) - np.log10(P_min) - np.log10(P_max)
        denominator = np.log10(P_max) - np.log10(P_min)
        P_reduced = np.divide(numerator,denominator)
        return P_reduced


    
    
    def map_to_alpha(self,sensitivty_dict:dict,
                 exp_dict_list:list,
                 parsed_yaml_file_list,
                 master_equation_reactions:list):
        
        
        #flatten master euqation reactions
        flatten = lambda *n: (e for a in n
            for e in (flatten(*a) if isinstance(a, (tuple, list)) else (a,)))  
        #flatten master index 
        master_equation_reactions = list(flatten(master_equation_reactions))

        
    
        nested_list = []
        def slicing_out_reactions(reaction_string,array):
            reactions_in_cti_file = exp_dict_list[0]['simulation'].processor.solution.reaction_equations()
            index_of_reaction_in_cti = reactions_in_cti_file.index(reaction_string)
            column_of_array = array[:,index_of_reaction_in_cti]
            column_of_array = column_of_array.reshape((column_of_array.shape[0],
                                                                  1))  
            return column_of_array
        mapped_to_alpha_full_simulation = []
        for i, exp in enumerate(exp_dict_list):
            # print(exp['simulation'].timeHistories)
            simulation = []
            single_experiment = []
            #print(parsed_yaml_file_list[i]['moleFractionObservables'][0],parsed_yaml_file_list[i]['concentrationObservables'][0],parsed_yaml_file_list[i]['ignitionDelayObservables'])
            if parsed_yaml_file_list[i]['moleFractionObservables'][0] != None or parsed_yaml_file_list[i]['concentrationObservables'][0] != None or parsed_yaml_file_list[i]['ignitionDelayObservables'][0] !=None:
                As = exp['ksens']['A']
                for xx,observable in enumerate(As):
                    temp = []
                    observable_list = []
                    for reaction in master_equation_reactions:
                        column = slicing_out_reactions(reaction,observable)
                        if re.match('[Ss]hock[- ][Tt]ube',exp['simulation_type']) and re.match('[Ss]pecies[- ][Pp]rofile',exp['experiment_type']):
                            single_reaction_array = self.array_reshape(self.multiply_by_sensitivites(column,sensitivty_dict[reaction][0],exp['simulation'].pressureAndTemperatureToExperiment[xx],reaction))
                        elif re.match('[Ss]hock[- ][Tt]ube',exp['simulation_type']) and re.match('[Ii]gnition[- ][Dd]elay',exp['experiment_type']):
                            single_reaction_array = self.array_reshape(self.multiply_by_sensitivites(column,sensitivty_dict[reaction][0],exp['simulation'].timeHistories[0],reaction))
                        elif re.match('[Ff]low[- ][Rr]eactor',exp['simulation_type']) and re.match('[Ss]pecies[- ][Pp]rofile',exp['experiment_type']):
                            single_reaction_array = self.array_reshape(self.multiply_by_sensitivites(column,sensitivty_dict[reaction][0],exp['simulation'].timeHistories[0],reaction))
                        elif re.match('[Jj][Ss][Rr]',exp['simulation_type']) and re.match('[Ss]pecies[- ][Pp]rofile',exp['experiment_type']):
                            single_reaction_array = self.array_reshape(self.multiply_by_sensitivites(column,sensitivty_dict[reaction][0],exp['simulation'].timeHistories[0],reaction))                            

                        temp.append(single_reaction_array)
                        observable_list.append(single_reaction_array)
                        
                    simulation.append(observable_list)
                   
                    single_experiment.append(np.hstack((temp)))
                    
                 
            if 'absorbance_observables' in list(exp.keys()):
                wavelengths = parsed_yaml_file_list[i]['absorbanceCsvWavelengths']
                for k,wl in enumerate(wavelengths):
                    temp = []
                    observable_list = []
                    for reaction in master_equation_reactions:
                        column = slicing_out_reactions(reaction,exp['absorbance_ksens'][wl][0])
                        single_reaction_array = self.array_reshape(self.multiply_by_sensitivites(column,sensitivty_dict[reaction][0],exp['time_history_interpolated_against_abs'][wl],reaction))
                        temp.append(single_reaction_array)
                        observable_list.append(single_reaction_array)
                        
                    single_experiment.append(np.hstack((temp)))
                    simulation.append(observable_list)
                   
                       
            

            nested_list.append(simulation)        
            mapped_to_alpha_full_simulation.append(np.vstack((single_experiment)))
        
        
        
       
        
            
        return mapped_to_alpha_full_simulation,nested_list
    

            
            
    def  map_parameters_to_s_matrix(self,mapped_to_alpha_full_simulation,
                                   sensitivity_dict:dict,
                                   master_equation_reactions:list):
        
        
        #flatten master euqation reactions
        flatten = lambda *n: (e for a in n
            for e in (flatten(*a) if isinstance(a, (tuple, list)) else (a,)))  
        #flatten master index 
        master_equation_reactions = list(flatten(master_equation_reactions))


        
        broken_up_by_reaction = {}
        tottal_array  = np.vstack((mapped_to_alpha_full_simulation))
        list_of_number_of_alphas = []
        for reaction in master_equation_reactions:
            
            list_of_number_of_alphas.append(sensitivity_dict[reaction][0].shape[0] * sensitivity_dict[reaction][0].shape[1] )
        
        
        start = 0        
        for i,reaction in enumerate(master_equation_reactions):

            stop = start + list_of_number_of_alphas[i]
            broken_up_by_reaction[reaction] = tottal_array[:,start:stop]  
            start = stop
        
        
        original_sens_dict = copy.deepcopy(sensitivity_dict)     
        new_sens_dict = {}

        for reaction in master_equation_reactions:
            by_reaction =[]
            for parameter_array in original_sens_dict[reaction]:
                temp =[]
                for sensitivity in np.nditer(parameter_array,order='C'):
                    sensitivity = float(sensitivity)
                    temp.append(sensitivity)
                by_reaction.append(temp)
            new_sens_dict[reaction] = by_reaction       
        
        
        mapped_dict = {}     
        #start looking here 
        #flatten list and then operate on the final 
        for reaction in master_equation_reactions:
            number_of_MP_nested_list = [[] for x in range(len(sensitivity_dict[reaction]))]
            for i,sens_list in enumerate(new_sens_dict[reaction]):
                for alpha_mapped_column in range(broken_up_by_reaction[reaction].shape[1]): 
                    column_alpha = broken_up_by_reaction[reaction][:,alpha_mapped_column]
                    temp_array = column_alpha*sens_list[alpha_mapped_column]
                    temp_array = temp_array.reshape((temp_array.shape[0],1))
                    number_of_MP_nested_list[i].append(temp_array)
            mapped_dict[reaction] = number_of_MP_nested_list
        
        tester = copy.deepcopy(mapped_dict)
        for reaction in master_equation_reactions:
            for i,MP in enumerate(mapped_dict[reaction]):
                lst = np.hstack((MP))
                mapped_dict[reaction][i] = lst
                
        for reaction in master_equation_reactions:
            for i,MP in enumerate(mapped_dict[reaction]):
                temp_sum = np.sum(MP,axis=1)
                temp_sum = temp_sum.reshape((temp_sum.shape[0],1))
                mapped_dict[reaction][i] = temp_sum                        
        
    
        for reaction in master_equation_reactions:
            mapped_dict[reaction] = np.hstack((mapped_dict[reaction]))    
        
        
        temp_list_2 = []
        for reaction in master_equation_reactions:
            temp_list_2.append(mapped_dict[reaction])
        
       
        
        S_matrix_mapped_MP = np.hstack((temp_list_2))
        #print(S_matrix_mapped_MP.shape, 'THIS IS THE SHAPE OF THING GOING INTO THE S MATRIX')
        return S_matrix_mapped_MP, new_sens_dict,broken_up_by_reaction,tottal_array,tester
    
    

    def combine_multiple_channels(self,S_matrix_mapped_MP,
                                  master_equation_sensitivity_dict:dict,
                                  master_equation_reactions_list:list):
        
        #first check what parts of the matrix should be combined 
        counter = 0
        previous = 0
        new_matrix_list = []
        for reaction in master_equation_reactions_list:
            if type(reaction) ==str:
                number_of_parameters = len(master_equation_sensitivity_dict[reaction])
                counter = counter + number_of_parameters
                new_matrix_list.append(S_matrix_mapped_MP[:,previous:counter])
                #print(reaction, np.shape(S_matrix_mapped_MP[:,previous:counter]))
            elif type(reaction) == tuple:
                ttl=0
                for secondary_reaction in reaction:
                    number_of_parameters = len(master_equation_sensitivity_dict[secondary_reaction])
                    ttl = ttl + number_of_parameters
                counter = counter + ttl
                full_matrix = S_matrix_mapped_MP[:,previous:counter]
                list_of_splits = np.hsplit(full_matrix,len(reaction))
                summation = sum(list_of_splits)
                new_matrix_list.append(summation)
            previous = counter
                    
        
        new_S_matrix = np.hstack((new_matrix_list))
        return new_S_matrix
    
    def surrogate_model_molecular_parameters_chevy(self,master_equation_sensitivity_dict:dict,
                                                   master_equation_sensitivites_new:dict,
                                                   master_equation_reactions:list,
                                                   delta_x_molecular_params_by_reaction_dict,
                                                   exp_dict_list):
        
        
        flatten = lambda *n: (e for a in n
            for e in (flatten(*a) if isinstance(a, (tuple, list)) else (a,)))  
        #flatten master index 
        master_equation_reactions_flattened = list(flatten(master_equation_reactions))
        
        #this function is not working correctly
        #print(delta_x_molecular_params_by_reaction_dict)
        reactions_in_cti_file = exp_dict_list[0]['simulation'].processor.solution.reaction_equations()
        number_of_reactions = len(reactions_in_cti_file)
        
        #this is where would need to implement tuple
        temp_dict = {}
        for i,reaction in enumerate(master_equation_reactions):                
            temp_array=[]
            if type(reaction) == str:
                for j,sensativity_array in enumerate(master_equation_sensitivity_dict[reaction]):
                    delta_x_MP = delta_x_molecular_params_by_reaction_dict[reaction][j]
                    temp_array.append(sensativity_array*delta_x_MP)
                    
                summation = sum(temp_array)
                temp_dict[reaction] = summation
            
            elif type(reaction) == tuple:
                for secondary_reaction in reaction:
                    temp_array=[]
                    for j,sensativity_array in enumerate(master_equation_sensitivity_dict[secondary_reaction]):
                        delta_x_MP = delta_x_molecular_params_by_reaction_dict[reaction][j]
                        temp_array.append(sensativity_array*delta_x_MP)
                
                    summation = sum(temp_array)
                    temp_dict[secondary_reaction] = summation                        
                    
                
            #print(temp_array)
            #summation = sum(temp_array)
            #if reaction=='H2O2 + OH <=> H2O + HO2':
                #print(summation)
            #temp_dict[reaction] = summation
            
        Keys =[]
        for x in np.arange(number_of_reactions-len(master_equation_reactions_flattened),number_of_reactions):
            Keys.append('r'+str(x))
            #is this in the correct order?
            #is this unit correct
        update_array_list_without_keys = []
        for reaction in master_equation_reactions_flattened:
            update_array_list_without_keys.append(temp_dict[reaction])
        
        MP = dict(zip(Keys,update_array_list_without_keys))                
        #print(MP)
        return MP     