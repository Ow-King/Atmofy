# File for the creation of the NP data frame that contains all of the parameters that will be used in the final app

import pandas as pd
from weather import get_weather
from time_features import get_next_3_hour_encoding


def get_next_3_hrs_parameters(latitude, longitude) -> pd.DataFrame:
    weather_df = get_weather(latitude, longitude)
    time_df = get_next_3_hour_encoding()
    result = pd.concat([weather_df, time_df], axis=1)
    return result


if __name__ == "__main__":
    param_dataframe = get_next_3_hrs_parameters(38.951, -92.334)
    print("\n3-Hour Parameter Data\n", param_dataframe)