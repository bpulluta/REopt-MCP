# Methods Bundle

## Bundle Summary

- Documents: 2
- Chunks: 6

## Document Index

- 1. REopt Methods (https://natlabrockies.github.io/REopt.jl/dev/reopt/methods/)
- 2. MPC Methods (https://natlabrockies.github.io/REopt.jl/dev/mpc/methods/)

## Documents

### 1. REopt Methods

Source: https://natlabrockies.github.io/REopt.jl/dev/reopt/methods/

#### Methods

The primary method for using REopt is the `run_reopt` method. In the simplest there are two required inputs to `run_reopt`: a `JuMP.Model` with an optimizer and the path to a JSON file to define the `Scenario`. Other methods for `run_reopt` are enumerated below. Other methods such as `build_reopt!` are also described to allow users to build custom REopt models. For example, after using `build_reopt!` a user could add constraints or change the objective function using `JuMP` commands.

#### run_reopt

`REopt.run_reopt` — Function
```julia
run_reopt(m::JuMP.AbstractModel, fp::String)
```

Solve the model using the `Scenario` defined in JSON file stored at the file path `fp`.

```julia
run_reopt(m::JuMP.AbstractModel, d::Dict)
```

Solve the model using the `Scenario` defined in dict `d`.

```julia
run_reopt(m::JuMP.AbstractModel, s::AbstractScenario)
```

Solve the model using a `Scenario` or `BAUScenario`.

```julia
run_reopt(t::Tuple{JuMP.AbstractModel, AbstractScenario})
```

Method for use with Threads when running BAU in parallel with optimal scenario.

```julia
run_reopt(ms::AbstractArray{T, 1}, fp::String) where T <: JuMP.AbstractModel
```

Solve the `Scenario` and `BAUScenario` in parallel using the first two (empty) models in `ms` and inputs defined in the JSON file at the filepath `fp`.

```julia
run_reopt(ms::AbstractArray{T, 1}, d::Dict) where T <: JuMP.AbstractModel
```

Solve the `Scenario` and `BAUScenario` in parallel using the first two (empty) models in `ms` and inputs from `d`.

```julia
run_reopt(ms::AbstractArray{T, 1}, p::REoptInputs) where T <: JuMP.AbstractModel
```

Solve the `Scenario` and `BAUScenario` in parallel using the first two (empty) models in `ms` and inputs from `p`.

#### build_reopt!

`REopt.build_reopt!` — Function
```julia
build_reopt!(m::JuMP.AbstractModel, fp::String)
```

Add variables and constraints for REopt model. `fp` is used to load in JSON file to construct REoptInputs.

```julia
build_reopt!(m::JuMP.AbstractModel, p::REoptInputs)
```

Add variables and constraints for REopt model.

#### simulate_outages

`REopt.simulate_outages` — Function
```
simulate_outages(;batt_kwh=0, batt_kw=0, pv_kw_ac_hourly=[], init_soc=[], critical_loads_kw=[],
    wind_kw_ac_hourly=[], batt_roundtrip_efficiency=0.829, diesel_kw=0, fuel_available=0, b=0, m=0,
    diesel_min_turndown=0.3
)
```

Time series simulation of outages starting at every time step of the year. Used to calculate how many time steps the critical load can be met in every outage, which in turn is used to determine probabilities of meeting the critical load.

**Arguments**

- `batt_kwh`: float, battery storage capacity
- `batt_kw`: float, battery inverter capacity
- `pv_kw_ac_hourly`: list of floats, AC production of PV system
- `init_soc`: list of floats between 0 and 1 inclusive, initial state-of-charge
- `critical_loads_kw`: list of floats
- `wind_kw_ac_hourly`: list of floats, AC production of wind turbine
- `batt_roundtrip_efficiency`: roundtrip battery efficiency
- `diesel_kw`: float, diesel generator capacity
- `fuel_available`: float, gallons of diesel fuel available
- `b`: float, diesel fuel burn rate intercept coefficient (y = m*x + b*rated_capacity) [gal/kwh/kw]
- `m`: float, diesel fuel burn rate slope (y = m*x + b*rated_capacity) [gal/kWh]
- `diesel_min_turndown`: minimum generator turndown in fraction of generator capacity (0 to 1)

Returns a dict

```
    "resilience_by_time_step": vector of time steps that critical load is met for outage starting in every time step,
    "resilience_hours_min": minimum of "resilience_by_time_step",
    "resilience_hours_max": maximum of "resilience_by_time_step",
    "resilience_hours_avg": average of "resilience_by_time_step",
    "outage_durations": vector of integers for outage durations with non zero probability of survival,
    "probs_of_surviving": vector of probabilities corresponding to the "outage_durations",
    "probs_of_surviving_by_month": vector of probabilities calculated on a monthly basis,
    "probs_of_surviving_by_hour_of_the_day":vector of probabilities calculated on a hour-of-the-day basis,
}
```

```julia
simulate_outages(d::Dict, p::REoptInputs; microgrid_only::Bool=false)
```

Time series simulation of outages starting at every time step of the year. Used to calculate how many time steps the critical load can be met in every outage, which in turn is used to determine probabilities of meeting the critical load.

**Arguments**

- `d`::Dict from `reopt_results`
- `p`::REoptInputs the inputs that generated the Dict from `reopt_results`
- `microgrid_only`::Bool whether or not to simulate only the optimal microgrid capacities or the total capacities. This input is only relevant when modeling multiple outages.

Returns a dict

```json
{
    "resilience_by_time_step": vector of time steps that critical load is met for outage starting in every time step,
    "resilience_hours_min": minimum of "resilience_by_time_step",
    "resilience_hours_max": maximum of "resilience_by_time_step",
    "resilience_hours_avg": average of "resilience_by_time_step",
    "outage_durations": vector of integers for outage durations with non zero probability of survival,
    "probs_of_surviving": vector of probabilities corresponding to the "outage_durations",
    "probs_of_surviving_by_month": vector of probabilities calculated on a monthly basis,
    "probs_of_surviving_by_hour_of_the_day":vector of probabilities calculated on a hour-of-the-day basis,
}
```

#### backup_reliability

`REopt.backup_reliability` — Function
```julia
backup_reliability(d::Dict, p::REoptInputs, r::Dict)
```

Return dictionary of backup reliability results.

**Arguments**

- `d::Dict`: REopt results dictionary. Subhourly time steps are not yet supported.
- `p::REoptInputs`: REopt Inputs Struct.
- `r::Dict`: Dictionary of inputs for reliability calculations. If r not included then uses all defaults.

Possible keys in r: -generator*operational*availability::Real = 0.995 Fraction of year generators not down for maintenance -generator*failure*to*start::Real = 0.0094 Chance of generator starting given outage -generator*mean*time*to*failure::Real = 1100 Average number of time steps between a generator's failures. 1/(failure to run probability). -num*generators::Int = 1 Number of generators. -generator*size*kw::Real = 0.0 Backup generator capacity. -num*battery*bins::Int = depends on battery sizing Number of bins for discretely modeling battery state of charge -battery*operational*availability::Real = 0.97 Likelihood battery will be available at start of outage -pv*operational*availability::Real = 0.98 Likelihood PV will be available at start of outage -wind*operational*availability::Real = 0.97 Likelihood Wind will be available at start of outage -max*outage*duration::Int = 96 Maximum outage duration modeled -microgrid_only::Bool = false Determines how generator, PV, and battery act during islanded mode

```julia
backup_reliability(r::Dict)
```

Return dictionary of backup reliability results.

**Arguments**

- `r::Dict`: Dictionary of inputs for reliability calculations. If r not included then uses all defaults.

Possible keys in r: -critical*loads*kw::Array Critical loads per time step. Must be hourly and have length of 8760. (Required input) -microgrid*only::Bool Boolean to check if only microgrid runs during grid outage (defaults to false) -chp*size*kw::Real CHP capacity. -pv*size*kw::Real Size of PV System -pv*production*factor*series::Array PV production factor per time step. Must be hourly and have length of 8760. (Required if pv*size*kw in dictionary) -pv*migrogrid*upgraded::Bool If true then PV runs during outage if microgrid*only = TRUE (defaults to false) -battery*size*kw::Real Battery capacity. If no battery installed then PV disconnects from system during outage -battery*size*kwh::Real Battery energy storage capacity -battery*charge*efficiency::Real Battery charge efficiency -battery*discharge*efficiency::Real Battery discharge efficiency -battery*starting*soc*series*fraction::Array Battery percent state of charge time series during normal grid-connected usage. Must be hourly and have length of 8760. -generator*failure*to*start::Real = 0.0094 Chance of generator starting given outage -generator*mean*time*to*failure::Real = 1100 Average number of time steps between a generator's failures. 1/(failure to run probability). -num*generators::Int = 1 Number of generators. -generator*size*kw::Real = 0.0 Backup generator capacity. -num*battery*bins::Int = num*battery*bins*default(r[:battery*size*kw],r[:battery*size*kwh]) Number of bins for discretely modeling battery state of charge -max*outage*duration::Int = 96 Maximum outage duration modeled

### 2. MPC Methods

Source: https://natlabrockies.github.io/REopt.jl/dev/mpc/methods/

#### Methods

`REopt.run_mpc` — Function
```julia
run_mpc(m::JuMP.AbstractModel, fp::String)
```

Solve the model predictive control problem using the `MPCScenario` defined in the JSON file stored at the file path `fp`.

Returns a Dict of results with keys matching those in the `MPCScenario`.

```julia
run_mpc(m::JuMP.AbstractModel,  d::Dict)
```

Solve the model predictive control problem using the `MPCScenario` defined in the dict `d`.

Returns a Dict of results with keys matching those in the `MPCScenario`.

```julia
run_mpc(m::JuMP.AbstractModel, p::MPCInputs)
```

Solve the model predictive control problem using the `MPCInputs`.

Returns a Dict of results with keys matching those in the `MPCScenario`.

```julia
run_mpc(m::JuMP.AbstractModel, ps::AbstractVector{MPCInputs})
```

Solve the model predictive control problem using multiple `MPCInputs`.

Returns a Dict of results with keys matching those in the `MPCScenario`.

`REopt.build_mpc!` — Function
```julia
build_mpc!(m::JuMP.AbstractModel, p::MPCInputs)
```

Add variables and constraints for model predictive control model. Similar to a REopt model but with any length of horizon (instead of one calendar year), and the DER sizes must be provided.

```julia
build_mpc!(m::JuMP.AbstractModel, ps::AbstractVector{MPCInputs})
```

Add variables and constraints for model predictive control model of multiple nodes. Similar to a REopt model but with any length of horizon (instead of one calendar year), and the DER sizes must be provided.
