import json
import pandas as pd
from data_handler import SQLiteFetcher
from data_handler import list_features, export_geojson

excel_file_path = '/workspaces/python3-poetry-pyenv/src/data/fz1_2023.xlsx'
skip_rows= 7

df_fz1_1 = pd.read_excel(excel_file_path, sheet_name='FZ1.2', skiprows=skip_rows, usecols="B:AF")

# Rename columns that contain "Unnamed" with the value in the first row (now index 0 after skipping rows)
new_columns = [col if "Unnamed" not in col else df_fz1_1.iloc[0][col] for col in df_fz1_1.columns]
df_fz1_1.columns = new_columns

# Drop the first row as it is now redundant after renaming columns
df_fz1_1 = df_fz1_1.drop(df_fz1_1.index[0])

# Fill NaNs in the 'Land' and 'Regierungsbezirk' columns with the last valid observation to propagate it forward
df_fz1_1['Land'] = df_fz1_1['Land\n\n'].ffill()
df_fz1_1['Regierungsbezirk'] = df_fz1_1['Regierungsbezirk'].ffill()

# Create new columns 'Statistische Kennziffer' and 'Zulassungsbezirk' with NaN values initially
df_fz1_1['Statistische Kennziffer'] = None
df_fz1_1['Zulassungsbezirk'] = None
# Populate these new columns by splitting the 'Statistische Kennziffer und Zulassungsbezirk' column
split_data = df_fz1_1['Statistische Kennziffer und Zulassungsbezirk\n'].str.split(n=1, expand=True)
df_fz1_1['Statistische Kennziffer'] = split_data[0]
df_fz1_1['Zulassungsbezirk'] = split_data[1]

with SQLiteFetcher('../../ChargeApp.db') as fetcher:
    kreise = fetcher.fetch_kreise()

# Merge the original DataFrame with the dictionary DataFrame on the matching variable
merged_df = pd.merge(
    pd.DataFrame(kreise).dropna(subset=['ags'])
    , df_fz1_1.dropna(subset=['Statistische Kennziffer'])
    , right_on='Statistische Kennziffer'
    , left_on='ags'
    , how='right'
    )

merged_df.rename(columns={'Insgesamt': 'cars',
                          'Nach Kraftstoffarten': 'cars_gasoline',
                          'Diesel': 'cars_diesel',
                          'Gas\n(einschl.\nbivalent)': 'cars_gas',
                          'Hybrid \ninsgesamt': 'cars_hybrid',
                          'darunter\nPlug-in-Hybrid': 'cars_plugin',
                          'Elektro (BEV)': 'cars_electric',
                          'sonstige': 'cars_other'
                          }, inplace=True)

df = merged_df[["KREISID", "ags", "nuts", "Land", "bez", "gen",
                "ewz", "stations", "cars", "cars_gasoline",
                "cars_diesel", "cars_gas", "cars_hybrid",
                "cars_plugin", "cars_electric", "cars_other"]]

def calculate_new_variable(df: pd.DataFrame, new_var_name: str, var1: str, var2: str) -> pd.DataFrame:
    """
    Calculate a new variable in the DataFrame based on two existing columns.

    Args:
        df (pd.DataFrame): The original DataFrame.
        new_var_name (str): The name of the new variable.
        var1 (str): The numerator variable.
        var2 (str): The denominator variable.

    Returns:
        pd.DataFrame: The modified DataFrame with the new variable.
    """

    new_df = df.copy()
    new_df.loc[:, new_var_name] = [x / y if y != 0 else None for x, y in zip(new_df[var1], new_df[var2])]

    return new_df

df = calculate_new_variable(df, 'ewz_sta', 'ewz', 'stations')
df = calculate_new_variable(df, 'cars_ewz', 'cars', 'ewz')
df = calculate_new_variable(df, 'cars_electric_ewz', 'cars_electric', 'ewz')
df = calculate_new_variable(df, 'cars_electric_cars', 'cars_electric', 'cars')
df = calculate_new_variable(df, 'cars_electric_sta', 'cars_electric', 'stations')

feature_list = list_features(df.to_dict('records'))
geojson = export_geojson(feature_list)

# Save to a file
with open('../data/ChargeApp.geojson', 'w', encoding="UTF8") as f:
    json.dump(geojson, f)