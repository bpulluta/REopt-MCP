# Tech-Models Bundle

## Bundle Summary

- Documents: 1
- Chunks: 2

## Document Index

- 1. REopt.jl (https://natlabrockies.github.io/REopt.jl/dev/)

## Documents

### 1. REopt.jl

Source: https://natlabrockies.github.io/REopt.jl/dev/

#### REopt.jl

REopt.jl is the core module of the REopt® techno-economic decision support platform, developed by the National Laboratory of the Rockies (NLR). REopt optimizes the sizing and dispatch of integrated energy systems for buildings, campuses, communities, microgrids, and more. REopt identifies the cost-optimal mix of generation, storage, and heating and cooling technologies to meet cost savings, resilience, emissions reductions, and energy performance goals. The open-source REopt.jl code is available on GitHub: https://github.com/NatLabRockies/REopt.jl.

#### Add NLR developer API key for PV, CST, and Wind

If you don't have an NLR developer network API key, sign up here on https://developer.nlr.gov to get one (free); this is required to load PV and Wind resource profiles from PVWatts and the Wind Toolkit APIs from within REopt.jl. Assign your API key to the expected environment variable:

```
ENV["NREL_DEVELOPER_API_KEY"]="your API key"
```

before running PV or Wind scenarios, and also assign your email to the expected environment variable as well before running CST scenarios:

```
ENV["NREL_DEVELOPER_EMAIL"]="your contact email"
```
