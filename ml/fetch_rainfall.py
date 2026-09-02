import traceback

try:
    import imdlib as imd

    LAT_MIN, LAT_MAX = 30.2, 31.0
    LON_MIN, LON_MAX = 79.0, 80.0

    print("Starting download...")
    imd.get_data('rain', 2010, 2021, fn_format='yearwise')
    print("Download step finished.")

    data = imd.open_data('rain', 2010, 2021, 'yearwise')
    df = data.get_xarray().to_dataframe().reset_index()

    df = df[df['rain'] > -100]
    df = df[
        (df['lat'].between(LAT_MIN, LAT_MAX)) &
        (df['lon'].between(LON_MIN, LON_MAX))
    ]

    df.to_csv('data/chamoli_rainfall_2010_2021.csv', index=False)
    print(f"Saved {df.shape[0]} rows")
    print(df.head())

except Exception as e:
    with open("error_log.txt", "w") as f:
        f.write("ERROR OCCURRED:\n")
        f.write(traceback.format_exc())
    print("FAILED - see error_log.txt")