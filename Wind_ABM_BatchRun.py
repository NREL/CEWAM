# -*- coding:utf-8 -*-
"""
Created on April 17 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

BatchRun - Circular Economy Wind Agent-based Model (CEWAM)
This module run batch runs of the model according to user inputs.
"""


from Wind_ABM_Model import *
from mesa.batchrunner import BatchRunnerMP
import time

# TODO: Continue here:
#  1) fix pull issue in home computer and launch preliminary calibration
#  2) rewrite the sobol code


if __name__ == '__main__':
    t0 = time.time()
    all_fixed_params = {
        "seed": None,
        "calibration": 1,
        "calibration_2": 1,
        "calibration_3": 1,
        "calibration_4": 1,
        "calibration_5": 1,
        "calibration_6": 1,
        "calibration_7": 1,
        "calibration_8": 1,
        "manufacturers": {"wind_blade": 5, "plastics_n_boards": 100,
                          "cement": 97},
        "developers": {'lifetime_extension': 10},
        "recyclers": {"dissolution": 41, "pyrolysis": 2,
                      "mechanical_recycling": 3, "cement_co_processing": 1},
        "small_world_networks": {
            "wind_plant_owners": {"node_degree": 15, "rewiring_prob": 0.1},
            "developers": {"node_degree": 5, "rewiring_prob": 0.1},
            "recyclers": {"node_degree": 5, "rewiring_prob": 0.1},
            "manufacturers": {"node_degree": 15, "rewiring_prob": 0.1},
            "original_equipment_manufacturer": {"node_degree": 4,
                                                "rewiring_prob": 0.1},
            "landfills": {"node_degree": 5, "rewiring_prob": 0.1},
            "regulators": {"node_degree": 5, "rewiring_prob": 0.1}},
        "external_files": {
            "state_distances": "StatesAdjacencyMatrix.csv",
            "uswtdb": "uswtdb_v3_3_20210114.csv",
            "projections": "nrel_mid_case_projections.csv",
            "wbj_database": "WBJ Landfills 2020.csv"},
        "average_lifetime": {'thermoset': [20.0, 20.1],
                             'thermoplastic': [20.0, 20.01]},
        "weibull_shape_factor": 2.2,
        "blade_size_to_mass_model": {'coefficient': 0.0026, 'power': 2.1447},
        "cap_to_diameter_model": {'coefficient': 57, 'power': 0.44},
        "temporal_scope": {'pre_simulation': 2000, 'simulation_start': 2020,
                           'simulation_end': 2061},
        "blades_per_rotor": 3,
        "eol_pathways": {"lifetime_extension": True, "dissolution": False,
                         "pyrolysis": True, "mechanical_recycling": True,
                         "cement_co_processing": True, "landfill": True},
        "eol_pathways_dist_init": {
            "lifetime_extension": 0.005, "dissolution": 0.0,
            "pyrolysis": 0.005, "mechanical_recycling": 0.005,
            "cement_co_processing": 0.005, "landfill": 0.98},
        "tpb_eol_coeff": {'w_bi': 0.33, 'w_a': 0.30, 'w_sn': 0.56,
                          'w_pbc': -0.13, 'w_p': 0.11, 'w_b': -0.21},
        "attitude_eol_parameters": {"mean": 0.84, 'standard_deviation': 0.1,
                                    'min': 0, 'max': 1},
        "choices_circularity": {
            "lifetime_extension": True, "dissolution": True, "pyrolysis": True,
            "mechanical_recycling": True, "cement_co_processing": True,
            "landfill": False, "thermoset": False, "thermoplastic": True},
        "decommissioning_cost": [1300, 33000],
        "lifetime_extension_costs": [600, 6000],
        "rec_processes_costs": {
            "dissolution": [0, 1E-6], "pyrolysis": [280.5, 550],
            "mechanical_recycling": [212.3, 286],
            "cement_co_processing": [99, 132]},
        "transport_shreds": {'shredding_costs': [99, 132],
                             'transport_cost_shreds': [0.0314, 0.0820]},
        "transport_segments": {
            'cutting_costs': 27.56, 'transport_cost_segments': 8.7,
            'length_segment': 30, 'segment_per_truck': 2},
        "transport_repair": 1.57,
        "eol_pathways_transport_mode": {
            "lifetime_extension": 'transport_repair',
            "dissolution": 'transport_segment',
            "pyrolysis": 'transport_segment',
            "mechanical_recycling": 'transport_segment',
            "cement_co_processing": 'transport_segment',
            "landfill": 'transport_segment'},
        "lifetime_extension_revenues": [124, 1.7E6],
        "rec_processes_revenues": {
            "dissolution": [0, 1E-6], "pyrolysis": [336, 672],
            "mechanical_recycling": [242, 302.5],
            "cement_co_processing": [0, 1E-6]},
        "lifetime_extension_years": [5, 15],
        "le_feasibility": 0.55,
        "early_failure_share": 0.03,
        "blade_types": {"thermoset": True, "thermoplastic": True},
        "blade_types_dist_init": {"thermoset": 1.0, "thermoplastic": 0.0},
        "tpb_bt_coeff": {'w_bi': 1.00, 'w_a': 0.30, 'w_sn': 0.21,
                         'w_pbc': -0.32, 'w_p': 0.00, 'w_b': 0.00},
        "attitude_bt_parameters": {'mean': 0.5, 'standard_deviation': 0.1,
                                   'min': 0, 'max': 1},
        "blade_costs": {"thermoset": [50E3, 500E3],
                        "thermoplastic_rate": 0.953},
        "recyclers_states": {
            "dissolution": [
                "Alabama", "Alabama", "Colorado", "Colorado", "Iowa",
                "Illinois", "Massachusetts", "Maine", "Maine", "Michigan",
                "Michigan", "Michigan", "Michigan", "Michigan", "Minnesota",
                "Missouri", "Missouri", "Missouri", "North Carolina",
                "North Carolina", "North Carolina", "North Carolina",
                "North Carolina", "New Jersey", "Ohio", "Ohio", "Ohio", "Ohio",
                "Ohio", "Pennsylvania", "Pennsylvania", "Pennsylvania",
                "South Carolina", "South Carolina", "South Carolina",
                "South Carolina", "Texas", "Texas", "Texas", "Texas", "Texas"],
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
            "dissolution": {"steel": 1, "plastic": 1, "resin": 1,
                            "glass_fiber": 1},
            "pyrolysis": {"steel": 1, "plastic": 0, "resin": 0,
                          "glass_fiber": 0.5},
            "mechanical_recycling": {"steel": 1, "plastic": 1, "resin": 1,
                                     "glass_fiber": 1},
            "cement_co_processing": {"steel": 1, "plastic": 0, "resin": 0,
                                     "glass_fiber": 1}},
        "bt_man_dist_init": {"thermoset": 1, "thermoplastic": 0.0},
        "attitude_bt_man_parameters": {
            'mean': 0.5, 'standard_deviation': 0.1, 'min': 0, 'max': 1},
        "tpb_bt_man_coeff": {'w_bi': 1.00, 'w_a': 0.15, 'w_sn': 0.35,
                             'w_pbc': -0.24, 'w_p': 0.00, 'w_b': 0.00},
        "lag_time_tp_blade_dev": 5,
        "tp_production_share": 0.5,
        "manufacturing_waste_ratio": {
            "steel": [0.12, 0.3], "plastic": [0.12, 0.3],
            "resin": [0.12, 0.3], "glass_fiber": [0.12, 0.3]},
        "oem_states": {
            "wind_blade": ["Colorado", "North Dakota", "South Dakota", "Iowa",
                           "Iowa"]},
        "man_waste_dist_init": {
            "dissolution": 0.0, "mechanical_recycling": 0.02,
            "landfill": 0.98},
        "tpb_man_waste_coeff": {'w_bi': 1.00, 'w_a': 0.30, 'w_sn': 0.56,
                                'w_pbc': -0.13, 'w_p': 0.00, 'w_b': 0.00},
        "attitude_man_waste_parameters": {
            "mean": 0.5, 'standard_deviation': 0.01, 'min': 0, 'max': 1},
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
                 'no_ban': 0.52}}}}

    def batch_parameters(sobol):
        if not sobol:
            nr_processes = 6
            variable_params = {
                "seed": list(range(10)),
                "calibration": [0.84],
                "calibration_2": [0.30],
                "calibration_3": [-0.21],
                "calibration_4": [-0.13],
                "calibration_5": [0],
                "calibration_6": [0],
                "calibration_7": [0],
                "calibration_8": [0.33]}
            fixed_params = all_fixed_params.copy()
            for key in variable_params.keys():
                fixed_params.pop(key)
            tot_run = 1
            for var_p in variable_params.values():
                tot_run *= len(var_p)
            print("Total number of run:", tot_run)
            return nr_processes, variable_params, fixed_params
        else:
            pass

    # noinspection PyShadowingNames
    # The variables parameters will be invoke along with the fixed parameters
    # allowing for either or both to be honored.
    def run_batch(sobol):
        nr_processes, variable_params, fixed_params = batch_parameters(sobol)
        batch_run = BatchRunnerMP(
            WindABM,
            nr_processes=nr_processes,
            variable_parameters=variable_params,
            fixed_parameters=fixed_params,
            iterations=1,
            max_steps=41,
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
                    lambda a: getattr(a, "yearly_waste_ratios")})
        batch_run.run_all()
        if not sobol:
            run_data = batch_run.get_model_vars_dataframe()
            run_data.to_csv("results\\BatchRun.csv")
        else:
            pass

    run_batch(sobol=False)

    t1 = time.time()
    print(t1 - t0)
    print("Done!")
