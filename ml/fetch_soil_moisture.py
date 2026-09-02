import traceback

try:
    import cdsapi
    import xarray as xr
    import pandas as pd
    import os
    import glob

    os.makedirs('data/raw/soil', exist_ok=True)

    MONTHS = [f"{m:02d}" for m in range(1, 13)]
    DAYS = [f"{d:02d}" for d in range(1, 32)]

    client = cdsapi.Client()

    for year in range(2010, 2022):
        out = f'data/raw/soil/soil_{year}.nc'
        if os.path.exists(out):
            print(f"{year}: already downloaded, skipping")
            continue

        print(f"{year}: requesting...")
        client.retrieve(
            "reanalysis-era5-land",
            {
                "variable": [
                    "volumetric_soil_water_layer_1",
                    "volumetric_soil_water_layer_2",
                ],
                "year": str(year),
                "month": MONTHS,
                "day": DAYS,
                "time": ["00:00", "12:00"],
                "area": [31.0, 79.0, 30.2, 80.0],   # N, W, S, E
                "data_format": "netcdf",
                "download_format": "unarchived",
            },
        ).download(out)
        print(f"{year}: done")

    print("Processing all years...")
    files = sorted(glob.glob('data/raw/soil/soil_*.nc'))
    frames = []

    for f in files:
        ds = xr.open_dataset(f)
        d = ds.to_dataframe().reset_index()
        frames.append(d)
        ds.close()

    df = pd.concat(frames, ignore_index=True)

    time_col = 'valid_time' if 'valid_time' in df.columns else 'time'
    df['date'] = pd.to_datetime(df[time_col]).dt.date

    daily = df.groupby(['date', 'latitude', 'longitude']).agg(
        soil_moisture_l1=('swvl1', 'mean'),
        soil_moisture_l2=('swvl2', 'mean')
    ).reset_index()

    daily = daily.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
    daily['lat'] = (daily['lat'] / 0.25).round() * 0.25
    daily['lon'] = (daily['lon'] / 0.25).round() * 0.25

    grid = daily.groupby(['date', 'lat', 'lon']).mean().reset_index()
    grid.to_csv('data/chamoli_soil_moisture.csv', index=False)

    print(f"Saved {grid.shape[0]} rows")
    print(grid.head())

except Exception:
    with open("error_log.txt", "w") as f:
        f.write(traceback.format_exc())
    print("FAILED - see error_log.txt")