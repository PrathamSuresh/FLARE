STEP 1 — Start with Chamoli

For the prototype, we are directly taking Chamoli district, Uttarakhand as our study area.

We collect the available datasets for Chamoli:

Flood inventory
Rainfall
River discharge / water level
Soil moisture
Elevation
Slope
Landslide data
Latitude / longitude
Other relevant environmental/geographical data

The flood inventory acts as our historical flood-event reference.

For example:

Flood Event	Location	Date
Flood 1	Chamoli	Date A
Flood 2	Chamoli	Date B
Flood 3	Chamoli	Date C
STEP 2 — Reconstruct what happened before each historical flood

For every historical flood, we look at the environmental conditions before the event.

For example:

Flood 1
Flood 1
   ↓
Look at conditions before the flood

Rainfall:
- 24 hours before
- 12 hours before
- 6 hours before
- 3 hours before

River:
- water level
- discharge
- rate at which water level/discharge increased

Soil:
- soil moisture / saturation

Terrain:
- elevation
- slope

Landslide:
- nearby landslide activity

So we get:

Flood 1 → these were the environmental conditions leading up to the flood.

Then we do the same for:

Flood 2 → these were the conditions.

Flood 3 → these were the conditions.

And so on.

This is where the ML model learns the temporal patterns.

For example, it may learn that:

high accumulated rainfall + rapidly increasing river discharge + already saturated soil

is a combination frequently associated with flooding.

So we're not just asking:

"Was rainfall high?"

We're looking at:

"How did the conditions change in the hours/days leading up to the flood?"

STEP 3 — Bring in Sentinel-1 for the historical floods

Now we want to know something different.

The flood inventory tells us:

A flood happened here on this date.

The environmental datasets tell us:

These conditions occurred before the flood.

But we also want to know:

WHERE did the water actually spread?

That's where Sentinel-1 comes in.

For each historical flood, we obtain Sentinel-1 imagery around the flood date.

We process the imagery to identify the:

Actual flood inundation extent

Conceptually:

                 CHAMOLI

       ┌──────────────────┐
       │       ███        │
       │       ███        │
       │       █████      │
       │        █████     │
       │          ███     │
       │     RIVER ███    │
       │ ~~~~~~~~~~~~~~~~ │
       └──────────────────┘

          █ = flooded area

So instead of only knowing:

"Chamoli flooded"

we now have a spatial flood footprint showing the areas that were actually inundated.

STEP 4 — Bring in the ward/village GIS boundaries

Now we need to translate that satellite flood footprint into administrative areas.

We obtain the GIS boundaries of the wards/villages in Chamoli.

Then we overlay:

Chamoli ward boundaries
          +
Sentinel-1 flood extent
          ↓
       OVERLAY

Now we can determine:

Which wards were actually affected by each historical flood?

For example:

Flood 1

Ward A ✓
Ward C ✓
Ward D ✓

Flood 2

Ward B ✓
Ward C ✓
Ward D ✓

Flood 3

Ward A ✓
Ward D ✓

STEP 5 — Create the historical ward-level flood dataset

Now we have something extremely useful.

We can create:

Ward	Flood 1	Flood 2	Flood 3	Historical exposure
Ward A	✓	✗	✓	High
Ward B	✗	✓	✗	Medium
Ward C	✓	✓	✗	High
Ward D	✓	✓	✓	Very High

And we don't have to stop at:

Ward C = flooded

We can calculate:

What percentage of Ward C was inundated?

For example:

Flood 1 → 37% of Ward C inundated.

That gives us a much more detailed spatial understanding of historical flooding.

STEP 6 — Train the ward-level model

Now we have two important layers of information.

Layer A — What conditions preceded the flood?

From:

rainfall + river + soil + terrain + landslide + etc.

Layer B — Where did the flood actually occur?

From:

Sentinel-1 flood extent + GIS ward boundaries.

So historically, we have:

ENVIRONMENTAL CONDITIONS
          ↓
       FLOOD EVENT
          ↓
ACTUAL SENTINEL FLOOD EXTENT
          ↓
   AFFECTED WARDS / AREAS

We use many historical events to train the model to understand:

Under these environmental conditions, which types of wards/areas are more likely to become flooded?

The ward model can also use each ward's relatively fixed characteristics, such as:

elevation
slope
distance from river
drainage characteristics
terrain
historical flood exposure
STEP 7 — Now comes TODAY / CURRENT PREDICTION

This is where we actually use the trained model.

Suppose today we collect current data for Chamoli:

Current/recent rainfall
Current/recent river discharge/water level
Current soil moisture
etc.

We feed the current conditions into our model.

The model first tells us:

🔴 Chamoli is currently at high flood risk.

But we don't simply divide Chamoli's probability among its wards.

This is important.

STEP 8 — Calculate probability for each ward

Now we take each ward individually.

For example:

Ward A

We give the model:

Ward A

Current rainfall
+
Current river conditions relevant to Ward A
+
Current soil conditions
+
Ward A elevation
+
Ward A slope
+
Ward A distance from river
+
Ward A drainage characteristics
+
Ward A historical flood characteristics
             ↓
       TRAINED MODEL
             ↓
      Ward A = 82%

Then:

Ward B
Ward B

Current conditions
+
Ward B's geographical characteristics
             ↓
       TRAINED MODEL
             ↓
      Ward B = 35%

Then Ward C, D, E, etc.

STEP 9 — Final current output

So the system could produce:

Location	Current flood probability
Chamoli	High
Ward A	82%
Ward B	35%
Ward C	76%
Ward D	18%

So now we know:

Chamoli is at high risk overall, but Ward A and Ward C are the most likely to be affected.

The most important distinction

We are NOT doing:

Chamoli = 80% flood probability
             ↓
somehow distribute 80%
between the wards

Instead:

CURRENT CONDITIONS
        ↓
      MODEL
        ↓
Chamoli = HIGH RISK
        ↓
Run ward-level prediction
for EACH ward
        ↓
Ward A = 82%
Ward B = 35%
Ward C = 76%
Ward D = 18%

Each ward gets its own prediction based on:

current conditions + that ward's geographical characteristics + what we learned from historical flood events.

So where does Sentinel fit?

This is the cleanest way to remember it:

🟦 Historical Sentinel-1

Used to answer:

"Where did previous floods actually spread?"

That creates our ward-level historical flood labels.

🟨 Current environmental data

Used to answer:

"Given today's conditions, is flooding likely?"

and:

"Which wards are likely to be affected?"

🟥 Sentinel-1 during/after a current flood

If suitable imagery becomes available, Sentinel-1 can answer:

"Where is flooding actually occurring?"

We can then compare:

MODEL PREDICTION
       VS
ACTUAL SENTINEL FLOOD EXTENT

This helps us validate and improve the model.

So the entire prototype in one flow
                    CHAMOLI
                       ↓
              HISTORICAL FLOODS
                       ↓
        ┌──────────────┴──────────────┐
        ↓                             ↓
Environmental datasets          Sentinel-1
        ↓                             ↓
"What happened before?"       "Where did water go?"
        ↓                             ↓
        └──────────────┬──────────────┘
                       ↓
             HISTORICAL DATASET
                       ↓
              TRAIN THE MODEL
                       ↓
              ─────── TODAY ───────
                       ↓
             Current environmental
                   conditions
                       ↓
              Is Chamoli at risk?
                       ↓
                  YES → HIGH
                       ↓
            Run prediction for
              EVERY WARD
                       ↓
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       Ward A        Ward B       Ward C
        82%           35%           76%
          ↓            ↓            ↓
          └────────────┼────────────┘
                       ↓
             WARD-LEVEL RISK MAP
                       ↓
          Potential high-risk zones
                       ↓
       Sentinel-1 when available
                       ↓
          Actual flood extent
                       ↓
            Compare + validate
In one sentence:

We use historical flood inventories and environmental data to learn what conditions precede floods, use historical Sentinel-1 imagery to determine where those floods actually spread and which wards were affected, train a ward-level model using this information, and then use today's environmental conditions to predict the flood probability of each ward in Chamoli.

That is the core prototype.