import pandas as pd
import numpy as np

# Ingredients
components = ['Seeds', 'Stems', 'Leaves', 'Moisture', 'CBD', 'Oil',
              'Cellulose', 'Hemicellulose', 'Lignin', 'Extractives', 'Waste',
              'Biopolymer', 'Binder', 'Additives', 'Water', 'Glycerol']

# DataFrames for streams and losses
streams = pd.DataFrame(columns=components)
losses = pd.DataFrame(columns=components)

# Initialize a list to store mass inputs and outputs at each step
process_steps = []


# Function to record and print mass flows at each step
def record_process_step(step_name, mass_input_streams, mass_output_streams, waste_output_losses,
                        mass_input_additional=0):
    mass_input = sum([streams.loc[stream].sum() for stream in mass_input_streams]) + mass_input_additional
    mass_output = sum([streams.loc[stream].sum() for stream in mass_output_streams])
    waste_output = sum([losses.loc[loss].sum() for loss in waste_output_losses])

    process_steps.append({
        'Step': step_name,
        'Mass Input': mass_input,
        'Mass Output': mass_output,
        'Waste Output': waste_output
    })

    print(f"\nStep: {step_name}")
    print(f"  Mass Input: {mass_input:.2f} kg/hr")
    print(f"  Mass Output: {mass_output:.2f} kg/hr")
    print(f"  Waste Output: {waste_output:.2f} kg/hr")


# Mass inflow rate
total_biomass = 100  # kg/hr

# Yield fractions
seed_yield_fraction = 0.1333  # Seeds are 13.33% of plant
leaf_yield_fraction = 0.3  # Leaves are 30%
stem_yield_fraction = 1 - seed_yield_fraction - leaf_yield_fraction

seed_mass = total_biomass * seed_yield_fraction
stem_mass = total_biomass * stem_yield_fraction
leaf_mass = total_biomass * leaf_yield_fraction

# Moisture contents
seed_moisture_content = 0.08  # 8%
stem_moisture_content = 0.70  # 70%
leaf_moisture_content = 0.70  # 70%

seed_moisture = seed_mass * seed_moisture_content
stem_moisture = stem_mass * stem_moisture_content
leaf_moisture = leaf_mass * leaf_moisture_content

seed_dry_mass = seed_mass * (1 - seed_moisture_content)
stem_dry_mass = stem_mass * (1 - stem_moisture_content)
leaf_dry_mass = leaf_mass * (1 - leaf_moisture_content)

# Step 1: Harvesting Biomass
streams.loc['Harvested Biomass'] = {
    'Seeds': seed_dry_mass,
    'Stems': stem_dry_mass,
    'Leaves': leaf_dry_mass,
    'Moisture': seed_moisture + stem_moisture + leaf_moisture,
    # Other components set to zero
}

# Leaf Waste
losses.loc['Leaf Waste'] = {
    'Waste': leaf_dry_mass,
    'Moisture': leaf_moisture,
    # Other components as zeros
}

# Record mass flows for Harvesting Biomass
step_mass_input = total_biomass
step_mass_output = streams.loc['Harvested Biomass'].sum()
waste_output = losses.loc['Leaf Waste'].sum().sum()

process_steps.append({
    'Step': 'Harvesting Biomass',
    'Mass Input': step_mass_input,
    'Mass Output': step_mass_output,
    'Waste Output': waste_output
})

print(f"Step: Harvesting Biomass")
print(f"  Mass Input: {step_mass_input:.2f} kg/hr")
print(f"  Mass Output: {step_mass_output:.2f} kg/hr")
print(f"  Waste Output: {waste_output:.2f} kg/hr")

# Separation Losses
separation_loss_percentage = 0.01  # 1%

separation_loss_seeds = streams.loc['Harvested Biomass', 'Seeds'] * separation_loss_percentage
separation_loss_stems = streams.loc['Harvested Biomass', 'Stems'] * separation_loss_percentage
separation_loss_moisture_seeds = seed_moisture * separation_loss_percentage
separation_loss_moisture_stems = stem_moisture * separation_loss_percentage

losses.loc['Separation Loss'] = {
    'Seeds': separation_loss_seeds,
    'Stems': separation_loss_stems,
    'Moisture': separation_loss_moisture_seeds + separation_loss_moisture_stems,
    # Other components as zeros
}

# Separated Seeds
streams.loc['Separated Seeds'] = {
    'Seeds': streams.loc['Harvested Biomass', 'Seeds'] - separation_loss_seeds,
    'Moisture': seed_moisture - separation_loss_moisture_seeds,
    # Other components as zeros
}

# Separated Stems
streams.loc['Separated Stems'] = {
    'Stems': streams.loc['Harvested Biomass', 'Stems'] - separation_loss_stems,
    'Moisture': stem_moisture - separation_loss_moisture_stems,
    # Other components as zeros
}

# Record mass flows for Separation
record_process_step(
    'Separation of Seeds and Stems',
    ['Harvested Biomass'],
    ['Separated Seeds', 'Separated Stems'],
    ['Separation Loss']
)

# Seed Drying
target_seed_moisture_content = 0.05  # 5%

final_seed_moisture = streams.loc['Separated Seeds', 'Seeds'] * target_seed_moisture_content / (
            1 - target_seed_moisture_content)
moisture_removed_seed_drying = streams.loc['Separated Seeds', 'Moisture'] - final_seed_moisture

losses.loc['Seed Drying Loss'] = {
    'Moisture': moisture_removed_seed_drying,
    # Other components as zeros
}

streams.loc['Dried Seeds'] = streams.loc['Separated Seeds'].copy()
streams.loc['Dried Seeds', 'Moisture'] = final_seed_moisture

# Record mass flows for Seed Drying
record_process_step(
    'Seed Drying',
    ['Separated Seeds'],
    ['Dried Seeds'],
    ['Seed Drying Loss']
)

# CBD and Oil Content
seed_CBD_content = 0.017  # 1.7%
seed_oil_content = 0.31  # 31%

streams.loc['Dried Seeds', 'CBD'] = streams.loc['Dried Seeds', 'Seeds'] * seed_CBD_content
streams.loc['Dried Seeds', 'Oil'] = streams.loc['Dried Seeds', 'Seeds'] * seed_oil_content

# Correct the Seeds mass by removing CBD and Oil for mass balance
streams.loc['Dried Seeds', 'Seeds'] -= (streams.loc['Dried Seeds', 'CBD'] + streams.loc['Dried Seeds', 'Oil'])

# Oil Extraction
cbd_extraction_efficiency = 0.3
oil_extraction_efficiency = 0.3

cbd_extracted = streams.loc['Dried Seeds', 'CBD'] * cbd_extraction_efficiency
oil_extracted = streams.loc['Dried Seeds', 'Oil'] * oil_extraction_efficiency

streams.loc['Extracted Seed Oils'] = {
    'CBD': cbd_extracted,
    'Oil': oil_extracted,
    # Other components as zeros
}

# Processed Seeds
streams.loc['Processed Seeds'] = streams.loc['Dried Seeds'].copy()
streams.loc['Processed Seeds', 'CBD'] -= cbd_extracted
streams.loc['Processed Seeds', 'Oil'] -= oil_extracted

# Add 'Processed Seeds' to losses as waste
losses.loc['Processed Seeds Waste'] = streams.loc['Processed Seeds']

# Remove 'Processed Seeds' from streams (optional)
streams.drop('Processed Seeds', inplace=True)

# Seed Extraction Loss
extraction_loss_percentage = 0.1
losses.loc['Seed Extraction Loss'] = streams.loc['Extracted Seed Oils'] * extraction_loss_percentage
streams.loc['Extracted Seed Oils'] *= (1 - extraction_loss_percentage)

# Record mass flows for Oil Extraction
record_process_step(
    'Oil Extraction',
    ['Dried Seeds'],
    ['Extracted Seed Oils'],
    ['Seed Extraction Loss', 'Processed Seeds Waste']
)

# Cream Production
additive_ratio = 12  # kg of 'Additives' per kg of 'oil_extracted'
water_ratio = 35  # kg of 'Water' per kg of 'oil_extracted'
glycerol_ratio = 2.14  # kg of 'Glycerol' per kg of 'oil_extracted'

additives = {
    'Additives': oil_extracted * additive_ratio,
    'Water': oil_extracted * water_ratio,
    'Glycerol': oil_extracted * glycerol_ratio
}

additives_series = pd.Series(additives)

# Add the masses to create 'Cream Product'
streams.loc['Cream Product'] = streams.loc['Extracted Seed Oils'].add(additives_series, fill_value=0)

# Cream Mixing Loss
mixing_loss_percentage = 0.01
losses.loc['Cream Mixing Loss'] = streams.loc['Cream Product'] * mixing_loss_percentage

# Adjust 'Cream Product' after losses
streams.loc['Cream Product'] *= (1 - mixing_loss_percentage)


# Record mass flows for Cream Production
record_process_step(
    'Cream Production',
    ['Extracted Seed Oils'],
    ['Cream Product'],
    ['Cream Mixing Loss'],
    mass_input_additional=sum(additives.values())
)

# Stem Drying
target_stem_moisture_content = 0.15  # 15%

final_stem_moisture = streams.loc['Separated Stems', 'Stems'] * target_stem_moisture_content / (
            1 - target_stem_moisture_content)
moisture_removed_stem_drying = streams.loc['Separated Stems', 'Moisture'] - final_stem_moisture

losses.loc['Stem Drying Loss'] = {
    'Moisture': moisture_removed_stem_drying,
    # Other components as zeros
}

streams.loc['Dried Stems'] = streams.loc['Separated Stems'].copy()
streams.loc['Dried Stems', 'Moisture'] = final_stem_moisture

# Record mass flows for Stem Drying
record_process_step(
    'Stem Drying',
    ['Separated Stems'],
    ['Dried Stems'],
    ['Stem Drying Loss']
)

# Retting
retting_loss_percentage = 0.05  # 5%

streams.loc['Retting Output'] = streams.loc['Dried Stems'].copy()
retting_loss = streams.loc['Retting Output'] * retting_loss_percentage
streams.loc['Retting Output'] -= retting_loss

losses.loc['Retting Loss'] = retting_loss

# Record mass flows for Retting
record_process_step(
    'Retting',
    ['Dried Stems'],
    ['Retting Output'],
    ['Retting Loss']
)

# Bark and Core Separation
bark_fraction = 0.30
core_fraction = 0.70

bark_mass = streams.loc['Retting Output', 'Stems'] * bark_fraction
core_mass = streams.loc['Retting Output', 'Stems'] * core_fraction

# Decortication
streams.loc['Decorticated Bark'] = {
    'Stems': 0,
    'Cellulose': bark_mass * 0.648,
    'Hemicellulose': bark_mass * 0.077,
    'Lignin': bark_mass * 0.043,
    'Extractives': bark_mass * 0.232,
    'Moisture': streams.loc['Retting Output', 'Moisture'] * (bark_fraction / (bark_fraction + core_fraction)),
    # Other components as zeros
}

streams.loc['Decorticated Core'] = {
    'Stems': 0,
    'Cellulose': core_mass * 0.345,
    'Hemicellulose': core_mass * 0.178,
    'Lignin': core_mass * 0.208,
    'Extractives': core_mass * 0.269,
    'Moisture': streams.loc['Retting Output', 'Moisture'] * (core_fraction / (bark_fraction + core_fraction)),
    # Other components as zeros
}

# Decortication Loss
decortication_loss_percentage = 0.05
decortication_loss = (streams.loc['Decorticated Bark'] + streams.loc[
    'Decorticated Core']) * decortication_loss_percentage
losses.loc['Decortication Loss'] = decortication_loss
streams.loc['Decorticated Bark'] *= (1 - decortication_loss_percentage)
streams.loc['Decorticated Core'] *= (1 - decortication_loss_percentage)

# Record mass flows for Decortication
record_process_step(
    'Decortication',
    ['Retting Output'],
    ['Decorticated Bark', 'Decorticated Core'],
    ['Decortication Loss']
)

# Fiber Extraction
bark_fiber_recovery = 0.50
core_fiber_recovery = 0.50

streams.loc['Bark Fibers'] = streams.loc['Decorticated Bark'].copy()
streams.loc['Bark Fibers', 'Cellulose'] *= bark_fiber_recovery

streams.loc['Core Fibers'] = streams.loc['Decorticated Core'].copy()
streams.loc['Core Fibers', 'Cellulose'] *= core_fiber_recovery

# Fiber Extraction Loss
bark_waste = streams.loc['Decorticated Bark'] - streams.loc['Bark Fibers']
core_waste = streams.loc['Decorticated Core'] - streams.loc['Core Fibers']
losses.loc['Fiber Extraction Loss'] = bark_waste + core_waste

# Record mass flows for Fiber Extraction
record_process_step(
    'Fiber Extraction',
    ['Decorticated Bark', 'Decorticated Core'],
    ['Bark Fibers', 'Core Fibers'],
    ['Fiber Extraction Loss']
)

# Packaging Materials
fibers_for_jars = streams.loc['Core Fibers'].copy()

jar_production_loss_percentage = 0.5
jar_production_loss = fibers_for_jars * jar_production_loss_percentage
losses.loc['Jar Production Loss'] = jar_production_loss
fibers_for_jars_processed = fibers_for_jars * (1 - jar_production_loss_percentage)

fibers_for_boxes = streams.loc['Bark Fibers'].copy()

box_production_loss_percentage = 0.5
box_production_loss = fibers_for_boxes * box_production_loss_percentage
losses.loc['Box Production Loss'] = box_production_loss
fibers_for_boxes_processed = fibers_for_boxes * (1 - box_production_loss_percentage)

# Jar and Box Additives
fibers_for_jars_mass = fibers_for_jars_processed.sum()
jar_biopolymer_ratio = 0.1  # kg of 'Biopolymer' per kg of fibers used in jars

jar_additives = {
    'Biopolymer': fibers_for_jars_mass * jar_biopolymer_ratio
}

fibers_for_boxes_mass = fibers_for_boxes_processed.sum()
box_binder_ratio = 0.1  # kg of 'Binder' per kg of fibers used in boxes

box_additives = {
    'Binder': fibers_for_boxes_mass * box_binder_ratio
}

# Cream Jars
streams.loc['Cream Jars'] = fibers_for_jars_processed.copy()
streams.loc['Cream Jars'].update(jar_additives)

# Outer Packaging
streams.loc['Outer Packaging'] = fibers_for_boxes_processed.copy()
streams.loc['Outer Packaging'].update(box_additives)

# Record mass flows for Packaging Production
record_process_step(
    'Packaging Production',
    ['Bark Fibers', 'Core Fibers'],
    ['Cream Jars', 'Outer Packaging'],
    ['Jar Production Loss', 'Box Production Loss'],
    mass_input_additional=sum(jar_additives.values()) + sum(box_additives.values())
)

# Now we can calculate total input and output
total_input_mass = streams.loc['Harvested Biomass'].sum() + \
                   sum(additives.values()) + \
                   sum(jar_additives.values()) + \
                   sum(box_additives.values())

# Total output mass
total_output_mass = streams.loc['Cream Product'].sum() + \
                    streams.loc['Cream Jars'].sum() + \
                    streams.loc['Outer Packaging'].sum()

# Total waste mass
losses = losses.fillna(0)
total_waste_mass = losses.sum().sum()

# Mass balance check
mass_balance_difference = total_input_mass - (total_output_mass + total_waste_mass)

# Output final results
print("\nLosses DataFrame:")
print(losses)

print(f"\nTotal Input Mass: {total_input_mass:.2f} kg/hr")
print(f"Total Output Mass: {total_output_mass:.2f} kg/hr")
print(f"Total Waste Mass: {total_waste_mass:.2f} kg/hr")
print(f"Mass Balance Difference (should be close to 0): {mass_balance_difference:.2f} kg/hr")

# Optional: Print a summary of mass flows at each step
print("\nSummary of Mass Flows at Each Step:")
for step in process_steps:
    print(f"{step['Step']}:")
    print(f"  Mass Input: {step['Mass Input']:.2f} kg/hr")
    print(f"  Mass Output: {step['Mass Output']:.2f} kg/hr")
    print(f"  Waste Output: {step['Waste Output']:.2f} kg/hr")

# Define the path where you want to save the Excel file
file_path = "mass_flow_details.xlsx"

# Create a Pandas Excel writer using the openpyxl engine
with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
    # Export streams DataFrame to a sheet named "Mass Flow"
    streams.to_excel(writer, sheet_name='Mass Flow')

    # Export losses DataFrame to a sheet named "Losses"
    losses.to_excel(writer, sheet_name='Losses')

print(f"Mass flow details exported to {file_path}")
