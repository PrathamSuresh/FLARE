import traceback

try:
    import rasterio
    import numpy as np
    import pandas as pd

    DEM_PATH = 'data/raw/output_SRTMGL1.tif'

    print("Opening DEM...")
    with rasterio.open(DEM_PATH) as src:
        elev = src.read(1).astype(float)
        transform = src.transform
        res_x = abs(transform[0])
        res_y = abs(transform[4])

    elev[elev < -1000] = np.nan

    print("Computing slope and aspect...")
    dy, dx = np.gradient(elev, res_y * 111320, res_x * 111320)
    slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
    aspect = np.degrees(np.arctan2(-dx, dy)) % 360

    rows, cols = elev.shape
    row_idx, col_idx = np.indices((rows, cols))
    xs, ys = rasterio.transform.xy(transform, row_idx.ravel(), col_idx.ravel())

    df = pd.DataFrame({
        'lat': np.array(ys),
        'lon': np.array(xs),
        'elevation': elev.ravel(),
        'slope': slope.ravel(),
        'aspect': aspect.ravel()
    }).dropna()

    print(f"Raw pixels: {df.shape[0]}")

    # snap to the 0.25 deg IMD rainfall grid
    df['lat'] = (df['lat'] / 0.25).round() * 0.25
    df['lon'] = (df['lon'] / 0.25).round() * 0.25

    grid = df.groupby(['lat', 'lon']).agg(
        elevation=('elevation', 'mean'),
        slope=('slope', 'mean'),
        slope_max=('slope', 'max'),
        aspect=('aspect', 'mean')
    ).reset_index()

    grid.to_csv('data/chamoli_terrain.csv', index=False)
    print(f"Saved {grid.shape[0]} grid cells")
    print(grid.head())

except Exception:
    with open("error_log.txt", "w") as f:
        f.write(traceback.format_exc())
    print("FAILED - see error_log.txt")