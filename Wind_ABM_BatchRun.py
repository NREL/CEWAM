# -*- coding:utf-8 -*-
"""
Created on April 17 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

BatchRun - Circular Economy Wind Agent-based Model (CEWAM)
This module run batch runs of the model according to user inputs.
"""


from Wind_ABM_Model import *
from mesa.batchrunner import BatchRunnerMP
from SALib.sample import saltelli
from copy import deepcopy
import time


if __name__ == '__main__':
    t0 = time.time()
    all_fixed_params = {
        "seed": None,
        "batch_run": True,
        "calibration": 1,
        "calibration_2": 1,
        "calibration_3": 1,
        "calibration_4": 1,
        "calibration_5": 1,
        "calibration_6": 1,
        "calibration_7": 1,
        "calibration_8": 1,
        "calibration_9": 1,
        "manufacturers": {"wind_blade": 5, "plastics_n_boards": 100,
                          "cement": 97},
        "developers": {'lifetime_extension': 10},
        "recyclers": {"dissolution": 6, "pyrolysis": 2,
                      "mechanical_recycling": 3, "cement_co_processing": 1},
        "small_world_networks": {
            "wind_plant_owners": {"node_degree": 15, "rewiring_prob": 0.1},
            "developers": {"node_degree": 5, "rewiring_prob": 0.1},
            "recyclers": {"node_degree": 5, "rewiring_prob": 0.1},
            "manufacturers": {"node_degree": 15, "rewiring_prob": 0.1},
            "original_equipment_manufacturer": {"node_degree": 4,
                                                "rewiring_prob": 1},
            "landfills": {"node_degree": 5, "rewiring_prob": 0.1},
            "regulators": {"node_degree": 5, "rewiring_prob": 0.1}},
        "external_files": {
            "state_distances": "state_centroid_distances.csv",
            "detailed_distances": "transport_distances.csv",
            "uswtdb": "uswtdb_v3_3_20210114.csv", "projections":
                "nrel_mid_case_projections.csv",
            "wbj_database": "WBJ Landfills 2020.csv"},
        "average_lifetime": {'thermoset': [20.0, 20.1],
                             'thermoplastic': [20.0, 20.01]},
        "weibull_shape_factor": 2.2,
        "blade_size_to_mass_model": {'coefficient': 0.0026, 'power': 2.1447},
        "cap_to_diameter_model": {'coefficient': 57, 'power': 0.44},
        "temporal_scope": {'pre_simulation': 2000, 'simulation_start': 2020,
                           'simulation_end': 2051},
        "blades_per_rotor": 3,
        "eol_pathways": {"lifetime_extension": True, "dissolution": False,
                         "pyrolysis": True, "mechanical_recycling": True,
                         "cement_co_processing": True, "landfill": True},
        "eol_pathways_dist_init": {
            "lifetime_extension": 0.005, "dissolution": 0.0,
            "pyrolysis": 0.005, "mechanical_recycling": 0.005,
            "cement_co_processing": 0.005, "landfill": 0.98},
        "tpb_eol_coeff": {'w_bi': 0.19, 'w_a': 0.29, 'w_sn': 0.19,
                          'w_pbc': -0.26, 'w_dpbc': -0.29, 'w_p': 0.04,
                          'w_b': -0.21},
        "attitude_eol_parameters": {"mean": 0.8, 'standard_deviation': 0.3,
                                    'min': 0, 'max': 1},
        "choices_circularity": {
            "lifetime_extension": True, "dissolution": True, "pyrolysis": True,
            "mechanical_recycling": True, "cement_co_processing": True,
            "landfill": False, "thermoset": False, "thermoplastic": True},
        "decommissioning_cost": [1300, 33000],
        "lifetime_extension_costs": [600, 6000],
        "rec_processes_costs": {
            "dissolution": [658, 659], "pyrolysis": [285, 629],
            "mechanical_recycling": [110, 310],
            "cement_co_processing": [99, 132]},
        "transport_shreds": {'shredding_costs': [99, 132],
                             'transport_cost_shreds': [0.0314, 0.0820]},
        "transport_segments": {
            'cutting_costs': 27.56, 'transport_cost_segments': 8.7,
            'length_segment': 30, 'segment_per_truck': 2},
        "transport_repair": 1.57,
        "eol_pathways_transport_mode": {
            "lifetime_extension": 'transport_repair',
            "dissolution": 'transport_segments',
            "pyrolysis": 'transport_segments',
            "mechanical_recycling": 'transport_segments',
            "cement_co_processing": 'transport_segments',
            "landfill": 'transport_segments'},
        "lifetime_extension_revenues": [124, 1.7E6],
        "rec_processes_revenues": {
            "dissolution": [658, 659], "pyrolysis": [332, 500],
            "mechanical_recycling": [145, 292],
            "cement_co_processing": [0, 1E-6]},
        "lifetime_extension_years": [5, 15],
        "le_feasibility": 0.55,
        "early_failure_share": 0.03,
        "blade_types": {"thermoset": True, "thermoplastic": False},
        "blade_types_dist_init": {"thermoset": 0.996, "thermoplastic": 0.004},
        "tpb_bt_coeff": {'w_bi': 0.38, 'w_a': 0.30, 'w_sn': 0.21,
                         'w_pbc': -0.32, 'w_dpbc': -0.32, 'w_p': 0.00,
                         'w_b': 0.00},
        "attitude_bt_parameters": {'mean': 0.8, 'standard_deviation': 0.1,
                                   'min': 0, 'max': 1},
        "blade_costs": {"thermoset": [50E3, 500E3],
                        "thermoplastic_rate": [0.92, 1.04]},
        "recyclers_states": {
            "dissolution": [
                "South Carolina", "Tennessee", "Iowa", "Texas",
                "Florida", "Missouri"],
            "pyrolysis": ["South Carolina", "Tennessee"],
            "mechanical_recycling": ["Iowa", "Texas", "Florida"],
            "cement_co_processing": ["Missouri"]},
        "learning_parameter": {
            "dissolution": [-0.21, -0.2], "pyrolysis": [-0.21, -0.2],
            "mechanical_recycling": [-0.21, -0.2],
            "cement_co_processing": [-0.21, -0.2]},
        "blade_mass_fractions": {"steel": 0.05, "plastic": 0.09, "resin": 0.30,
                                 "glass_fiber": 0.56},
        "rec_recovery_fractions": {
            "dissolution": {"steel": 1, "plastic": 1, "resin": 0.9,
                            "glass_fiber": 0.5},
            "pyrolysis": {"steel": 1, "plastic": 0, "resin": 0,
                          "glass_fiber": 0.5},
            "mechanical_recycling": {"steel": 1, "plastic": 1, "resin": 1,
                                     "glass_fiber": 1},
            "cement_co_processing": {"steel": 1, "plastic": 0, "resin": 0,
                                     "glass_fiber": 1}},
        "bt_man_dist_init": {"thermoset": 0.996, "thermoplastic": 0.004},
        "attitude_bt_man_parameters": {
            'mean': 0.9, 'standard_deviation': 0.1, 'min': 0, 'max': 1},
        "tpb_bt_man_coeff": {'w_bi': 1.00, 'w_a': 0.15, 'w_sn': 0.125,
                             'w_pbc': -0.24, 'w_dpbc': 0.00,
                             'w_p': 0.00, 'w_b': 0.00},
        "lag_time_tp_blade_dev": 5,
        "tp_production_share": 1,
        "manufacturing_waste_ratio": {
            "steel": [0.12, 0.3], "plastic": [0.12, 0.3],
            "resin": [0.12, 0.3], "glass_fiber": [0.12, 0.3]},
        "oem_states": {
            "wind_blade": ["Colorado", "North Dakota", "South Dakota", "Iowa",
                           "Iowa"]},
        "man_waste_dist_init": {
            "dissolution": 0.0, "mechanical_recycling": 0.02,
            "landfill": 0.98},
        "tpb_man_waste_coeff": {
            'w_bi': 0.19, 'w_a': 0.29, 'w_sn': 0.19, 'w_pbc': -0.26,
            'w_dpbc': -0.29, 'w_p': 0.00, 'w_b': 0.00},
        "attitude_man_waste_parameters": {
            "mean": 0.5, 'standard_deviation': 0.1, 'min': 0, 'max': 1},
        "recycling_init_cap": {"dissolution": 1, "pyrolysis": 33100,
                               "mechanical_recycling": 54200,
                               "cement_co_processing": 54200},
        "conversion_factors": {'metric_short_ton': 1.10231},
        "landfill_closure_threshold": [0.9, 1],
        "waste_volume_model": {
            'waste_volume': False, 'transport_segments': 0.034,
            'transport_shreds': 0.33, 'transport_repair': np.nan,
            'landfill_density': 1.009, 'cdw_density': 1.009,
            'land_cost_conv': 0.47},
        "reg_landfill_threshold": [0.9, 1],
        "atb_land_wind": {'start': {'year': 2018, 't_cap': 2.4, 't_rd': 116},
                          'end': {'year': 2030, 't_cap': 5.5, 't_rd': 175}},
        "regulation_scenario": {
            'remaining_cap_based': False, 'empirically_based':
            {'regulation': True, 'lag_time': [18, 32],
             'regulation_freq': {
                 'ban_shreds': 0.23, 'ban_whole_only': 0.25,
                 'no_ban': 0.52}}},
        "recycler_margin": {
            "dissolution": [0.05, 0.25], "pyrolysis": [0.05, 0.25],
            "mechanical_recycling": [0.05, 0.25],
            "cement_co_processing": [0.05, 0.25]},
        "recyclers_names": {
            "dissolution": {
                "South Carolina": 'Carbon Conversions - dissolution',
                "Tennessee": 'Carbon Rivers - dissolution', "Iowa":
                    'GFS IA - dissolution', "Texas":
                    'GFS TX - dissolution', "Florida":
                    'EcoWolf - dissolution', "Missouri":
                    'Veolia - dissolution'}, "pyrolysis": {
                "South Carolina": 'Carbon Conversions', "Tennessee":
                    'Carbon Rivers'}, "mechanical_recycling": {
                "Iowa": 'GFS IA', "Texas": 'GFS TX', "Florida":
                    'EcoWolf'}, "cement_co_processing": {
                "Missouri": 'Veolia'}},
        "detailed_transport_model": True}

    def set_up_batch_run(
            nr_processes, variable_params, fixed_params, number_steps):
        batch_run = BatchRunnerMP(
            WindABM,
            nr_processes=nr_processes,
            variable_parameters=variable_params,
            fixed_parameters=fixed_params,
            iterations=1,
            max_steps=number_steps,
            model_reporters={
                "Year":
                    lambda a: getattr(a, "clock") +
                    fixed_params["temporal_scope"]['simulation_start'] - 1,
                "Cumulative capacity (MW)": lambda a: getattr(a, "all_cap"),
                "State cumulative capacity (MW)":
                    lambda a: getattr(a, "states_cap"),
                "Cumulative waste (metric tons)":
                    lambda a: getattr(a, "all_waste"),
                "State waste (metric tons)":
                    lambda a: getattr(a, "states_waste"),
                "State waste - eol pathways (metric tons)":
                    lambda a: getattr(a, "states_waste_eol_path"),
                "Number wpo agents": lambda a: getattr(a, "number_wpo_agent"),
                "eol pathway adoption":
                    lambda a: getattr(a, "eol_pathway_adoption"),
                "Blade type adoption (MW)":
                    lambda a: getattr(a, "blade_type_capacities"),
                "Average recycling costs ($/metric ton)":
                    lambda a: getattr(a, "average_eol_costs"),
                "Recovered materials (metric tons)":
                    lambda a: getattr(a, "recovered_materials"),
                "Manufactured blades (MW)":
                    lambda a: getattr(a, "bt_manufactured_q"),
                "Manufacturing waste (metric tons)":
                    lambda a: getattr(a, "manufacturing_waste_q"),
                "Turbines average lifetime (years)":
                    lambda a: a.safe_div(
                        sum(getattr(a, "average_lifetimes_wpo")),
                        len(getattr(a, "average_lifetimes_wpo"))),
                "Total eol costs ($)":
                    lambda a: getattr(a, "total_eol_costs"),
                "Total eol revenues ($)":
                    lambda a: getattr(a, "total_eol_revenues"),
                "Total manufacturing waste costs ($)":
                    lambda a: getattr(a, "total_man_waste_costs"),
                "Total manufacturing waste revenues ($)":
                    lambda a: getattr(a, "total_man_waste_revenues"),
                "Total blade costs ($)":
                    lambda a: getattr(a, "total_bt_costs"),
                "Landfill waste volume model":
                    lambda a: a.waste_volume_model['waste_volume'],
                "Landfill number": lambda a: getattr(a, "landfill_count"),
                "Landfills remaining capacity (ton or m3)":
                    lambda a: getattr(a, "landfill_remaining_cap"),
                "Landfills initial capacity (ton or m3)":
                    lambda a: getattr(a, "init_land_capacity"),
                "Landfill ban enacted":
                    lambda a: {key: value['landfill'] for key, value in
                               a.bans_enacted.items()},
                "Blade waste in landfill":
                    lambda a: getattr(a, "state_blade_waste"),
                "Yearly waste ratios":
                    lambda a: getattr(a, "yearly_waste_ratios"),
                "Cumulative blade ratios":
                    lambda a: getattr(a, "cum_blade_ratios"),
                "Cumulative waste ratios":
                    lambda a: getattr(a, "cum_waste_ratios")})
        return batch_run

    # noinspection PyShadowingNames
    # The variable parameters will be invoke along with the fixed parameters
    # allowing for either or both to be honored.
    def run_batch(sobol, number_steps, number_run, num_core):
        nr_processes = num_core
        if not sobol:
            variable_params = {
                "seed": list(range(number_run)),
                "calibration": [11],
                "calibration_2": [0.8, 1],
                "calibration_3": [0.8, 1],  # -0.15
                "calibration_4": [1259, 2059],  # -0.26
                "calibration_5": [1],
                "calibration_6": [0, 2],  # 0.29
                "calibration_7": [1],  # -0.29
                "calibration_8": [1]
            }  # 0.17
            fixed_params = all_fixed_params.copy()
            for key in variable_params.keys():
                fixed_params.pop(key)
            tot_run = 1
            for var_p in variable_params.values():
                tot_run *= len(var_p)
            print("Total number of run:", tot_run)
            fixed_params["temporal_scope"] = {
                'pre_simulation': 2000, 'simulation_start': 2020,
                'simulation_end': (2020 + number_steps)}
            batch_run = set_up_batch_run(
                nr_processes, variable_params, fixed_params, number_steps)
            batch_run.run_all()
            run_data = batch_run.get_model_vars_dataframe()
            run_data.to_csv("results\\BatchRun.csv")
        else:
            list_variables = [
                "calibration_2", "calibration_8"]
            problem = {'num_vars': 2,
                       'names': [
                           "pre-process costs",
                           "w_b"],
                       'bounds': [[0, 132], [0, 1]]}
            x = saltelli.sample(problem, 100)
            baseline_row = np.array([27.56, 1])
            x = np.vstack((x, baseline_row))
            lower_bound_row = np.array([0, 0])
            x = np.vstack((x, lower_bound_row))
            upper_bound_row = np.array([132, 1])
            x = np.vstack((x, upper_bound_row))
            for x_i in range(x.shape[1]):
                lower_bound = deepcopy(baseline_row)
                bounds = problem['bounds'][x_i]
                if lower_bound[x_i] != bounds[0]:
                    lower_bound[x_i] = bounds[0]
                    x = np.vstack((x, lower_bound))
                upper_bound = deepcopy(baseline_row)
                if upper_bound[x_i] != bounds[1]:
                    upper_bound[x_i] = bounds[1]
                    x = np.vstack((x, upper_bound))
            appended_data = []
            for i in range(x.shape[0]):
                print("Sobol matrix line: ", i, " out of ", x.shape[0])
                fixed_params = deepcopy(all_fixed_params)
                for j in range(x.shape[1]):
                    value_to_change = x[i][j]
                    variable_to_change = list_variables[j]
                    if j < 1:
                        fixed_params[variable_to_change] = value_to_change
                    elif j < 2:
                        fixed_params[variable_to_change] = value_to_change
                    elif j < 3:
                        fixed_params[variable_to_change] = value_to_change
                    elif j < 4:
                        fixed_params[variable_to_change] = value_to_change
                    else:
                        fixed_params[variable_to_change] = value_to_change
                variable_params = {"seed": list(range(number_run))}
                tot_run = 1
                for var_p in variable_params.values():
                    tot_run *= len(var_p)
                print('With', tot_run, 'iterations per line')
                fixed_params["temporal_scope"] = {
                    'pre_simulation': 2000, 'simulation_start': 2020,
                    'simulation_end': (2020 + number_steps)}
                # fixed_params["batch_run"] = False
                fixed_params["calibration"] = 5
                fixed_params["calibration_3"] = 0.11 * 0.53
                for key in variable_params.keys():
                    fixed_params.pop(key)
                batch_run = set_up_batch_run(
                    nr_processes, variable_params, fixed_params, number_steps)
                batch_run.run_all()
                run_data = batch_run.get_model_vars_dataframe()
                for k in range(x.shape[1]):
                    run_data["x_%s" % k] = x[i][k]
                appended_data.append(run_data)
            appended_data = pd.concat(appended_data)
            appended_data.to_csv("results\\SobolBatchRun.csv")

    run_batch(sobol=False, number_steps=31, number_run=20, num_core=6)

    t1 = time.time()
    print(t1 - t0)
    print("Done!")
