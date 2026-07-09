# Inputs

Source: https://natlabrockies.github.io/REopt.jl/dev/reopt/inputs/

# Inputs

Inputs to the `run_reopt` function can be provided in one of four formats:

1. a file path (string) to a JSON file,
2. a `Dict`,
3. using the `Scenario` struct, or
4. using the `REoptInputs` struct

Any one of these types can be passed to the run\_reopt method as shown in Examples.

The first option is perhaps the most straightforward. For example, the minimum requirements for a JSON scenario file would look like:

```
{
    "Site": {
        "longitude": -118.1164613,
        "latitude": 34.5794343
    },
    "ElectricLoad": {
        "doe_reference_name": "MidriseApartment",
        "annual_kwh": 1000000.0
    },
    "ElectricTariff": {
        "urdb_label": "5ed6c1a15457a3367add15ae"
    }
}
```

The order of the keys does not matter. Note that this scenario does not include any energy generation technologies and therefore the results can be used as a baseline for comparison to scenarios that result in cost-optimal generation technologies (alternatively, a user could include a BAUScenario as shown in Examples).

To add PV to the analysis simply add a PV key with an empty dictionary (to use default values):

```
{
    "Site": {
        "longitude": -118.1164613,
        "latitude": 34.5794343
    },
    "ElectricLoad": {
        "doe_reference_name": "MidriseApartment",
        "annual_kwh": 1000000.0
    },
    "ElectricTariff": {
        "urdb_label": "5ed6c1a15457a3367add15ae"
    },
    "PV": {}
}
```

This scenario will consider the option to purchase a solar PV system to reduce energy costs, and if solar PV can reduce the energy costs then REopt will provide the optimal PV capacity (assuming perfect foresight!). See PV for all available input keys and default values for `PV`. To override a default value, simply specify a value for a given key. For example, the site under consideration might have some existing PV capacity to account for, which can be done by setting the `existing_kw` key to the appropriate value.

## Scenario

The `Scenario` struct captures all of the possible user input keys (see Inputs for potential input formats). A Scenario struct will be automatically created if a `Dict` or file path are supplied to the run\_reopt method. Alternatively, a user can create a `Scenario` struct and supply this to run\_reopt.

`REopt.Scenario` — Type
```
Scenario(d::Dict; flex_hvac_from_json=false)
```

A Scenario struct can contain the following keys:

- Site (required)
- Financial (optional)
- ElectricTariff (required when `off_grid_flag=false`)
- ElectricLoad (required)
- PV (optional, can be Array)
- Wind (optional)
- ElectricStorage (optional)
- HotThermalStorage (optional)
- HighTempThermalStorage (optional)
- ColdThermalStorage (optional)
- ElectricStorage (optional)
- ElectricUtility (optional)
- Generator (optional)
- HeatingLoad (optional)
- CoolingLoad (optional)
- ExistingBoiler (optional)
- Boiler (optional)
- CHP (optional)
- FlexibleHVAC (optional)
- ExistingChiller (optional)
- AbsorptionChiller (optional)
- GHP (optional, can be Array)
- SteamTurbine (optional)
- ElectricHeater (optional)
- CST (optional)
- ASHPSpaceHeater (optional)
- ASHPWaterHeater (optional)

All values of `d` are expected to be `Dicts` except for `PV` and `GHP`, which can be either a `Dict` or `Dict[]` (for multiple PV arrays or GHP options).

source
```
Scenario(fp::String)
```

Consruct Scenario from filepath `fp` to JSON with keys aligned with the `Scenario(d::Dict)` method.

source
## BAUScenario

The Business-as-usual (BAU) inputs are automatically created based on the `BAUScenario` struct when a user supplies two `JuMP.Model`s to `run_reopt()` (as shown in Examples). The outputs of the BAU scenario are used to calculate comparative results such as the `Financial` net present value (`npv`).

`REopt.BAUInputs` — Function
```
BAUInputs(p::REoptInputs)
```

The`BAUInputs` (REoptInputs for the Business As Usual scenario) are created based on the `BAUScenario`, which is in turn created based on the optimized-case `Scenario`.

The following assumptions are made for the BAU Inputs:

- `PV` and `Generator` `min_kw` and `max_kw` set to the `existing_kw` values
- `ExistingBoiler` and `ExistingChiller` # TODO
- All other generation and storage tech sizes set to zero
- Capital costs are assumed to be zero for existing `PV` and `Generator`
- O&M costs and all other tech inputs are assumed to be the same for existing `PV` and `Generator` as those specified for the optimized case
- Outage assumptions for deterministic vs stochastic # TODO
source
## Settings

`REopt.Settings` — Type

Captures high-level inputs affecting the optimization.

`Settings` is an optional REopt input with the following keys and default values:

```
    time_steps_per_hour::Int = 1 # corresponds to the time steps per hour for user-provided time series (e.g., `ElectricLoad.loads_kw` and `DomesticHotWaterLoad.fuel_loads_mmbtu_per_hour`)
    add_soc_incentive::Bool = true # when true, an incentive is added to the model's objective function to keep the ElectricStorage SOC high
    off_grid_flag::Bool = false # true if modeling an off-grid system, not connected to bulk power system
    include_climate_in_objective::Bool = false # true if climate costs of emissions should be included in the model's objective function
    include_health_in_objective::Bool = false # true if health costs of emissions should be included in the model's objective function
    solver_name::String = "HiGHS" # solver used to obtain a solution to model instance. available options: ["HiGHS", "Cbc", "CPLEX", "Xpress"]
```
source
## Site

`REopt.Site` — Type

Inputs related to the physical location:

`Site` is a required REopt input with the following keys and default values:

```
    latitude::Real,
    longitude::Real,
    land_acres::Union{Real, Nothing} = nothing, # acres of land available for PV panels and/or Wind turbines. Constraint applied separately to PV and Wind, meaning the two technologies are assumed to be able to be co-located.
    roof_squarefeet::Union{Real, Nothing} = nothing,
    min_resil_time_steps::Int=0, # The minimum number consecutive timesteps that load must be fully met once an outage begins. Only applies to multiple outage modeling using inputs outage_start_time_steps and outage_durations.
    mg_tech_sizes_equal_grid_sizes::Bool = true,
    sector::String = "commercial/industrial", # available options: ["commercial/industrial", "federal"]
    federal_sector_state::String = "",
    federal_procurement_type::String = "",
    CO2_emissions_reduction_min_fraction::Union{Float64, Nothing} = nothing,
    CO2_emissions_reduction_max_fraction::Union{Float64, Nothing} = nothing,
    bau_emissions_lb_CO2_per_year::Union{Float64, Nothing} = nothing, # Auto-populated based on BAU run. This input will be overwritten if the BAU scenario is run, but can be user-provided if no BAU scenario is run.
    bau_grid_emissions_lb_CO2_per_year::Union{Float64, Nothing} = nothing,
    renewable_electricity_min_fraction::Union{Float64, Nothing} = nothing,
    renewable_electricity_max_fraction::Union{Float64, Nothing} = nothing,
    include_grid_renewable_fraction_in_RE_constraints::Bool = false,
    include_exported_elec_emissions_in_total::Bool = true,
    include_exported_renewable_electricity_in_total::Bool = true,
    outdoor_air_temperature_degF::Union{Nothing, Array{<:Real,1}} = nothing,
    node::Int = 1,
```
source
## ElectricLoad

`REopt.ElectricLoad` — Type

`ElectricLoad` is a required REopt input with the following keys and default values:

```
    loads_kw::Array{<:Real,1} = Real[],
    normalize_and_scale_load_profile_input::Bool = false,  # Takes loads_kw and normalizes and scales it to annual_kwh, monthly_totals_kwh, or monthly_peaks_kw
    path_to_csv::String = "", # for csv containing loads_kw
    doe_reference_name::String = "",
    blended_doe_reference_names::Array{String, 1} = String[],
    blended_doe_reference_percents::Array{<:Real,1} = Real[], # Values should be between 0-1 and sum to 1.0
    year::Union{Int, Nothing} = doe_reference_name ≠ "" || blended_doe_reference_names ≠ String[] ? 2017 : nothing, # used in ElectricTariff to align rate schedule with weekdays/weekends. DOE CRB profiles defaults to using 2017. If providing load data, specify year of data.
    city::String = "",
    annual_kwh::Union{Real, Nothing} = nothing, # scales the load profile to this annual energy. Can apply to either loads_kw (if normalize_and_scale_load_profile_input=true) or doe_reference loads
    monthly_totals_kwh::Array{<:Real,1} = Real[], # scales the load profile to these monthly energy totals. Must provide 12 values. Can apply to either loads_kw (if normalize_and_scale_load_profile_input=true) or doe_reference loads
    monthly_peaks_kw::Array{<:Real,1} = Real[], # scales the load profile to these monthly peak loads. Can apply to either loads_kw (if normalize_and_scale_load_profile_input=true) or doe_reference loads
    critical_loads_kw::Union{Nothing, Array{Real,1}} = nothing,
    loads_kw_is_net::Bool = true, # set to true if loads_kw is already net of on-site electricity generation.
    critical_loads_kw_is_net::Bool = false, # set to true if critical_loads_kw is already net of on-site electricity generation.
    critical_load_fraction::Real = off_grid_flag ? 1.0 : 0.5, # fractional input is applied to the typical load profile to determine critical loads.
    operating_reserve_required_fraction::Real = off_grid_flag ? 0.1 : 0.0, # if off grid, 10%, else must be 0%. Applied to each time_step as a % of electric load.
    min_load_met_annual_fraction::Real = off_grid_flag ? 0.99999 : 1.0 # if off grid, 99.999%, else must be 100%. Applied to each time_step as a % of electric load.
```
source
## ElectricTariff

`REopt.ElectricTariff` — Method

`ElectricTariff` is a required REopt input for on-grid scenarios only (it cannot be supplied when `Settings.off_grid_flag` is true) with the following keys and default values:

```
    urdb_label::String="",
    urdb_response::Dict=Dict(), # Response JSON for URDB rates. Note: if creating your own urdb_response, ensure periods are zero-indexed.
    urdb_utility_name::String="",
    urdb_rate_name::String="",
    urdb_metadata::Dict=Dict(), # Meta data about the URDB rate, from the URDB API response
    wholesale_rate::T1=nothing, # Price of electricity sold back to the grid in absence of net metering. Can be a scalar value, which applies for all-time, or an array with time-sensitive values. If an array is input then it must have a length of 8760, 17520, or 35040. The inputed array values are up/down-sampled using mean values to match the Settings.time_steps_per_hour.
    export_rate_beyond_net_metering_limit::T2=nothing, # Price of electricity sold back to the grid beyond total annual grid purchases, regardless of net metering. Can be a scalar value, which applies for all-time, or an array with time-sensitive values. If an array is input then it must have a length of 8760, 17520, or 35040. The inputed array values are up/down-sampled using mean values to match the Settings.time_steps_per_hour
    monthly_energy_rates::Array=[], # Array (length of 12) of blended energy rates in dollars per kWh
    monthly_demand_rates::Array=[], # Array (length of 12) of blended demand charges in dollars per kW
    blended_annual_energy_rate::S=nothing, # Annual blended energy rate [$ per kWh] (total annual energy in kWh divided by annual cost in dollars)
    blended_annual_demand_rate::R=nothing, # Average monthly demand charge [$ per kW per month]. Rate will be applied to monthly peak demand.
    add_monthly_rates_to_urdb_rate::Bool=false, # Set to 'true' to add the monthly blended energy rates and demand charges to the URDB rate schedule. Otherwise, blended rates will only be considered if a URDB rate is not provided.
    tou_energy_rates_per_kwh::Array=[], # Time-of-use energy rates, provided by user. Must be an array with length equal to number of timesteps per year.
    add_tou_energy_rates_to_urdb_rate::Bool=false, # Set to 'true' to add the tou  energy rates to the URDB rate schedule. Otherwise, tou energy rates will only be considered if a URDB rate is not provided.
    remove_tiers::Bool=false,
    demand_lookback_months::AbstractArray{Int64, 1}=Int64[], # Array of 12 binary values, indicating months in which `demand_lookback_percent` applies. If any of these is true, `demand_lookback_range` should be zero.
    demand_lookback_percent::Real=0.0, # Lookback percentage. Applies to either `demand_lookback_months` with value=1, or months in `demand_lookback_range`.
    demand_lookback_range::Int=0, # Number of months for which `demand_lookback_percent` applies. If not 0, `demand_lookback_months` should not be supplied.
    coincident_peak_load_active_time_steps::Vector{Vector{Int64}}=[Int64[]], # The optional coincident_peak_load_charge_per_kw will apply at the max grid-purchased power during these timesteps. Note timesteps are indexed to a base of 1 not 0.
    coincident_peak_load_charge_per_kw::AbstractVector{<:Real}=Real[] # Optional coincident peak demand charge that is applied to the max load during the timesteps specified in coincident_peak_load_active_time_steps.
    ) where {
        T1 <: Union{Nothing, Real, Array{<:Real}},
        T2 <: Union{Nothing, Real, Array{<:Real}},
        S <: Union{Nothing, Real},
        R <: Union{Nothing, Real}
    }
```
source
## Financial

`REopt.Financial` — Type

`Financial` is an optional REopt input with the following keys and default values:

```
    om_cost_escalation_rate_fraction::Real = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, federal_sector_state=federal_sector_state, struct_name="Financial"), "om_cost_escalation_rate_fraction", 0.025),
    elec_cost_escalation_rate_fraction::Real = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, federal_sector_state=federal_sector_state, struct_name="Financial"), "elec_cost_escalation_rate_fraction", 0.0166),
    existing_boiler_fuel_cost_escalation_rate_fraction::Real = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, federal_sector_state=federal_sector_state, struct_name="Financial"), "existing_boiler_fuel_cost_escalation_rate_fraction", 0.0348),
    boiler_fuel_cost_escalation_rate_fraction::Real = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, federal_sector_state=federal_sector_state, struct_name="Financial"), "boiler_fuel_cost_escalation_rate_fraction", 0.0348),
    chp_fuel_cost_escalation_rate_fraction::Real = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, federal_sector_state=federal_sector_state, struct_name="Financial"), "chp_fuel_cost_escalation_rate_fraction", 0.0348),
    generator_fuel_cost_escalation_rate_fraction::Real = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, federal_sector_state=federal_sector_state, struct_name="Financial"), "generator_fuel_cost_escalation_rate_fraction", 0.0197),
    offtaker_tax_rate_fraction::Real = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, federal_sector_state=federal_sector_state, struct_name="Financial"), "offtaker_tax_rate_fraction", 0.26),
    offtaker_discount_rate_fraction::Real = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, federal_sector_state=federal_sector_state, struct_name="Financial"), "offtaker_discount_rate_fraction", 0.0624),
    third_party_ownership::Real = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, federal_sector_state=federal_sector_state, struct_name="Financial"), "third_party_ownership", false),
    owner_tax_rate_fraction::Real = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, federal_sector_state=federal_sector_state, struct_name="Financial"), "owner_tax_rate_fraction", 0.26),
    owner_discount_rate_fraction::Real = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, federal_sector_state=federal_sector_state, struct_name="Financial"), "owner_discount_rate_fraction", 0.0624),
    analysis_years::Int = 25,
    value_of_lost_load_per_kwh::Union{Array{R,1}, R} where R<:Real = 1.00, #only applies to multiple outage modeling
    microgrid_upgrade_cost_fraction::Real = 0.0
    macrs_five_year::Array{Float64,1} = [0.2, 0.32, 0.192, 0.1152, 0.1152, 0.0576],  # IRS pub 946
    macrs_seven_year::Array{Float64,1} = [0.1429, 0.2449, 0.1749, 0.1249, 0.0893, 0.0892, 0.0893, 0.0446],
    offgrid_other_capital_costs::Real = 0.0, # only applicable when `off_grid_flag` is true. Straight-line depreciation is applied to this capex cost, reducing taxable income.
    offgrid_other_annual_costs::Real = 0.0 # only applicable when `off_grid_flag` is true. Considered tax deductible for owner. Costs are per year.
    min_initial_capital_costs_before_incentives::Union{Nothing,Real} = nothing # minimum up-front capital cost for all technologies, excluding replacement costs and incentives.
    max_initial_capital_costs_before_incentives::Union{Nothing,Real} = nothing # maximum up-front capital cost for all technologies, excluding replacement costs and incentives.
    # Emissions cost inputs
    CO2_cost_per_tonne::Real = 51.0,
    CO2_cost_escalation_rate_fraction::Real = 0.042173,
    NOx_grid_cost_per_tonne::Union{Nothing,Real} = nothing,
    SO2_grid_cost_per_tonne::Union{Nothing,Real} = nothing,
    PM25_grid_cost_per_tonne::Union{Nothing,Real} = nothing,
    NOx_onsite_fuelburn_cost_per_tonne::Union{Nothing,Real} = nothing, # Default data from EASIUR based on location
    SO2_onsite_fuelburn_cost_per_tonne::Union{Nothing,Real} = nothing, # Default data from EASIUR based on location
    PM25_onsite_fuelburn_cost_per_tonne::Union{Nothing,Real} = nothing, # Default data from EASIUR based on location
    NOx_cost_escalation_rate_fraction::Union{Nothing,Real} = nothing, # Default data from EASIUR based on location
    SO2_cost_escalation_rate_fraction::Union{Nothing,Real} = nothing, # Default data from EASIUR based on location
    PM25_cost_escalation_rate_fraction::Union{Nothing,Real} = nothing # Default data from EASIUR based on location
```
source
## ElectricUtility

`REopt.ElectricUtility` — Type

`ElectricUtility` is an optional REopt input with the following keys and default values:

```
    net_metering_limit_kw::Real = 0, # Upper limit on the total capacity of technologies that can participate in net metering agreement.
    interconnection_limit_kw::Real = 1.0e9, # Limit on total electric system capacity size that can be interconnected to the grid
    allow_simultaneous_export_import::Bool = true,  # if true the site has two meters (in effect). Set to false if the export rate is greater than the cost of energy (otherwise, REopt will export before meeting site load).

    # Single Outage Modeling Inputs (Outage Modeling Option 1):
    outage_start_time_step::Int=0,  # for modeling a single outage, with critical load spliced into the baseline load ...
    outage_end_time_step::Int=0,  # ... utility production_factor = 0 during the outage

    # Multiple Outage Modeling Inputs (Outage Modeling Option 2):
    # minimax the expected outage cost, with max taken over outage start time, expectation taken over outage duration
    outage_start_time_steps::Array{Int,1}=Int[],  # we minimize the maximum outage cost over outage start times
    outage_durations::Array{Int,1}=Int[],  # One-to-one with outage_probabilities. Outage_durations can be a random variable, and should be in timesteps aligning with time_steps_per_hour (e.g., duration of 4 equates to 1 hour if time_steps_per_hour is 4)
    outage_probabilities::Array{R,1} where R<:Real = [1.0],

    ### Cambium Emissions and Clean Energy Inputs ###
    cambium_scenario::String = "Mid-case", # Cambium Scenario for evolution of electricity sector (see Cambium documentation for descriptions).
        ## Options: ["Mid-case", "Low renewable energy cost",   "High renewable energy cost", "High demand growth",  "Low natural gas prices", "High natural gas prices", "Mid-case with 95% decarbonization by 2050",  "Mid-case with 100% decarbonization by 2035"]
    cambium_location_type::String =  "GEA Regions 2023", # Geographic boundary at which emissions and clean energy fraction are calculated. Options: ["Nations", "GEA Regions 2023"]
    cambium_start_year::Int = 2025, # First year of operation of system. Emissions and clean energy fraction will be levelized starting in this year for the duration of cambium_levelization_years. # Options: any year 2025 through 2050.
    cambium_levelization_years::Int = analysis_years, # Expected lifetime or analysis period of the intervention being studied. Emissions and clean energy fraction will be averaged over this period.
    cambium_grid_level::String = "enduse", # Options: ["enduse", "busbar"]. Busbar refers to point where bulk generating stations connect to grid; enduse refers to point of consumption (includes distribution loss rate).

    ### Grid Climate Emissions Inputs ###
    # Climate Option 1 (Default): Use levelized emissions data from NLR's Cambium database by specifying the following fields:
    cambium_co2_metric::String = "lrmer_co2e", # Emissions metric used. Default: "lrmer_co2e" - Long-run marginal emissions rate for CO2-equivalant, combined combustion and pre-combustion emissions rates. Options: See metric definitions and names in the Cambium documentation

    # Climate Option 2: Use CO2 emissions data from the EPA's AVERT based on the AVERT emissions region and specify annual percent decrease
    co2_from_avert::Bool = false, # Default is to use Cambium data for CO2 grid emissions. Set to `true` to instead use data from the EPA's AVERT database.

    # Climate Option 3: Provide your own custom emissions factors for CO2 and specify annual percent decrease
    emissions_factor_series_lb_CO2_per_kwh::Union{Real,Array{<:Real,1}} = Float64[], # Custom CO2 emissions profile. Can be scalar or timeseries (aligned with time_steps_per_hour). Ensure emissions year aligns with load year.

    # Used with Climate Options 2 or 3: Annual percent decrease in CO2 emissions factors
    emissions_factor_CO2_decrease_fraction::Union{Nothing, Real} = co2_from_avert || length(emissions_factor_series_lb_CO2_per_kwh) > 0  ? EMISSIONS_DECREASE_DEFAULTS["CO2e"] : nothing , # Annual percent decrease in the total annual CO2 emissions rate of the grid. A negative value indicates an annual increase.

    ### Grid Health Emissions Inputs ###
    # Health Option 1 (Default): Use health emissions data from the EPA's AVERT based on the AVERT emissions region and specify annual percent decrease
    avert_emissions_region::String = "", # AVERT emissions region. Default is based on location, or can be overriden by providing region here.

    # Health Option 2: Provide your own custom emissions factors for health emissions and specify annual percent decrease:
    emissions_factor_series_lb_NOx_per_kwh::Union{Real,Array{<:Real,1}} = Float64[], # Custom NOx emissions profile. Can be scalar or timeseries (aligned with time_steps_per_hour). Ensure emissions year aligns with load year.
    emissions_factor_series_lb_SO2_per_kwh::Union{Real,Array{<:Real,1}} = Float64[], # Custom SO2 emissions profile. Can be scalar or timeseries (aligned with time_steps_per_hour). Ensure emissions year aligns with load year.
    emissions_factor_series_lb_PM25_per_kwh::Union{Real,Array{<:Real,1}} = Float64[], # Custom PM2.5 emissions profile. Can be scalar or timeseries (aligned with time_steps_per_hour). Ensure emissions year aligns with load year.

    # Used with Health Options 1 or 2: Annual percent decrease in health emissions factors:
    emissions_factor_NOx_decrease_fraction::Real = EMISSIONS_DECREASE_DEFAULTS["NOx"],
    emissions_factor_SO2_decrease_fraction::Real = EMISSIONS_DECREASE_DEFAULTS["SO2"],
    emissions_factor_PM25_decrease_fraction::Real = EMISSIONS_DECREASE_DEFAULTS["PM25"]

    ### Grid Clean Energy Fraction Inputs ###
    cambium_cef_metric::String = "cef_load", # Options = ["cef_load", "cef_gen"] # cef_load is the fraction of generation that is clean, for the generation that is allocated to a region’s end-use load; cef_gen is the fraction of generation that is clean within a region
    renewable_energy_fraction_series::Union{Real,Array{<:Real,1}} = Float64[], # Fraction of energy supplied by the grid that is renewable. Can be scalar or timeseries (aligned with time_steps_per_hour)
```
source
## PV

`REopt.PV` — Type

`PV` is an optional REopt input with the following keys and default values:

```
    array_type::Int=1, # PV Watts array type (0: Ground Mount Fixed (Open Rack); 1: Rooftop, Fixed; 2: Ground Mount 1-Axis Tracking; 3 : 1-Axis Backtracking; 4: Ground Mount, 2-Axis Tracking)
    tilt::Real = (array_type == 0 || array_type == 1) ? 20 : 0, # tilt = 20 for fixed rooftop arrays (1) or ground-mount (2) ; tilt = 0 for everything else (3 and 4)
    module_type::Int=0, # PV module type (0: Standard; 1: Premium; 2: Thin Film)
    losses::Real=0.14, # System losses
    azimuth::Real = latitude≥0 ? 180 : 0, # set azimuth to zero for southern hemisphere
    gcr::Real=0.4,  # Ground coverage ratio
    radius::Int=0, # Radius, in miles, to use when searching for the closest climate data station. Use zero to use the closest station regardless of the distance
    name::String="PV", # for use with multiple pvs
    location::String="both", # one of ["roof", "ground", "both"]
    existing_kw::Real=0,
    min_kw::Real=0,
    max_kw::Real=1.0e9, # max new DC capacity (beyond existing_kw)
    installed_cost_per_kw::Union{Real, AbstractVector{<:Real}} = Float64[], # defaults to avg_installed_cost_per_kw for the determined size class as specified in data/pv/pv_defaults.json. Note that mount_premium scaling factors are applied for ground-mount systems based on array_type.
    om_cost_per_kw::Real=18.0,
    degradation_fraction::Real=0.005,
    macrs_option_years::Int = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, struct_name="PV"), "macrs_option_years", 5),
    macrs_bonus_fraction::Real = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, struct_name="PV"), "macrs_bonus_fraction", 1.0),
    macrs_itc_reduction::Real = 0.5,
    kw_per_square_foot::Real=0.01,
    acres_per_kw::Real=6e-3,
    inv_eff::Real=0.96,
    dc_ac_ratio::Real=1.2,
    production_factor_series::Union{Nothing, Array{<:Real,1}} = nothing, # Optional user-defined production factors. Must be normalized to units of kW-AC/kW-DC nameplate. The series must be one year (January through December) of hourly, 30-minute, or 15-minute generation data.
    federal_itc_fraction::Real = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, struct_name="PV"), "federal_itc_fraction", 0.3),
    federal_rebate_per_kw::Real = 0.0,
    state_ibi_fraction::Real = 0.0,
    state_ibi_max::Real = 1.0e10,
    state_rebate_per_kw::Real = 0.0,
    state_rebate_max::Real = 1.0e10,
    utility_ibi_fraction::Real = 0.0,
    utility_ibi_max::Real = 1.0e10,
    utility_rebate_per_kw::Real = 0.0,
    utility_rebate_max::Real = 1.0e10,
    production_incentive_per_kwh::Float64 = 0.0 # revenue from production incentive per kWh electricity produced, including curtailment
    production_incentive_max_benefit::Float64 = 1.0e9 # maximum allowable annual revenue from production incentives
    production_incentive_years::Int = 1 # number of year in which production incentives are paid
    production_incentive_max_kw::Float64 = 1.0e9 # maximum allowable system size to receive production incentives
    can_net_meter::Bool = off_grid_flag ? false : true,
    can_wholesale::Bool = off_grid_flag ? false : true,
    can_export_beyond_nem_limit::Bool = off_grid_flag ? false : true,
    can_curtail::Bool = true,
    operating_reserve_required_fraction::Real = off_grid_flag ? 0.25 : 0.0, # if off grid, 25%, else 0%. Applied to each time_step as a % of PV generation.
    size_class::Union{Int, Nothing} = nothing, # Size class for cost curve selection
    tech_sizes_for_cost_curve::AbstractVector = Float64[], # System sizes for detailed cost curve
    use_detailed_cost_curve::Bool = false, # Use detailed cost curve instead of average cost
    electric_load_annual_kwh::Real = 0.0, # Annual electric load (kWh) for size class determination
    site_land_acres::Union{Real, Nothing} = nothing,  # site.land_acres to determine size_class if space constraineed
    site_roof_squarefeet::Union{Real, Nothing} = nothing  # site.roof_squarefeet to determine size_class if space constraineed
```

When using 'use*detailed*cost*curve' is set to `true`, and providing specific values for `tech*sizes*for*cost*curve`and`installed*cost*per*kw`, both`tech*sizes*for*cost*curve`and`installed*cost*per*kw` must have the same length. Size class is automatically determined based on average load if not specified, which affects default costs. Ground-mount('array*type' = 0,2,3,4) systems have different cost structures than rooftop ('array\_type' = 1) systems when using default values.

source
## Wind

`REopt.Wind` — Type

`Wind` is an optional REopt input with the following keys and default values:

```
    min_kw = 0.0,
    max_kw = 1.0e9,
    installed_cost_per_kw = nothing,
    om_cost_per_kw = 42.0,
    production_factor_series = nothing, # Optional user-defined production factors. Must be normalized to units of kW-AC/kW-DC nameplate. The series must be one year (January through December) of hourly, 30-minute, or 15-minute generation data.
    size_class = "",
    wind_meters_per_sec = [],
    wind_direction_degrees = [],
    temperature_celsius = [],
    pressure_atmospheres = [],
    acres_per_kw = 0.03, # assuming a power density of 30 acres per MW for turbine sizes >= 1.5 MW. No size constraint applied to turbines below 1.5 MW capacity. (not exposed in API)
    macrs_option_years = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, struct_name="Wind"), "macrs_option_years", 5),
    macrs_bonus_fraction = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, struct_name="Wind"), "macrs_bonus_fraction", 1.0),
    macrs_itc_reduction = 0.5,
    federal_itc_fraction = get(get_sector_defaults(; sector=sector, federal_procurement_type=federal_procurement_type, struct_name="Wind"), "federal_itc_fraction", 0.3),
    federal_rebate_per_kw = 0.0,
    state_ibi_fraction = 0.0,
    state_ibi_max = 1.0e10,
    state_rebate_per_kw = 0.0,
    state_rebate_max = 1.0e10,
    utility_ibi_fraction = 0.0,
    utility_ibi_max = 1.0e10,
    utility_rebate_per_kw = 0.0,
    utility_rebate_max = 1.0e10,
    production_incentive_per_kwh::Float64 = 0.0 # revenue from production incentive per kWh electricity produced, including curtailment
    production_incentive_max_benefit::Float64 = 1.0e9 # maximum allowable annual revenue from production incentives
    production_incentive_years::Int = 1 # number of year in which production incentives are paid
    production_incentive_max_kw::Float64 = 1.0e9 # maximum allowable system size to receive production incentives
    can_net_meter = true,
    can_wholesale = true,
    can_export_beyond_nem_limit = true
    operating_reserve_required_fraction::Real = off_grid_flag ? 0.50 : 0.0, # Only applicable when `off_grid_flag` is true. Applied to each time_step as a % of wind generation serving load.
```
source
## ElectricStorage

`REopt.ElectricStorageDefaults` — Type

`ElectricStorage` is an optional optional REopt input with the following keys and default values:

```
    min_kw::Real = 0.0
    max_kw::Real = 1.0e4
    min_kwh::Real = 0.0
    max_kwh::Real = 1.0e6
    internal_efficiency_fraction::Float64 = 0.975
    inverter_efficiency_fraction::Float64 = 0.96
    rectifier_efficiency_fraction::Float64 = 0.96
    soc_min_fraction::Float64 = 0.2
    soc_min_applies_during_outages::Bool = false
    soc_init_fraction::Float64 = off_grid_flag ? 1.0 : 0.5
    can_grid_charge::Bool = off_grid_flag ? false : true
    installed_cost_per_kw::Real = 968.0 # Cost of power components (e.g., inverter and BOS)
    installed_cost_per_kwh::Real = 253.0 # Cost of energy components (e.g., battery pack)
    installed_cost_constant::Real = 222115.0 # "+c" constant cost that is added to total ElectricStorage installed costs if a battery is included. Accounts for costs not expected to scale with power or energy capacity.
    replace_cost_per_kw::Real = 0.0
    replace_cost_per_kwh::Real = 0.0
    replace_cost_constant::Real = 0.0
    inverter_replacement_year::Int = 10
    battery_replacement_year::Int = 10
    cost_constant_replacement_year::Int = 10
    om_cost_fraction_of_installed_cost::Float64 = 0.025 # Annual O&M cost as a fraction of installed cost
    macrs_option_years::Int = 5 #Note: default may change if Site.sector is not "commercial/industrial"
    macrs_bonus_fraction::Float64 = 1.0 #Note: default may change if Site.sector is not "commercial/industrial"
    macrs_itc_reduction::Float64 = 0.5
    total_itc_fraction::Float64 = 0.3 #Note: default may change if Site.sector is not "commercial/industrial"
    total_rebate_per_kw::Real = 0.0
    total_rebate_per_kwh::Real = 0.0
    charge_efficiency::Float64 = rectifier_efficiency_fraction * internal_efficiency_fraction^0.5
    discharge_efficiency::Float64 = inverter_efficiency_fraction * internal_efficiency_fraction^0.5
    grid_charge_efficiency::Float64 = can_grid_charge ? charge_efficiency : 0.0
    model_degradation::Bool = false
    degradation::Dict = Dict()
    minimum_avg_soc_fraction::Float64 = 0.0
    optimize_soc_init_fraction::Bool = false # If true, soc_init_fraction will not apply. Model will optimize initial SOC and constrain initial SOC = final SOC.
    min_duration_hours::Real = 0.0 # Minimum amount of time storage can discharge at its rated power capacity
    max_duration_hours::Real = 100000.0 # Maximum amount of time storage can discharge at its rated power capacity (ratio of ElectricStorage size_kwh to size_kw)
```
source`REopt.Degradation` — Type
```
Degradation
```

Inputs used when `ElectricStorage.model_degradation` is `true`:

```
Base.@kwdef mutable struct Degradation
    calendar_fade_coefficient::Real = 1.16E-03
    cycle_fade_coefficient::Vector{<:Real} = [2.46E-05]
    cycle_fade_fraction::Vector{<:Real} = [1.0]
    time_exponent::Real = 0.428
    installed_cost_per_kwh_declination_rate::Real = 0.05
    maintenance_strategy::String = "augmentation"  # one of ["augmentation", "replacement"]
    maintenance_cost_per_kwh::Vector{<:Real} = Real[]
end
```

None of the above values are required. If `ElectricStorage.model_degradation` is `true` then the defaults above are used. If the `maintenance_cost_per_kwh` is not provided then it is determined using the `ElectricStorage.installed_cost_per_kwh` and the `installed_cost_per_kwh_declination_rate` along with a present worth factor fff to account for the present cost of buying a battery in the future. The present worth factor for each day is:

f(day)=(1−rg)day365(1+rd)day365f(day) = \frac{ (1-r\_g)^\frac{day}{365} } { (1+r\_d)^\frac{day}{365} }f(day)=(1+rd​)365day​(1−rg​)365day​​

where rgr\_grg​ = `installed_cost_per_kwh_declination_rate` and rdr\_drd​ = `p.s.financial.owner_discount_rate_fraction`.

Note this day-specific calculation of the present-worth factor accumulates differently from the annually updated discount rate for other net-present value calculations in REopt, and has a higher effective discount rate as a result. The present worth factor is used in the same manner irrespective of the `maintenance_strategy`.

**Battery State Of Health**

The state of health [`SOH`] is a linear function of the daily average state of charge [`Eavg`] and the daily equivalent full cycles [`EFC`]. The initial `SOH` is set to the optimal battery energy capacity (in kWh). The evolution of the `SOH` beyond the first day is:

SOH[d]=SOH[d−1]−h(12kcalEavg[d−1]/d+kcycEFC[d−1]∀d∈{2…D})SOH[d] = SOH[d-1] - h\left( \frac{1}{2} k\_{cal} Eavg[d-1] / \sqrt{d} + k\_{cyc} EFC[d-1] \quad \forall d \in \{2\dots D\} \right)SOH[d]=SOH[d−1]−h(21​kcal​Eavg[d−1]/d​+kcyc​EFC[d−1]∀d∈{2…D})

where:

- kcalk\_{cal}kcal​ is the `calendar_fade_coefficient`
- kcyck\_{cyc}kcyc​ is the `cycle_fade_coefficient`
- hhh is the hours per time step
- DDD is the total number of days, 365 \* `analysis_years`

The `SOH` is used to determine the maintence cost of the storage system, which depends on the `maintenance_strategy`.

**Augmentation Maintenance Strategy**

The augmentation maintenance strategy assumes that the battery energy capacity is maintained by replacing degraded cells daily in terms of cost. Using the definition of the `SOH` above the maintenance cost is:

Caug=∑d∈{2…D}Cinstallf(day)(SOH[d−1]−SOH[d])C\_{\text{aug}} = \sum\_{d \in \{2\dots D\}} C\_{\text{install}} f(day) \left( SOH[d-1] - SOH[d] \right)Caug​=∑d∈{2…D}​Cinstall​f(day)(SOH[d−1]−SOH[d])

where

- f(day)f(day)f(day) is the present worth factor of battery degradation costs as described above;
- CinstallC\_{\text{install}}Cinstall​ is the `ElectricStorage.installed_cost_per_kwh`; and
- SOH[d−1]−SOH[d]SOH[d-1] - SOH[d]SOH[d−1]−SOH[d] is the incremental amount of battery capacity lost in a day.

The CaugC\_{\text{aug}}Caug​ is added to the objective function to be minimized with all other costs.

**Replacement Maintenance Strategy**

Modeling the replacement maintenance strategy is more complex than the augmentation strategy. Effectively the replacement strategy says that the battery has to be replaced once the `SOH` drops below 80% of the optimal, purchased capacity. It is possible that multiple replacements (at same replacement frequency) could be required under this strategy.

The replacement strategy cost is:

Crepl=BkWhNreplf(d80)CinstallC\_{\text{repl}} = B\_{\text{kWh}} N\_{\text{repl}} f(d\_{80}) C\_{\text{install}}Crepl​=BkWh​Nrepl​f(d80​)Cinstall​

where:

- BkWhB\_{\text{kWh}}BkWh​ is the optimal battery capacity (`ElectricStorage.size_kwh` in the results dictionary);
- NreplN\_{\text{repl}}Nrepl​ is the number of battery replacments required (a function of the month in which the `SOH` falls below 80% of original capacity);
- f(d80)f(d\_{80})f(d80​) is the present worth factor at approximately the 15th day of the month in which the `SOH` falls below 80% of original capacity;
- CinstallC\_{\text{install}}Cinstall​ is the `ElectricStorage.installed_cost_per_kwh`.

The CreplC\_{\text{repl}}Crepl​ is added to the objective function to be minimized with all other costs.

**Battery residual value**

Since the battery can be replaced one-to-many times under this strategy, battery residual value captures the $ value of remaining battery life at end of analysis period. For example if replacement happens in month 145, then assuming 25 year analysis period there will be 2 replacements (months 145 and 290). The last battery which was placed in service during month 290 only serves for 10 months (i.e. 6.89% of its expected life assuming 145 month replacement frequecy). In this case, the battery has 93.1% of residual life remaining as useful life left after analysis period ends. A residual value cost vector is created to hold this value for all months. Residual value is calculated as:

Cresidual=Rf(dlast)CinstallC\_{\text{residual}} = R f(d\_{\text{last}}) C\_{\text{install}}Cresidual​=Rf(dlast​)Cinstall​ where:

- RRR is the `residual_factor` which determines portion of battery life remaining at the end of the analysis period;
- f(dlast)f(d\_{\text{last}})f(dlast​) is the present worth factor at approximately the 15th day of the last month in the analysis period;
- CinstallC\_{\text{install}}Cinstall​ is the `ElectricStorage.installed_cost_per_kwh`.

The CresidualC\_{\text{residual}}Cresidual​ is added to the objective function to be minimized with all other costs.

**Example of inputs**

The following shows how one would use the degradation model in REopt via the Scenario inputs:

```
{
    ...
    "ElectricStorage": {
        "installed_cost_per_kwh": 390,
        ...
        "model_degradation": true,
        "degradation": {
            "calendar_fade_coefficient": 1.16E-03,
            "cycle_fade_coefficient": [2.46E-05],
            "cycle_fade_fraction": [1.0],
            "time_exponent": 0.428
            "installed_cost_per_kwh_declination_rate": 0.05,
            "maintenance_strategy": "replacement",
            ...
        }
    },
    ...
}
```

Note that not all of the above inputs are necessary. When not providing `calendar_fade_coefficient` for example the default value will be used.

source
## Generator

`REopt.Generator` — Type

`Generator` is an optional REopt input with the following keys and default values:

```
    only_runs_during_grid_outage::Bool = true,
    existing_kw::Real = 0,
    min_kw::Real = 0,
    max_kw::Real = 1.0e6,
    installed_cost_per_kw::Real = off_grid_flag ? 880 : only_runs_during_grid_outage ? 650.0 : 800.0,
    om_cost_per_kw::Real = off_grid_flag ? 10.0 : 20.0,
    om_cost_per_kwh::Real = 0.0,
    fuel_cost_per_gallon::Real = 2.25,
    electric_efficiency_full_load::Real = 0.322,
    electric_efficiency_half_load::Real = electric_efficiency_full_load,
    fuel_avail_gal::Real = 1.0e9,
    fuel_higher_heating_value_kwh_per_gal::Real = 40.7,
    min_turn_down_fraction::Real = off_grid_flag ? 0.15 : 0.0,
    sells_energy_back_to_grid::Bool = false,
    can_net_meter::Bool = false,
    can_wholesale::Bool = false,
    can_export_beyond_nem_limit = false,
    can_curtail::Bool = false,
    macrs_option_years::Int = 0,
    macrs_bonus_fraction::Real = 0.0,
    macrs_itc_reduction::Real = 0.0,
    federal_itc_fraction::Real = 0.0,
    federal_rebate_per_kw::Real = 0.0,
    state_ibi_fraction::Real = 0.0,
    state_ibi_max::Real = 1.0e10,
    state_rebate_per_kw::Real = 0.0,
    state_rebate_max::Real = 1.0e10,
    utility_ibi_fraction::Real = 0.0,
    utility_ibi_max::Real = 1.0e10,
    utility_rebate_per_kw::Real = 0.0,
    utility_rebate_max::Real = 1.0e10,
    production_incentive_per_kwh::Float64 = 0.0 # revenue from production incentive per kWh electricity produced, including curtailment
    production_incentive_max_benefit::Float64 = 1.0e9 # maximum allowable annual revenue from production incentives
    production_incentive_years::Int = 0 # number of year in which production incentives are paid
    production_incentive_max_kw::Float64 = 1.0e9 # maximum allowable system size to receive production incentives
    fuel_renewable_energy_fraction::Real = 0.0,
    emissions_factor_lb_CO2_per_gal::Real = 22.58, # CO2e
    emissions_factor_lb_NOx_per_gal::Real = 0.0775544,
    emissions_factor_lb_SO2_per_gal::Real = 0.040020476,
    emissions_factor_lb_PM25_per_gal::Real = 0.0,
    replacement_year::Int = off_grid_flag ? 10 : analysis_years, # Project year in which generator capacity will be replaced at a cost of replace_cost_per_kw.
    replace_cost_per_kw::Real = off_grid_flag ? installed_cost_per_kw : 0.0 # Per kW replacement cost for generator capacity. Replacement costs are considered tax deductible.
```
source
## ExistingBoiler

`REopt.ExistingBoiler` — Type

`ExistingBoiler` is an optional REopt input with the following keys and default values:

```
    max_heat_demand_kw::Real=0, # Auto-populated based on SpaceHeatingLoad and DomesticHotWaterLoad inputs
    production_type::String = "hot_water", # Can be "steam" or "hot_water"
    max_thermal_factor_on_peak_load::Real = 1.25,
    installed_cost_per_mmbtu_per_hour::Real = 0.0  # Represents needed CapEx in BAU, assuming net present value basis; cost is scaled to the size of boiler needed
    installed_cost_dollars::Real = 0.0  # Represents needed CapEx in BAU, assuming net present cost basis; also incurred in Optimal case if still using at all
    efficiency::Real = NaN, # Existing boiler system efficiency - conversion of fuel to usable heating thermal energy. See note below.
    fuel_cost_per_mmbtu::Union{<:Real, AbstractVector{<:Real}} = [], # REQUIRED. Can be a scalar, a list of 12 monthly values, or a time series of values for every time step
    fuel_type::String = "natural_gas", # "restrict_to": ["natural_gas", "landfill_bio_gas", "propane", "diesel_oil"]
    can_supply_steam_turbine::Bool = false,
    retire_in_optimal::Bool = false,  # Do NOT use in the optimal case (still used in BAU)
    fuel_renewable_energy_fraction::Real = get(FUEL_DEFAULTS["fuel_renewable_energy_fraction"],fuel_type,0),
    emissions_factor_lb_CO2_per_mmbtu::Real = get(FUEL_DEFAULTS["emissions_factor_lb_CO2_per_mmbtu"],fuel_type,0),
    emissions_factor_lb_NOx_per_mmbtu::Real = get(FUEL_DEFAULTS["emissions_factor_lb_NOx_per_mmbtu"],fuel_type,0),
    emissions_factor_lb_SO2_per_mmbtu::Real = get(FUEL_DEFAULTS["emissions_factor_lb_SO2_per_mmbtu"],fuel_type,0),
    emissions_factor_lb_PM25_per_mmbtu::Real = get(FUEL_DEFAULTS["emissions_factor_lb_PM25_per_mmbtu"],fuel_type,0)
    can_serve_dhw::Bool = true # If ExistingBoiler can supply heat to the domestic hot water load
    can_serve_space_heating::Bool = true # If ExistingBoiler can supply heat to the space heating load
    can_serve_process_heat::Bool = true # If ExistingBoiler can supply heat to the process heating load
```
source
## CHP

`REopt.CHP` — Type

`CHP` is an optional REopt input with the following keys and default values:

```
    prime_mover::Union{String, Nothing} = nothing # Suggested to inform applicable default cost and performance. "restrict_to": ["recip_engine", "micro_turbine", "combustion_turbine", "fuel_cell"]
    fuel_cost_per_mmbtu::Union{<:Real, AbstractVector{<:Real}} = [] # REQUIRED. Can be a scalar, a list of 12 monthly values, or a time series of values for every time step

    # Required "custom inputs" if not providing prime_mover:
    installed_cost_per_kw::Union{Float64, AbstractVector{Float64}} = NaN # Installed CHP system cost in $/kW (based on rated electric power)
    tech_sizes_for_cost_curve::Union{Float64, AbstractVector{Float64}} = NaN # Size of CHP systems corresponding to installed cost input points"
    om_cost_per_kwh::Float64 = NaN # CHP non-fuel variable operations and maintenance costs in $/kwh
    electric_efficiency_full_load::Float64 = NaN # Electric efficiency of CHP prime-mover at full-load, HHV-basis
    electric_efficiency_half_load::Float64 = NaN # Electric efficiency of CHP prime-mover at half-load, HHV-basis
    min_turn_down_fraction::Float64 = NaN # Minimum CHP electric loading in fraction of capacity (size_kw)
    thermal_efficiency_full_load::Float64 = NaN # CHP fraction of fuel energy converted to hot-thermal energy at full electric load
    thermal_efficiency_half_load::Float64 = NaN # CHP fraction of fuel energy converted to hot-thermal energy at half electric load
    min_allowable_kw::Float64 = NaN # Minimum CHP size (based on electric) that still allows the model to choose zero (e.g. no CHP system)
    cooling_thermal_factor::Float64 = NaN  # only needed with cooling load
    unavailability_periods::AbstractVector{Dict} = Dict[] # CHP unavailability periods for scheduled and unscheduled maintenance, list of dictionaries with keys of "['month', 'start_week_of_month', 'start_day_of_week', 'start_hour', 'duration_hours'] all values are one-indexed and start_day_of_week uses 1 for Monday, 7 for Sunday
    unavailability_hourly::AbstractVector{Int64} = Int64[] # Hourly 8760 profile of unavailability (1) and availability (0)

    # Optional inputs:
    size_class::Union{Int, Nothing} = nothing # CHP size class for using appropriate default inputs, with size_class=0 using an average of all other size class data
    min_kw::Float64 = 0.0 # Minimum CHP size (based on electric) constraint for optimization
    max_kw::Float64 = NaN # Maximum CHP size (based on electric) constraint for optimization. Determined by heuristic sizing based on heating load or electric load.
    fuel_type::String = "natural_gas" # "restrict_to": ["natural_gas", "landfill_bio_gas", "propane", "diesel_oil"]
    om_cost_per_kw::Float64 = 0.0 # Annual CHP fixed operations and maintenance costs in $/kw-yr
    om_cost_per_hr_per_kw_rated::Float64 = 0.0 # CHP non-fuel variable operations and maintenance costs in $/hr/kw_rated
    supplementary_firing_capital_cost_per_kw::Float64 = 150.0 # Installed CHP supplementary firing system cost in $/kW (based on rated electric power)
    supplementary_firing_max_steam_ratio::Float64 = 1.0 # Ratio of max fired steam to un-fired steam production. Relevant only for combustion_turbine prime_mover
    supplementary_firing_efficiency::Float64 = 0.92 # Thermal efficiency of the incremental steam production from supplementary firing. Relevant only for combustion_turbine prime_mover
    standby_rate_per_kw_per_month::Float64 = 0.0 # Standby rate charged to CHP based on CHP electric power size
    reduces_demand_charges::Bool = true # Boolean indicator if CHP does not reduce demand charges
    can_supply_steam_turbine::Bool=false # If CHP can supply steam to the steam turbine for electric production
    can_serve_dhw::Bool = true # If CHP can supply heat to the domestic hot water load
    can_serve_space_heating::Bool = true # If CHP can supply heat to the space heating load
    can_serve_process_heat::Bool = true # If CHP can supply heat to the process heating load
    is_electric_only::Bool = false # If CHP is a prime generator that does not supply heat

    macrs_option_years::Int = 5 # Notes: this value cannot be 0 if aiming to apply 100% bonus depreciation; default may change if Site.sector is not "commercial/industrial"
    macrs_bonus_fraction::Float64 = 1.0 #Note: default may change if Site.sector is not "commercial/industrial"
    macrs_itc_reduction::Float64 = 0.5
    federal_itc_fraction::Float64 = 0.0
    federal_rebate_per_kw::Float64 = 0.0
    state_ibi_fraction::Float64 = 0.0
    state_ibi_max::Float64 = 1.0e10
    state_rebate_per_kw::Float64 = 0.0
    state_rebate_max::Float64 = 1.0e10
    utility_ibi_fraction::Float64 = 0.0
    utility_ibi_max::Float64 = 1.0e10
    utility_rebate_per_kw::Float64 = 0.0
    utility_rebate_max::Float64 = 1.0e10
    production_incentive_per_kwh::Float64 = 0.0 # revenue from production incentive per kWh electricity produced, including curtailment
    production_incentive_max_benefit::Float64 = 1.0e9 # maximum allowable annual revenue from production incentives
    production_incentive_years::Int = 0 # number of year in which production incentives are paid
    production_incentive_max_kw::Float64 = 1.0e9 # maximum allowable system size to receive production incentives
    can_net_meter::Bool = false
    can_wholesale::Bool = false
    can_export_beyond_nem_limit::Bool = false
    can_curtail::Bool = false
    fuel_renewable_energy_fraction::Float64 = FUEL_DEFAULTS["fuel_renewable_energy_fraction"][fuel_type]
    emissions_factor_lb_CO2_per_mmbtu::Float64 = FUEL_DEFAULTS["emissions_factor_lb_CO2_per_mmbtu"][fuel_type]
    emissions_factor_lb_NOx_per_mmbtu::Float64 = FUEL_DEFAULTS["emissions_factor_lb_NOx_per_mmbtu"][fuel_type]
    emissions_factor_lb_SO2_per_mmbtu::Float64 = FUEL_DEFAULTS["emissions_factor_lb_SO2_per_mmbtu"][fuel_type]
    emissions_factor_lb_PM25_per_mmbtu::Float64 = FUEL_DEFAULTS["emissions_factor_lb_PM25_per_mmbtu"][fuel_type]
```
source
## AbsorptionChiller

`REopt.AbsorptionChiller` — Type

`AbsorptionChiller` is an optional REopt input with the following keys and default values:

```
    thermal_consumption_hot_water_or_steam::Union{String, Nothing} = nothing  # Defaults to "hot_water" if chp_prime_mover or boiler_type are not provided
    chp_prime_mover::String = ""  # Informs thermal_consumption_hot_water_or_steam if not provided

    # Defaults for fields below are dependent on thermal_consumption_hot_water_or_steam and max cooling load
    installed_cost_per_ton::Union{Float64, Nothing} = nothing # Thermal power-based cost of absorption chiller (3.5 to 1 ton to kwt)
    om_cost_per_ton::Union{Float64, Nothing} = nothing # Yearly fixed O&M cost on a thermal power (ton) basis
    min_ton::Float64 = 0.0, # Minimum thermal power size constraint for optimization
    max_ton::Float64 = BIG_NUMBER, # Maximum thermal power size constraint for optimization
    cop_thermal::Union{Float64, Nothing} = nothing, # Absorption chiller system coefficient of performance - conversion of hot thermal power input to usable cooling thermal energy output
    cop_electric::Float64 = 14.1, # Absorption chiller electric consumption CoP from cooling tower heat rejection - conversion of electric power input to usable cooling thermal energy output
    macrs_option_years::Float64 = 0, # MACRS schedule for financial analysis. Set to zero to disable
    macrs_bonus_fraction::Float64 = 0 # Percent of upfront project costs to depreciate under MACRS
    heating_load_input::Union{String, Nothing} = nothing # heating load that serves as input to absorption chiller
```

!!! Note To model AbsorptionChiller, there is logic which informs defaults for costs and COP: (i) `thermal_consumption_hot_water_or_steam` from ["steam", "hot*water"], (ii) `chp*prime*mover` from ["recip*engine", "micro*turbine", "combustion*turbine", "fuel*cell"], or (iii) if (i) and (ii) are not provided, the default `thermal*consumption*hot*water*or*steam`is`hot*water` The defaults for costs and COP will be populated from data/absorption*chiller/defaults.json, based on the `thermal_consumption_hot_water_or_steam` or `chp_prime_mover`. `boiler_type` is "steam" if `prime_mover` is "combustion*turbine" and is "hot*water" for all other `chp_prime_mover` types.

source
## Boiler

`REopt.Boiler` — Type
```
Boiler
```

When modeling a heating load an `ExistingBoiler` model is created even if user does not provide the `ExistingBoiler` key. The `Boiler` model is not created by default. If a user provides the `Boiler` key then the optimal scenario has the option to purchase this new `Boiler` to meet the heating load in addition to using the `ExistingBoiler` to meet the heating load.

```
function Boiler(;
    min_mmbtu_per_hour::Real = 0.0, # Minimum thermal power size
    max_mmbtu_per_hour::Real = 0.0, # Maximum thermal power size
    efficiency::Real = 0.8, # boiler system efficiency - conversion of fuel to usable heating thermal energy
    fuel_cost_per_mmbtu::Union{<:Real, AbstractVector{<:Real}} = 0.0,
    macrs_option_years::Int = 0, # MACRS schedule for financial analysis. Set to zero to disable
    macrs_bonus_fraction::Real = 0.0, # Fraction of upfront project costs to depreciate under MACRS
    installed_cost_per_mmbtu_per_hour::Real = 293000.0, # Thermal power-based cost
    om_cost_per_mmbtu_per_hour::Real = 2930.0, # Thermal power-based fixed O&M cost
    om_cost_per_mmbtu::Real = 0.0, # Thermal energy-based variable O&M cost
    fuel_type::String = "natural_gas",  # "restrict_to": ["natural_gas", "landfill_bio_gas", "propane", "diesel_oil", "uranium"]
    can_supply_steam_turbine::Bool = true # If the boiler can supply steam to the steam turbine for electric production
    can_serve_dhw::Bool = true # If Boiler can supply heat to the domestic hot water load
    can_serve_space_heating::Bool = true # If Boiler can supply heat to the space heating load
    can_serve_process_heat::Bool = true # If Boiler can supply heat to the process heating load
    fuel_renewable_energy_fraction::Real = get(FUEL_DEFAULTS["fuel_renewable_energy_fraction"],fuel_type,0) # fraction of renewable-sourced fuel input to boiler
    emissions_factor_lb_CO2_per_mmbtu::Real = get(FUEL_DEFAULTS["emissions_factor_lb_CO2_per_mmbtu"],fuel_type,0)
    emissions_factor_lb_NOx_per_mmbtu::Real = get(FUEL_DEFAULTS["emissions_factor_lb_NOx_per_mmbtu"],fuel_type,0)
    emissions_factor_lb_SO2_per_mmbtu::Real = get(FUEL_DEFAULTS["emissions_factor_lb_SO2_per_mmbtu"],fuel_type,0)
    emissions_factor_lb_PM25_per_mmbtu::Real = get(FUEL_DEFAULTS["emissions_factor_lb_PM25_per_mmbtu"],fuel_type,0)
)
```
source
## HotThermalStorage

`REopt.HotThermalStorageDefaults` — Type

`HotThermalStorage` is an optional REopt input with the following keys and default values:

```
    min_gal::Float64 = 0.0
    max_gal::Float64 = 0.0
    hot_water_temp_degF::Float64 = 180.0
    cool_water_temp_degF::Float64 = 160.0
    internal_efficiency_fraction::Float64 = 0.999999
    soc_min_fraction::Float64 = 0.1
    soc_init_fraction::Float64 = 0.5
    installed_cost_per_gal::Float64 = 1.50
    thermal_decay_rate_fraction::Float64 = 0.0004
    om_cost_per_gal::Float64 = 0.0
    macrs_option_years::Int = 5 #Note: default may change if Site.sector is not "commercial/industrial"
    macrs_bonus_fraction::Float64 = 1.0 #Note: default may change if Site.sector is not "commercial/industrial"
    macrs_itc_reduction::Float64 = 0.5
    total_itc_fraction::Float64 = 0.3 #Note: default may change if Site.sector is not "commercial/industrial"
    total_rebate_per_kwh::Float64 = 0.0
    can_serve_dhw::Bool = true
    can_serve_space_heating::Bool = true
    can_serve_process_heat::Bool = false
```
source
## HighTempThermalStorage

`REopt.HighTempThermalStorageDefaults` — Type

`HighTempThermalStorage` is an optional REopt input with the following keys and default values:

```
    fluid::String = "INCOMP::Nak"
    min_kwh::Float64 = 0.0
    max_kwh::Float64 = 0.0
    hot_temp_degF::Float64 = 1065.0
    cool_temp_degF::Float64 = 554.0
    internal_efficiency_fraction::Float64 = 0.999999
    soc_min_fraction::Float64 = 0.1
    soc_init_fraction::Float64 = 0.5
    installed_cost_per_kwh::Float64 = 86.0
    thermal_decay_rate_fraction::Float64 = 0.0004
    om_cost_per_kwh::Float64 = 0.0
    macrs_option_years::Int = 5 #Note: default may change if Site.sector is not "commercial/industrial"
    macrs_bonus_fraction::Float64 = 1.0 #Note: default may change if Site.sector is not "commercial/industrial"
    macrs_itc_reduction::Float64 = 0.5
    total_itc_fraction::Float64 = 0.3 #Note: default may change if Site.sector is not "commercial/industrial"
    total_rebate_per_kwh::Float64 = 0.0
    can_supply_steam_turbine::Bool = true
    can_serve_dhw::Bool = false
    can_serve_space_heating:Bool = false
    can_serve_process_heat::Bool = true
    one_direction_flow::Bool = false
```
source
## ColdThermalStorage

`REopt.ColdThermalStorageDefaults` — Type

Cold thermal energy storage sytem; specifically, a chilled water system used to meet thermal cooling loads.

`ColdThermalStorage` is an optional REopt input with the following keys and default values:

```
    min_gal::Float64 = 0.0
    max_gal::Float64 = 0.0
    hot_water_temp_degF::Float64 = 56.0 # Warmed-side return water temperature from the cooling load to the ColdTES (top of tank)
    cool_water_temp_degF::Float64 = 44.0 # Chilled-side supply water temperature from ColdTES (bottom of tank) to the cooling load
    internal_efficiency_fraction::Float64 = 0.999999 # Thermal losses due to mixing from thermal power entering or leaving tank
    soc_min_fraction::Float64 = 0.1 # Minimum allowable TES thermal state of charge
    soc_init_fraction::Float64 = 0.5 # TES thermal state of charge at first hour of optimization
    installed_cost_per_gal::Float64 = 1.50 # Thermal energy-based cost of TES (e.g. volume of the tank)
    thermal_decay_rate_fraction::Float64 = 0.0004 # Thermal loss (gain) rate as a fraction of energy storage capacity, per hour (frac*energy_capacity/hr = kw_thermal)
    om_cost_per_gal::Float64 = 0.0 # Yearly fixed O&M cost dependent on storage energy size
    macrs_option_years::Int = 5 #Note: default may change if Site.sector is not "commercial/industrial"
    macrs_bonus_fraction::Float64 = 1.0 #Note: default may change if Site.sector is not "commercial/industrial"
    macrs_itc_reduction::Float64 = 0.5
    total_itc_fraction::Float64 = 0.3 #Note: default may change if Site.sector is not "commercial/industrial"
    total_rebate_per_kwh::Float64 = 0.0
```
source
## HeatingLoad

`REopt.HeatingLoad` — Method

**`HeatingLoad` is a base function for the types of heating load inputs with the following keys and default values:**

```
    load_type::String = "",  # Valid options are space_heating for SpaceHeatingLoad, domestic_hot_water for DomesticHotWaterLoad, and process_heat for ProcessHeatLoad
    doe_reference_name::String = "",  # For SpaceHeatingLoad and DomesticHotWaterLoad
    blended_doe_reference_names::Array{String, 1} = String[],  # For SpaceHeatingLoad and DomesticHotWaterLoad
    blended_doe_reference_percents::Array{<:Real,1} = Real[],  # For SpaceHeatingLoad and DomesticHotWaterLoad
    industrial_reference_name::String = "",  # For ProcessHeatLoad
    blended_industrial_reference_names::Array{String, 1} = String[],  # For ProcessHeatLoad
    blended_industrial_reference_percents::Array{<:Real,1} = Real[],  # For ProcessHeatLoad
    city::String = "",
    year::Union{Int, Nothing} = doe_reference_name ≠ "" || blended_doe_reference_names ≠ String[] || industrial_reference_name ≠ "" || blended_industrial_reference_names ≠ String[] ? 2017 : nothing, # CRB profiles are 2017 by default. If providing load profile, specify year of data.
    annual_mmbtu::Union{Real, Nothing} = nothing,
    monthly_mmbtu::Array{<:Real,1} = Real[],
    addressable_load_fraction::Any = 1.0,  # Fraction of input fuel load which is addressable by heating technologies. Can be a scalar or vector with length aligned with use of monthly_mmbtu or fuel_loads_mmbtu_per_hour.
    fuel_loads_mmbtu_per_hour::Array{<:Real,1} = Real[], # Vector of space heating fuel loads [mmbtu/hr]. Length must equal 8760 * `Settings.time_steps_per_hour`
    normalize_and_scale_load_profile_input::Bool = false,  # Takes fuel_loads_mmbtu_per_hour and normalizes and scales it to annual_mmbtu or monthly_mmbtu
    existing_boiler_efficiency::Real = NaN
```

There are different ways to define a heating load:

1. A time-series via the `fuel_loads_mmbtu_per_hour`,
2. Scaling a DOE Commercial Reference Building (CRB) or industrial reference profile or a blend of profiles to either the `annual_mmbtu` or `monthly_mmbtu` values;
3. Using the same `doe_reference_name` or `blended_doe_reference_names` from the `ElectricLoad`.
4. A time-series via the `fuel_loads_mmbtu_per_hour` along with `annual_mmbtu` or `monthly_mmbtu` with `normalize_and_scale_load_profile_input`=true

When using an `ElectricLoad` defined from a `doe_reference_name` or `blended_doe_reference_names` one only needs to provide an empty Dict in the scenario JSON to add a `SpaceHeatingLoad` to a `Scenario`, i.e.:

```
...
"ElectricLoad": {"doe_reference_name": "MidriseApartment"},
"SpaceHeatingLoad" : {},
...
```

In this case the values provided for `doe_reference_name`, or `blended_doe_reference_names` and `blended_doe_reference_percents` are copied from the `ElectricLoad` to the the particular `HeatingLoad` type.

!!! note for all heating loads Hot water, space heating, and process heat "load" inputs are in terms of energy input required (boiler fuel), not the actual end use thermal energy demand. The fuel energy is multiplied by the existing*boiler*efficiency to get the actual energy demand.

source
## CoolingLoad

`REopt.CoolingLoad` — Type

`CoolingLoad` is an optional REopt input with the following keys and default values:

```
    doe_reference_name::String = "",
    blended_doe_reference_names::Array{String, 1} = String[],
    blended_doe_reference_percents::Array{<:Real,1} = Real[],
    city::String = "",
    year::Int = doe_reference_name ≠ "" || blended_doe_reference_names ≠ String[] ? 2017 : nothing, # CRB profiles are 2017 by default. If providing load profile, specify year of data.
    annual_tonhour::Union{Real, Nothing} = nothing,
    monthly_tonhour::Array{<:Real,1} = Real[],
    thermal_loads_ton::Array{<:Real,1} = Real[], # Vector of cooling thermal loads [ton] = [short ton hours/hour]. Length must equal 8760 * `Settings.time_steps_per_hour`
    annual_fraction_of_electric_load::Union{Real, Nothing} = nothing, # Fraction of total electric load that is used for cooling
    monthly_fractions_of_electric_load::Array{<:Real,1} = Real[],
    per_time_step_fractions_of_electric_load::Array{<:Real,1} = Real[]
```

There are many ways to define a `CoolingLoad`:

1. a time-series via the `thermal_loads_ton`,
2. DoE Commercial Reference Building (CRB) profile or a blend of CRB profiles which uses the buildings' fraction of total electric for cooling profile applied to the `ElectricLoad`
3. scaling a DoE Commercial Reference Building (CRB) profile or a blend of CRB profiles using `annual_tonhour` or `monthly_tonhour`
4. the `annual_fraction_of_electric_load`, `monthly_fractions_of_electric_load`, or `per_time_step_fractions_of_electric_load` values, which get applied to the `ElectricLoad` to determine the cooling electric load;
5. or using the `doe_reference_name` or `blended_doe_reference_names` from the `ElectricLoad`.

The electric-based `loads_kw` of the `CoolingLoad` is a *subset* of the total electric load `ElectricLoad`, so `CoolingLoad.loads_kw` for the BAU/conventional electric consumption of the `existing_chiller` is subtracted from the `ElectricLoad` for the non-cooling electric load balance constraint in the model.

When using an `ElectricLoad` defined from a `doe_reference_name` or `blended_doe_reference_names` one only needs to provide an empty Dict in the scenario JSON to add a `CoolingLoad` to a `Scenario`, i.e.:

```
...
"ElectricLoad": {"doe_reference_name": "MidriseApartment"},
"CoolingLoad" : {},
...
```

In this case the values provided for `doe_reference_name`, or `blended_doe_reference_names` and `blended_doe_reference_percents` are copied from the `ElectricLoad` to the `CoolingLoad`.

source
## FlexibleHVAC

`REopt.FlexibleHVAC` — Type

`FlexibleHVAC` is an optional REopt input with the following keys and default values:

```
    system_matrix::AbstractMatrix{Float64}  # N x N, with N states (temperatures in RC network)
    input_matrix::AbstractMatrix{Float64}  # N x M, with M inputs
    exogenous_inputs::AbstractMatrix{Float64}  # M x T, with T time steps
    control_node::Int64
    initial_temperatures::AbstractVector{Float64}
    temperature_upper_bound_degC::Union{Real, Nothing}
    temperature_lower_bound_degC::Union{Real, Nothing}
    installed_cost::Float64
```

Every model with `FlexibleHVAC` includes a preprocessing step to calculate the business-as-usual (BAU) cost of meeting the thermal loads using a dead-band controller. The BAU cost is then used in the binary decision for purchasing the `FlexibleHVAC` system: if the `FlexibleHVAC` system is purchased then the heating and cooling costs are determined by the HVAC dispatch that minimizes the lifecycle cost of energy. If the `FlexibleHVAC` system is not purchased then the BAU heating and cooling costs must be paid.

There are two construction methods for `FlexibleHVAC`, which depend on whether or not the data was loaded in from a JSON file. The issue with data from JSON is that the vector-of-vectors from the JSON file must be appropriately converted to Julia Matrices. When loading in a Scenario from JSON that includes a `FlexibleHVAC` model, if you include the `flex_hvac_from_json` argument to the `Scenario` constructor then the conversion to Matrices will be done appropriately.

source
## ExistingChiller

`REopt.ExistingChiller` — Type

`ExistingChiller` is an optional REopt input with the following keys and default values:

```
    loads_kw_thermal::Vector{<:Real},
    cop::Union{Real, Nothing} = nothing,
    max_thermal_factor_on_peak_load::Real=1.25
    installed_cost_per_kw::Real = 0.0  # Represents needed CapEx in BAU, assuming net present value basis based on current size; also incurred in Optimal case if still using at all
    installed_cost_dollars::Real = 0.0  # Represents needed CapEx in BAU, assuming net present cost basis; also incurred in Optimal case if still using at all
    retire_in_optimal::Bool = false  # Do NOT use in the optimal case (still used in BAU)
```
source
## GHP

`REopt.GHP` — Type

GHP evaluations typically require the `GhpGhx.jl` package to be loaded unless the `GhpGhx.jl` package was already used externally to create `inputs_dict["GHP"]["ghpghx_responses"]`. See the Home page under "Additional package loading for GHP" for instructions. This `GHP` struct uses the response from `GhpGhx.jl` to process input parameters for REopt including additional cost parameters for `GHP`.

```
GHP
```

struct with outer constructor:

```
    require_ghp_purchase::Union{Bool, Int64} = false  # 0 = false, 1 = true
    installed_cost_heatpump_per_ton::Float64 = 1075.0
    installed_cost_wwhp_heating_pump_per_ton::Float64 = 700.0
    installed_cost_wwhp_cooling_pump_per_ton::Float64 = 700.0
    heatpump_capacity_sizing_factor_on_peak_load::Float64 = 1.1
    installed_cost_ghx_per_ft::Float64 = 14.0
    installed_cost_building_hydronic_loop_per_sqft = 1.70
    om_cost_per_sqft_year::Float64 = -0.51
    building_sqft::Float64                                  # Required input
    space_heating_efficiency_thermal_factor::Float64 = NaN  # Default depends on building and location
    cooling_efficiency_thermal_factor::Float64 = NaN        # Default depends on building and location
    ghpghx_response::Dict = Dict()
    can_serve_dhw::Bool = false
    max_ton::Real                                           # Maximum heat pump capacity size. Default at a big number
    max_number_of_boreholes::Real                           # Maximum GHX size
    load_served_by_ghp::String                              # "scaled" or "nonpeak"

    macrs_option_years::Int = 0
    macrs_bonus_fraction::Float64 = 0.0
    macrs_itc_reduction::Float64 = 0.5
    federal_itc_fraction::Float64 = 0.3 #Note: default may change if Site.sector is not "commercial/industrial"
    federal_rebate_per_ton::Float64 = 0.0
    federal_rebate_per_kw::Float64 = 0.0
    state_ibi_fraction::Float64 = 0.0
    state_ibi_max::Float64 = 1.0e10
    state_rebate_per_ton::Float64 = 0.0
    state_rebate_per_kw::Float64 = 0.0
    state_rebate_max::Float64 = 1.0e10
    utility_ibi_fraction::Float64 = 0.0
    utility_ibi_max::Float64 = 1.0e10
    utility_rebate_per_ton::Float64 = 0.0
    utility_rebate_per_kw::Float64 = 0.0
    utility_rebate_max::Float64 = 1.0e10

    # Processed data from inputs and results of GhpGhx.jl
    heating_thermal_kw::Vector{Float64} = []
    cooling_thermal_kw::Vector{Float64} = []
    yearly_electric_consumption_kw::Vector{Float64} = []
    peak_combined_heatpump_thermal_ton::Float64 = NaN

    # Intermediate parameters for cost processing
    tech_sizes_for_cost_curve::Union{Float64, AbstractVector{Float64}} = NaN
    installed_cost_per_kw::Union{Float64, AbstractVector{Float64}} = NaN
    heatpump_capacity_ton::Float64 = NaN

    # Process and populate these parameters needed more directly by the model
    installed_cost::Float64 = NaN
    om_cost_year_one::Float64 = NaN
```
source
## SteamTurbine

`REopt.SteamTurbine` — Type

`SteamTurbine` is an optional REopt input with the following keys and default values:

```
    size_class::Union{Int64, Nothing} = nothing
    min_kw::Float64 = 0.0
    max_kw::Float64 = 1.0e9
    electric_produced_to_thermal_consumed_ratio::Float64 = NaN
    thermal_produced_to_thermal_consumed_ratio::Float64 = NaN
    is_condensing::Bool = false
    inlet_steam_pressure_psig::Float64 = NaN
    inlet_steam_temperature_degF::Float64 = NaN
    inlet_steam_superheat_degF::Float64 = 0.0
    outlet_steam_pressure_psig::Float64 = NaN
    outlet_steam_min_vapor_fraction::Float64 = 0.8  # Minimum practical vapor fraction of steam at the exit of the steam turbine
    isentropic_efficiency::Float64 = NaN
    gearbox_generator_efficiency::Float64 = NaN  # Combined gearbox (if applicable) and electric motor/generator efficiency
    net_to_gross_electric_ratio::Float64 = NaN  # Efficiency factor to account for auxiliary loads such as pumps, controls, lights, etc
    installed_cost_per_kw::Float64 = NaN   # Installed cost based on electric power capacity
    om_cost_per_kw::Float64 = 0.0  # Fixed O&M cost based on electric power capacity
    om_cost_per_kwh::Float64 = NaN  # Variable O&M based on electric energy produced
    production_incentive_per_kwh::Float64 = 0.0 # revenue from production incentive per kWh electricity produced, including curtailment
    production_incentive_max_benefit::Float64 = 1.0e9 # maximum allowable annual revenue from production incentives
    production_incentive_years::Int = 0 # number of year in which production incentives are paid
    production_incentive_max_kw::Float64 = 1.0e9 # maximum allowable system size to receive production incentives

    can_net_meter::Bool = false
    can_wholesale::Bool = false
    can_export_beyond_nem_limit::Bool = false
    can_curtail::Bool = false
    can_waste_heat::Bool = false
    can_serve_dhw::Bool = true
    can_serve_space_heating::Bool = true
    can_serve_process_heat::Bool = true
    charge_storage_only::Bool = false

    macrs_option_years::Int = 5 # Note that this value cannot be 0 if aiming to apply 100% bonus depreciation
    macrs_bonus_fraction::Float64 = 1.0
```
source
## ElectricHeater

`REopt.ElectricHeater` — Type

ElectricHeater

If a user provides the `ElectricHeater` key then the optimal scenario has the option to purchase this new `ElectricHeater` to meet the heating load in addition to using the `ExistingBoiler` to meet the heating load.

```
function ElectricHeater(;
    min_mmbtu_per_hour::Real = 0.0, # Minimum thermal power size
    max_mmbtu_per_hour::Real = BIG_NUMBER, # Maximum thermal power size
    installed_cost_per_mmbtu_per_hour::Union{Real, nothing} = nothing, # Thermal power-based cost
    om_cost_per_mmbtu_per_hour::Union{Real, nothing} = nothing, # Thermal power-based fixed O&M cost
    macrs_option_years::Int = 0, # MACRS schedule for financial analysis. Set to zero to disable
    macrs_bonus_fraction::Real = 0.0, # Fraction of upfront project costs to depreciate under MACRS
    can_supply_steam_turbine::Union{Bool, nothing} = nothing # If the boiler can supply steam to the steam turbine for electric production
    cop::Union{Real, nothing} = nothing # COP of the heating (i.e., thermal produced / electricity consumed)
    can_serve_dhw::Bool = true # If electric heater can supply heat to the domestic hot water load
    can_serve_space_heating::Bool = true # If electric heater can supply heat to the space heating load
    can_serve_process_heat::Bool = true # If electric heater can supply heat to the process heating load
)
```
source
## ASHPSpaceHeater

`REopt.ASHPSpaceHeater` — Function

ASHPSpaceHeater

If a user provides the `ASHPSpaceHeater` key then the optimal scenario has the option to purchase this new `ASHPSpaceHeater` to meet the heating load in addition to using the `ExistingBoiler` to meet the heating load.

```
function ASHPSpaceHeater(;
    min_ton::Real = 0.0, # Minimum thermal power size
    max_ton::Real = BIG_NUMBER, # Maximum thermal power size
    min_allowable_ton::Union{Real, Nothing} = nothing, # Minimum nonzero thermal power size if included
    min_allowable_peak_capacity_fraction::Union{Real, Nothing} = nothing, # minimum allowable fraction of peak heating + cooling load
    sizing_factor::::Union{Real, Nothing} = nothing, # Size multiplier of system, relative that of the max load given by dispatch profile
    om_cost_per_ton::Union{Real, nothing} = nothing, # Thermal power-based fixed O&M cost
    macrs_option_years::Int = 0, # MACRS schedule for financial analysis. Set to zero to disable
    macrs_bonus_fraction::Real = 0.0, # Fraction of upfront project costs to depreciate under MACRS
    can_serve_cooling::Union{Bool, Nothing} = nothing # If ASHP can supply heat to the cooling load
    force_into_system::Bool = false # force into system to serve all space heating loads if true
    force_dispatch::Bool = true # force ASHP to meet load or maximize output if true
    avoided_capex_by_ashp_present_value::Real = 0.0 # avoided capital expenditure due to presence of ASHP system vs. defaults heating and cooling techs

    #The following inputs are used to create the attributes heating_cop and heating cf:
    heating_cop_reference::Array{<:Real,1}, # COP of the heating (i.e., thermal produced / electricity consumed)
    heating_cf_reference::Array{<:Real,1}, # ASHP's heating capacity factor curves
    heating_reference_temps_degF ::Array{<:Real,1}, # ASHP's reference temperatures for heating COP and CF
    back_up_temp_threshold_degF::Real = 10, # Degree in F that system switches from ASHP to resistive heater

    #The following inputs are used to create the attributes cooling_cop and cooling cf:
    cooling_cop::Array{<:Real,1}, # COP of the cooling (i.e., thermal produced / electricity consumed)
    cooling_cf::Array{<:Real,1}, # ASHP's cooling capacity factor curves
    cooling_reference_temps_degF ::Array{<:Real,1}, # ASHP's reference temperatures for cooling COP and CF

    #The following inputs are taken from the Site object:
    ambient_temp_degF::Array{<:Real,1}  #time series of ambient temperature
    heating_load::Array{Real,1} # time series of site space heating load
    cooling_load::Union{Array{Real,1}, Nothing} # time series of site cooling load
)
```
source
## ASHPWaterHeater

`REopt.ASHPWaterHeater` — Function

ASHPWaterHeater

If a user provides the `ASHPWaterHeater` key then the optimal scenario has the option to purchase this new `ASHPWaterHeater` to meet the domestic hot water load in addition to using the `ExistingBoiler` to meet the domestic hot water load.

```
function ASHPWaterHeater(;
    min_ton::Real = 0.0, # Minimum thermal power size
    max_ton::Real = BIG_NUMBER, # Maximum thermal power size
    min_allowable_ton::Real = 0.0 # Minimum nonzero thermal power size if included
    installed_cost_per_ton::Union{Real, nothing} = nothing, # Thermal power-based cost
    om_cost_per_ton::Union{Real, nothing} = nothing, # Thermal power-based fixed O&M cost
    macrs_option_years::Int = 0, # MACRS schedule for financial analysis. Set to zero to disable
    macrs_bonus_fraction::Real = 0.0, # Fraction of upfront project costs to depreciate under MACRS
    can_supply_steam_turbine::Union{Bool, nothing} = nothing # If the boiler can supply steam to the steam turbine for electric production
    avoided_capex_by_ashp_present_value::Real = 0.0 # avoided capital expenditure due to presence of ASHP system vs. defaults heating and cooling techs
    force_into_system::Bool = false # force into system to serve all hot water loads if true
    force_dispatch::Bool = true # force ASHP to meet load or maximize output if true

    #The following inputs are used to create the attributes heating_cop and heating cf:
    heating_cop_reference::Array{<:Real,1}, # COP of the heating (i.e., thermal produced / electricity consumed)
    heating_cf_reference::Array{<:Real,1}, # ASHP's heating capacity factor curves
    heating_reference_temps_degF ::Array{<:Real,1}, # ASHP's reference temperatures for heating COP and CF
    back_up_temp_threshold_degF::Real = 10 # temperature threshold at which backup resistive heater is used

    #The following inputs are taken from the Site object:
    ambient_temp_degF::Array{<:Real,1} = Float64[] # time series of ambient temperature
    heating_load::Array{<:Real,1} # time series of site domestic hot water load
)
```
source
## CST

`REopt.CST` — Type
```
CST
```

If a user provides the `CST` key then the optimal scenario has the option to purchase this new `CST` technology to meet compatible heating loads in addition to using the `ExistingBoiler` to meet the heating load(s).

```
function CST(;
    min_kw::Real = 0.0, # Minimum thermal power size (capacity)
    max_kw::Real = BIG_NUMBER, # Maximum thermal power size (capacity)
    production_factor::AbstractVector{<:Real} = Float64[],  production factor
    elec_consumption_factor_series::AbstractVector{<:Real} = Float64[], electric consumption factor per kw TODO: (do we need? are we including parasitics?)
    acres_per_kw::Union{Real,Nothing} = nothing, #
    macrs_option_years::Union{Int,Nothing} = nothing, # MACRS schedule for financial analysis. Set to zero to disable
    macrs_bonus_fraction::Union{Real,Nothing} = nothing, # Fraction of upfront project costs to depreciate under MACRS
    installed_cost_per_kw::Union{Real,Nothing} = nothing, # Thermal power-based cost, see cst_defaults.json for CST default by type
    om_cost_per_kw::Union{Real,Nothing} = nothing, # Thermal power-based fixed O&M cost, see cst_defaults.json for CST default by type
    om_cost_per_kwh::Union{Real,Nothing} = nothing, # Thermal energy produced-based variable O&M cost
    tech_type::Union{String,Nothing} = nothing,  # restrict to: ["ptc", "mst", "lf", "swh_evactube", "swh_flatplate"]
    can_supply_steam_turbine::Union{Bool,Nothing} = nothing # If the CST can supply steam to the steam turbine for electric production
    can_serve_dhw::Union{Bool,Nothing} = nothing # If CST can supply heat to the domestic hot water load
    can_serve_space_heating::Union{Bool,Nothing} = nothing # If CST can supply heat to the space heating load
    can_serve_process_heat::Union{Bool,Nothing} = nothing # If CST can supply heat to the process heating load
    can_waste_heat::Union{Bool,Nothing} = nothing # If CST can curtail excess heat
    charge_storage_only::Union{Bool,Nothing} = nothing # If CST can only supply hot TES (i.e., cannot meet load directly)
    emissions_factor_lb_CO2_per_mmbtu::Real = 0.0
    emissions_factor_lb_NOx_per_mmbtu::Real = 0.0
    emissions_factor_lb_SO2_per_mmbtu::Real = 0.0
    emissions_factor_lb_PM25_per_mmbtu::Real = 0.0
    inlet_temp_degF::Real = 400.0 # heat transfer medium temperature at inlet of CST heat offtaker (e.g., inlet to HTF hot tank or industrial process)
    outlet_temp_degF::Real = 70.0 # heat transfer medium temperature at outlet of CST heat offtaker (e.g., HTF cold tank storage)
)
```
source
