// FLARE — Sentinel-1 change detection, Chamoli district
// Event: 2021-02-07 Rishiganga / Dhauliganga debris flow (Joshimath)
//
// GEE's COPERNICUS/S1_GRD is already thermal-noise-removed, calibrated to
// sigma0, and terrain-corrected. Values are in dB.
//
// This version adds the masks the first run showed we needed: elevation,
// slope, and a valley-corridor restriction. Read the Console output top to
// bottom — the diagnostics matter more than the map on a first run.

// ================================================================ parameters
// Tune these three and re-run. Everything else can stay as is.
var THRESHOLD  = -3;      // dB. More negative = stricter. Try -3, -5, -7.
var MAX_ELEV   = 3000;    // m. Above this is snow and ice, not flood.
var MAX_SLOPE  = 15;      // degrees. Water does not pool on cliffs.

// ================================================================ study area
var chamoli    = ee.Geometry.Rectangle([79.0,  30.2,  80.0,  31.0]);

// The 2021 flow ran down the Rishiganga into the Dhauliganga past Raini and
// Tapovan toward Joshimath. Restricting to this corridor removes the entire
// high-altitude snowfield that dominated the first run.
var rishiganga = ee.Geometry.Rectangle([79.55, 30.35, 79.95, 30.60]);

var aoi = chamoli;        // where we search
var focus = rishiganga;   // where we expect the signal

// ===================================================================== dates
var eventDate = ee.Date('2021-02-07');

var preStart  = eventDate.advance(-24, 'day');
var preEnd    = eventDate.advance(-1,  'day');
var postStart = eventDate.advance(1,   'day');
var postEnd   = eventDate.advance(12,  'day');

// =============================================================== collection
var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(aoi)
  .filter(ee.Filter.eq('instrumentMode', 'IW'))
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
  .select('VV');

var around = s1.filterDate(preStart, postEnd);
print('--- coverage ---');
print('Scenes in window:', around.size());
print('Relative orbits available:',
      around.aggregate_array('relativeOrbitNumber_start').distinct());

// ======================================================== same-track pairing
// Only valid within one relative orbit. Ascending and descending passes view
// the terrain from opposite sides; differencing across them compares viewing
// geometry, not ground change.
var ORBIT = 56;

var track = s1.filter(ee.Filter.eq('relativeOrbitNumber_start', ORBIT));
var pre   = track.filterDate(preStart,  preEnd);
var post  = track.filterDate(postStart, postEnd);

print('Pre-event scenes on orbit ' + ORBIT + ':',  pre.size());
print('Post-event scenes on orbit ' + ORBIT + ':', post.size());
print('Pre-event dates:',  pre.aggregate_array('system:time_start')
        .map(function(t) { return ee.Date(t).format('YYYY-MM-dd'); }));
print('Post-event dates:', post.aggregate_array('system:time_start')
        .map(function(t) { return ee.Date(t).format('YYYY-MM-dd'); }));

function despeckle(img) {
  return img.focal_median(30, 'circle', 'meters');
}

var preS  = despeckle(pre.median().clip(aoi));
var postS = despeckle(post.median().clip(aoi));

// ================================================================ difference
// Already dB, so subtraction is the ratio. Negative = surface got darker,
// which is the open-water signature.
var diff = postS.subtract(preS).rename('change_db');

// =================================================================== masking
var dem   = ee.Image('USGS/SRTMGL1_003');
var slope = ee.Terrain.slope(dem);

// Permanent rivers and reservoirs are not floods.
var permanentWater = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
  .select('occurrence').gt(50).unmask(0);

// The first run lit up snowfields above 4000 m near the Tibet border. Fresh
// and wet snow changes backscatter between passes exactly like water does.
// Elevation is the cheapest way to exclude it.
var terrainOK = dem.lt(MAX_ELEV)
  .and(slope.lt(MAX_SLOPE))
  .and(permanentWater.not());

var flooded = diff.lt(THRESHOLD).updateMask(terrainOK).selfMask()
                  .rename('flooded');

// ==================================================================== extent
function areaKm2(mask, region, label) {
  var a = mask.multiply(ee.Image.pixelArea()).reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: region,
    scale: 30,
    maxPixels: 1e10
  });
  print(label, ee.Number(a.values().get(0)).divide(1e6));
}

print('--- detected extent ---');
areaKm2(flooded, aoi,   'Whole district, sq km:');
areaKm2(flooded, focus, 'Rishiganga corridor, sq km:');

// The ratio is the real diagnostic. The corridor is about 4% of the district
// by area. If detections are spread evenly, the corridor share will be near
// that. A genuine flood signal should be far more concentrated there.

// =================================================================== display
Map.centerObject(focus, 11);

Map.addLayer(preS,  {min: -25, max: 0}, 'Pre-event VV (dB)',  false);
Map.addLayer(postS, {min: -25, max: 0}, 'Post-event VV (dB)', false);

// Look at this layer first. Unthresholded change along the valley is the
// honest answer to whether this event left any SAR signature at all. Debris
// can brighten as readily as water darkens, so check both directions.
Map.addLayer(diff, {min: -8, max: 8, palette: ['red', 'white', 'blue']},
             'Change (dB), red = darker', true);

Map.addLayer(dem.gte(MAX_ELEV).selfMask(), {palette: ['dddddd']},
             'Masked: above ' + MAX_ELEV + ' m', false);
Map.addLayer(permanentWater.selfMask(), {palette: ['888888']},
             'Permanent water', false);
Map.addLayer(flooded, {palette: ['00BFFF']}, 'Detected new water', true);

Map.addLayer(ee.Image().paint(ee.FeatureCollection([ee.Feature(focus)]), 0, 2),
             {palette: ['FF6600']}, 'Rishiganga corridor', true);

// ==================================================================== export
// Uncomment, then run from the Tasks tab. Pull the GeoTIFF into GeoPandas for
// the ward overlay.
//
// Export.image.toDrive({
//   image: flooded.unmask(0).toByte(),
//   description: 'chamoli_flood_2021_02_07',
//   folder: 'FLARE',
//   region: aoi,
//   scale: 30,
//   maxPixels: 1e10
// });