import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)


def get_weather(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "minutely_15": "temperature_2m,cloud_cover,rain,showers,snowfall,snowfall_height",
        "hourly": "is_day",
        "forecast_hours": 3,
        "forecast_minutely_15": 12
    }
    responses = openmeteo.weather_api(url, params = params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation: {response.Elevation()} m asl")
    print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

    # Process minutely_15 data. The order of variables needs to be the same as requested.
    minutely_15 = response.Minutely15()
    minutely_15_temperature_2m = minutely_15.Variables(0).ValuesAsNumpy()
    minutely_15_cloud_cover = minutely_15.Variables(1).ValuesAsNumpy()
    minutely_15_rain = minutely_15.Variables(2).ValuesAsNumpy()
    minutely_15_showers = minutely_15.Variables(3).ValuesAsNumpy()
    minutely_15_snowfall = minutely_15.Variables(4).ValuesAsNumpy()
    minutely_15_snowfall_height = minutely_15.Variables(5).ValuesAsNumpy()

    # Process the hourly data for the status of the daylight.
    hourly = response.Hourly()
    hourly_is_day = hourly.Variables(0).ValuesAsNumpy()

    minutely_15_data = {
        "date": pd.date_range(
            start = pd.to_datetime(minutely_15.Time(), unit = "s", utc = True),
            end = pd.to_datetime(minutely_15.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = minutely_15.Interval()),
            inclusive = "left"
        )
    }

    minutely_15_data["temperature_2m"] = minutely_15_temperature_2m
    minutely_15_data["cloud_cover"] = minutely_15_cloud_cover
    minutely_15_data["rain"] = minutely_15_rain
    minutely_15_data["showers"] = minutely_15_showers
    minutely_15_data["snowfall"] = minutely_15_snowfall
    minutely_15_data["snowfall_height"] = minutely_15_snowfall_height

    minutely_15_dataframe = pd.DataFrame(data = minutely_15_data)

    # is_day is hourly resolution; map each 15-min row to its containing hour.
    hourly_dataframe = pd.DataFrame(data = {
        "date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        ),
        "is_day": hourly_is_day
    })

    minutely_15_dataframe = pd.merge_asof(
        minutely_15_dataframe.sort_values("date"),
        hourly_dataframe.sort_values("date"),
        on = "date",
        direction = "backward"
    )

    return minutely_15_dataframe


if __name__ == "__main__":
    weather_dataframe = get_weather(38.951, -92.334)
    print("\n3-Hour Weather Data\n", weather_dataframe)
