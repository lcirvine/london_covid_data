import os
import configparser
import requests
import json
from datetime import date, timedelta
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

config = configparser.ConfigParser()
config.read('london_map_settings.ini')
today_date = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d')
images_folder = os.path.join(os.getcwd(), 'Images')
json_folder = os.path.join(os.getcwd(), 'JSON Data')
for fd in [images_folder, json_folder]:
    if not os.path.exists(fd):
        os.mkdir(fd)


class COVIDData:
    def __init__(self):
        # data source: https://data.london.gov.uk/dataset/coronavirus--covid-19--cases
        self.base_url = "https://data.london.gov.uk/api/table/s8c9t_j4fs2"
        self.sql_url = f"?sql=SELECT * FROM dataset WHERE date = '{today_date}'"
        self.url = self.base_url + self.sql_url

    def get_data(self, save_file: bool = True):
        r = requests.get(self.url)
        data = json.loads(r.content)
        df = pd.json_normalize(data, 'rows')
        if len(df) > 0:
            if save_file:
                with open(os.path.join(json_folder, f"London COVID Data {today_date}.txt"), "w") as f:
                    json.dump(data, f)
            return df
        else:
            print("No results for today's date")
            exit()


class LondonMap:
    def __init__(self):
        # data source: https://data.london.gov.uk/dataset/statistical-gis-boundary-files-london
        self.fp_map = os.path.join(config.get('london_map', 'file_path'), 'London_Ward.shp')
        self.map_df = gpd.read_file(self.fp_map)

    def change_names(self):
        self.map_df['DISTRICT'].replace({'City of Westminster': 'Westminster',
                                         'Hackney': 'Hackney and City of London',
                                         'City and County of the City of London': 'Hackney and City of London'},
                                        inplace=True)

    def return_map(self):
        return self.map_df


def main():
    cd = COVIDData()
    df = cd.get_data()
    lm = LondonMap()
    lm.change_names()
    map_df = lm.return_map()

    merged = map_df.set_index('DISTRICT').join(df.set_index('area_name'))
    variable = 'total_cases'
    vmin, vmax = 0, df[variable].max()
    fig, ax = plt.subplots(1, figsize=(10, 6))

    merged.plot(column=variable, cmap='Blues', linewidth=0.8, ax=ax, edgecolor='0.8')
    ax.axis('off')
    ax.set_title('London COVID-19 Cases by Borough', fontdict={'fontsize': '25', 'fontweight': '3'})
    ax.annotate('Source: London Datastore, 2020',
                xy=(0.1, .08), xycoords='figure fraction',
                horizontalalignment='left', verticalalignment='top',
                fontsize=10, color='#555555')

    sm = plt.cm.ScalarMappable(cmap='Blues', norm=plt.Normalize(vmin=vmin, vmax=vmax))
    sm._A = []
    cbar = fig.colorbar(sm)

    fig.savefig(os.path.join(images_folder, f"London COVID Map {today_date}.png"), dpi=300)


if __name__ == '__main__':
    main()
