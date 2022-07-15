import pandas as pd
import numpy as np
import json
from datetime import datetime

# Author: Kent Nex
# Date: 2022-06-06 
# Title: Eve ore calculator

class pilot_information:
    def __init__(self):
        self.name = ""
        self.other_names = []
        self.ore = {}
    
    def set_name(self, name):
        self.name = name

    def set_other_names(self, other_names):
        self.other_names = other_names

    def set_pilot_ores(self, ore):
         self.ore = ore

    def get_name(self):
        return self.name

    def get_other_names(self):
        return self.other_names

class pilot_manager:
    def __init__(self):
        self.pilots = {}
    
    def add_pilot_from_class(self, pilot):
        self.pilots[pilot.name] = pilot

    def add_pilot_from_json(self, pilot_name, pilot_other_names):
        pilot = pilot_information()
        pilot.set_name(pilot_name)
        pilot.set_other_names(pilot_other_names)
        self.pilots[pilot_name] = pilot

    def print_pilots(self):
        for pilot in self.pilots:
            print("{0}: {1}: {2}".format(pilot, self.pilots[pilot].get_other_names(),  self.pilots[pilot].ore))
        
def open_config(path):
    with open(path, "r") as read_file:
        decoded_file = json.load(read_file)
    return decoded_file

def get_ore_list(file):
    ore_list = []
    for section in file['ore']:
        ore_section = file['ore'][section]
        for modifier in ore_section['modifier']:
            for ore_type in ore_section['type']:
                ore_list.append((modifier + " " + ore_type).strip())
    return(ore_list)

def get_config_information(path, pilots):
    config_file = open_config(path)

    file_path = config_file['file_location']
    tax_rate = config_file['tax_rate']
    pilots_json = config_file['pilot_names']
    ore_list = get_ore_list(config_file)
    
    for pilot in pilots_json:
        pilots.add_pilot_from_json(pilot, pilots_json[pilot])

    return (tax_rate, ore_list, file_path)

def get_ore_pilots(path, pilots, ore_list):
    features = ["Pilot", "Quantity", "Ore Type"]
    df = pd.read_csv(path, sep=',', usecols = features)
    for pilot in pilots.pilots:
        pilot_ores_df = (df[np.isin(df, pilots.pilots[pilot].get_other_names()).any(axis=1)])
        pilot_ores = {}
        for ore in ore_list:
            amount = (pilot_ores_df.loc[pilot_ores_df['Ore Type'] == ore]).sum()[2]
            if amount > 0:
                pilot_ores[ore] = amount
        pilots.pilots[pilot].set_pilot_ores(pilot_ores)
    
def get_total_each_ore_from_pilots(pilots, ore_list):
    total_ore = {}
    for ore in ore_list:
        total_ore[ore] = 0
        for pilot in pilots.pilots:
            if ore in pilots.pilots[pilot].ore:
                total_ore[ore] += pilots.pilots[pilot].ore[ore]
    return total_ore

def print_to_file_with_tax_reduciton(path, pilots, tax_rate, ore_totals):
    padding = len(max(ore_totals, key=len))+1
    max_length = len(str(ore_totals[max(ore_totals, key=ore_totals.get)]))+3
    with open(path, "w") as write_file:
        write_file.write("Player mined after {0}% taxrate:\n\n".format(tax_rate*100))
        for pilot in pilots.pilots:
            if len(pilots.pilots[pilot].ore) > 0:
                write_file.write(pilots.pilots[pilot].get_name()+"\n")
                for ore in pilots.pilots[pilot].ore:
                    if pilots.pilots[pilot].ore[ore] > 0:
                        left_format = "    {0}".format(ore).ljust(padding)
                        right_format = "{0}".format(str(round(int(pilots.pilots[pilot].ore[ore])*(1-tax_rate)))).rjust(max_length)
                    write_file.write("{0}{1}\n".format(left_format, right_format))
            write_file.write('\n')
        
        write_file.write("\nOre Totals pre tax: (for listed pilots)\n")
        for ore in ore_totals:
            if ore_totals[ore] > 0:
                write_file.write("{0}{1}\n".format(ore.ljust(padding), str(ore_totals[ore]).rjust(max_length)))

tax_rate = 0
pilots = pilot_manager()
ore_list = []

tax_rate, ore_list, csv_sheet = get_config_information('config.json', pilots)
get_ore_pilots(csv_sheet, pilots, ore_list)
ore_totals = get_total_each_ore_from_pilots(pilots, ore_list)

now = datetime.now()
print_to_file_with_tax_reduciton(now.strftime("output_%d_%m_%Y_%H_%M_%S.txt"), pilots, tax_rate, ore_totals)
