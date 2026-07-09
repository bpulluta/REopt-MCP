# Developer Bundle

## Bundle Summary

- Documents: 5
- Chunks: 31

## Document Index

- 1. Adding a Technology (https://natlabrockies.github.io/REopt.jl/dev/developer/adding_tech/)
- 2. Design Concepts for the REopt Module (https://natlabrockies.github.io/REopt.jl/dev/developer/concept/)
- 3. Documenting the Code (https://natlabrockies.github.io/REopt.jl/dev/developer/documentation/)
- 4. The REoptInputs structure (https://natlabrockies.github.io/REopt.jl/dev/developer/inputs/)
- 5. File Organization (https://natlabrockies.github.io/REopt.jl/dev/developer/organization/)

## Documents

### 1. Adding a Technology

Source: https://natlabrockies.github.io/REopt.jl/dev/developer/adding_tech/

#### Adding a Technology

REopt can be used in many ways, but its primary use is to evaluate the techno-economic feasibility of energy generation and storage technologies. In this section we describe how one might add a new technology to the REopt model for evaluation. At a high level the steps are:

1. Define the mathematical model for how the technology will interact with the other technologies, which includes:
   - defining appropriate decision variables (the technology's capacity for example)
   - defining model constraints (operational constraints for example)
2. Define the inputs and default values necessary to model the technology in the mathematical model
3. Map the input values to the sets and coefficients needed in the mathematical model
4. Create an adapter function to output the desired results from the mathematical model
5. Test the new technology
6. Document the new inputs and outputs functions

All steps are not necessarily executed in this order and in fact most likely must be done in concert. For example, in order to define a model constraint one must define the input parameters. Also, it is good practice to think of how you will test the new technology from the very beginning of the design process and incrementally test your additions to the model as well as make sure that no existing tests fail due to your modifications to REopt.

#### 1. Mathematical Model

Each technology will have unique decision variables and constraints. However, there are some decision variables that apply to many technologies. We will use the `PV` technology to demonstrate some variables and constraints that are shared among all generation technologies and some that are unique to `PV`.

First, the `PV` technology can meet electrical demand and thus is part of the `techs.elec`. By including the `PV` technology in the set of `techs.elec` we can take advantage of existing model constraints such as the electrical load balance:

```
@constraint(m, [ts in p.time_steps_with_grid],
    sum(p.production_factor[t, ts] * p.levelization_factor[t] * m[Symbol("dvRatedProduction"*_n)][t,ts] for t in p.techs.elec)
    + sum( m[Symbol("dvDischargeFromStorage"*_n)][b,ts] for b in p.s.storage.types.elec )
    + sum(m[Symbol("dvGridPurchase"*_n)][ts, tier] for tier in 1:p.s.electric_tariff.n_energy_tiers)
    ==
    sum( sum(m[Symbol("dvProductionToStorage"*_n)][b, t, ts] for b in p.s.storage.types.elec)
    + m[Symbol("dvCurtail"*_n)][t, ts] for t in p.techs.elec)
    + sum(m[Symbol("dvGridToStorage"*_n)][b, ts] for b in p.s.storage.types.elec)
    + p.s.electric_load.loads_kw[ts]
)
```

From the load balance constraint we can see that the `PV` technology (and each `techs.elec`) includes input parameters for the `production_factor` and `levelization_factor`, and that the `PV` technology has the decision variables `dvRatedProduction` and `dvCurtail`.

The `p.techs` data structure is defined as follows:

#### Techs

`REopt.Techs` — Type
```
Techs
```

`Techs` contains the index sets that are used to define the model constraints and decision variables.

```julia
mutable struct Techs
    all::Vector{String}
    elec::Vector{String}
    pv::Vector{String}
    gen::Vector{String}
    pbi::Vector{String}
    no_curtail::Vector{String}
    no_turndown::Vector{String}
    segmented::Vector{String}
    heating::Vector{String}
    cooling::Vector{String}
    boiler::Vector{String}
    fuel_burning::Vector{String}
    thermal::Vector{String}
    chp::Vector{String}
    requiring_oper_res::Vector{String}
    providing_oper_res::Vector{String}
    electric_chiller::Vector{String}
    absorption_chiller::Vector{String}
    steam_turbine::Vector{String}
    can_supply_steam_turbine::Vector{String}
    electric_heater::Vector{String}
    can_serve_space_heating::Vector{String}
    can_serve_dhw::Vector{String}
    can_serve_process_heat::Vector{String}
    ghp::Vector{String}
    ashp::Vector{String}
    ashp_wh::Vector{String}
end
```
`REopt.Techs` — Method
```julia
Techs(s::Scenario)
```

Create a `Techs` struct for the REoptInputs.

`REopt.Techs` — Method
```julia
Techs(p::REoptInputs, s::BAUScenario)
```

Create a `Techs` struct for the BAUInputs

From the Techs definition we can see that there are already a lot of different energy generation technology categories in REopt. Adding a new technology to the model could be as simple as adding the appropriate inputs to `REoptInputs` (described in the next section) and using the `Techs` structure to define which variables and constraints apply to the new technology.

The `PV` technology is also part of a unique set of `Techs`, namely the `techs.pv` (there can be multiple `PV` technologies in a single model as we will see soon). An example of a constraint applied over `techs.pv` is:

```
@constraint(m, [loc in p.pvlocations],
    sum(m[Symbol("dvSize"*_n)][t] * p.pv_to_location[t][loc] for t in p.techs.pv) <= p.maxsize_pv_locations[loc]
)
```

Here we can see that the `dvSize` for each `techs.pv` is constrained based on the location of each `PV` technology. This constraint allows us to uniquely limit the `PV` capacity for roof mounted systems vs. ground mounted systems based on the available space at a site. We also see some additional inputs for the `PV` technology, such as the `pvlocations` and `maxsize_pv_locations`. Creating these input values is described in the next two sections.

#### 2. User Inputs

Any new technology should have a `technologyname.jl` file in the `src/core` directory. For example, in the `src/core/pv.jl` file we have a data structure and constructor for defining default values and creating the `PV` structure that is attached to the Scenario. Once the new technology's data structure is defined it must be added to the `Scenario` structure (see `src/core/scenario.jl`).

When adding a new technology to REopt one must decide on how a user of the REopt will define the technology. Continuing with the `PV` example we saw that we need to define the `production_factor` for the `PV` technology in every time step. The `production_factor` varies from zero to one and defines the availability of the technology. For `PV` we have a default method for creating the `production_factor` as well as allow the user to provide their own `production_factor`.

We let the user define the `production_factor` by providing the `PV`s `production_factor_series` input in their JSON file or dictionary when creating their Scenario. If the user does not provide a value for `production_factor_series` then we use the PVWatts API to get a `production_factor` based on the `Site.latitude` and `Site.longitude`. The PV inputs structure also allows the user to change the arguments that are passed to PVWatts.

#### 3. REopt Inputs

The REoptInputs constructor is the work-horse for defining all the mathematical model parameters. It converts the user's Scenario into a format that is necessary for adding the model decision variables and constraints.

A major part of the REoptInputs constructor is creating arrays that are indexed on sets of strings (defined in Techs) that allow us to define constraints all applicable technologies. Continuing with the `PV` example, the electrical load balance constraint includes:

```
sum(p.production_factor[t, ts] * p.levelization_factor[t] * m[Symbol("dvRatedProduction"*_n)][t,ts] for t in p.techs.elec)
```

which implies that we need to define a `production_factor` for all `techs.elec` in every time step `ts`. To create the `production_factor` array the REoptInputs constructor first creates an empty array like so:

```
production_factor = DenseAxisArray{Float64}(undef, techs.all, 1:length(s.electric_load.loads_kw))
```

and then passes that array to technology specific functions that add their production factors to the `production_factor` array. For example, for `PV` within the `setup_pv_inputs` method we have:

```
for pv in s.pvs
    production_factor[pv.name, :] = get_production_factor(pv, s.site.latitude, s.site.longitude)
    ...
end
```

The completed `production_factor` array is then attached to the `REoptInputs` structure so that it can be used as needed to create the mathematical model.

#### 4. Results

After adding a new technology to the REopt mathematical model and getting the new inputs set up you can create some results from the optimized model. Some or all of your new results can also be used in a test for the new technology.

All of the results methods are defined in `src/results`, with `src/results/results.jl` containing the main method for creating results. The results are returned to the user as a dictionary. If a user is not modeling your new technology then there is no reason to create any new results. Therefore, in `reopt_results` we have:

```
if !isempty(p.techs.pv)
    add_pv_results(m, p, d; _n)
end
```

which uses the model `m` and the `REoptInputs` `p` to add results to the dictionary `d`.

#### 5. Testing the new technology

Adding a new test is not necessarily the last step in adding a technology to the REopt model. In fact, it is best to use a simple test to test your code as you add the new technolgy and then adapt the test as you add more capability to the code. For example, once you have created you new technology's input interface you can test just creating a `Scenario` with the new technology by passing the path to a JSON file that contains the minimum required inputs for a Scenario and your new technology. This might look like:

```
@testset "My new technology" begin
    s = Scenario("path/to/mynewtech.json")
end
```

The next testing step might be checking the `REoptInputs` additions for your new technolgy:

```
@testset "My new technology" begin
    s = Scenario("path/to/mynewtech.json")
    p = REoptInputs(s)
end
```

Once you have all of your new inputs set up you can test the model creation with:

```
@testset "My new technology" begin
    m = Model(Cbc.Optimizer)
    build_reopt!(m, "path/to/mynewtech.json")
end
```

Finally, you can test the full work-flow with something like:

```
@testset "My new technology" begin
    m = Model(Cbc.Optimizer)
    results = run_reopt(m, "path/to/mynewtech.json")
    @test results["mynewtech"]["some_result"] ≈ 78.9 atol=0.1
end
```

### 2. Design Concepts for the REopt Module

Source: https://natlabrockies.github.io/REopt.jl/dev/developer/concept/

#### Design Concepts for the REopt Module

At a high level each REopt model consists of four major components:

1. The Scenario as defined by the user's inputs and default values.
2. The REoptInputs, which convert the `Scenario` into the necessary values for the REopt mathematical program.
3. The REopt Model (built here), which includes all the constraints and the objective function that are built using the REoptInputs
4. And the results, which are returned to the user and derived from the optimal solution of the REopt Model.

The REopt Model is built via the build_reopt! method. However, the run_reopt method includes `build_reopt!` within it so typically a user does not need to directly call `build_reopt!` (unless they wish to modify the model before solving it, eg. by adding a constraint).

run_reopt is the main interface for users.

#### Upper size limits

The `max_kw` input value for any technology is considered to be the maximum *additional* capacity that may be installed beyond the `existing_kw`. Note also that the `Site` space constraints (`roof_squarefeet` and `land_acres`) for `PV` technologies can be less than the provided `max_kw` value.

#### Lower size limits

The `min_kw` input value for any technology sets the lower bound on the capacity. If `min_kw` is non-zero then the model will be forced to choose at least that system size. The `min_kw` value is set equal to the `existing_kw` value in the Business As Usual scenario.

#### Business As Usual Scenario

In order to calculate the Net Present Value of the optimal solution, as well as other baseline metrics, one can optionally run the Business As Usual (BAU) scenario. When an array of `JuMP.Model`s is provided to `run_reopt` the BAU scenario is also run. For example:

```
m1 = Model(optimizer_with_attributes(Xpress.Optimizer, "OUTPUTLOG" => 0))
m2 = Model(optimizer_with_attributes(Xpress.Optimizer, "OUTPUTLOG" => 0))
results = run_reopt([m1,m2], "./scenarios/pv_storage.json")
```

The BAU scenario is created by modifying the REoptInputs (created from the user's Scenario). In the BAU scenario we have the following assumptions:

- Each existing technology has zero capital cost, but does have operations and maintenance costs.
- The ElectricTariff, Financial, Site, ElectricLoad, and ElectricUtility inputs are the same as the optimal case.
- The `min_kw` and `max_kw` values are set to the `existing_kw` value.

### 3. Documenting the Code

Source: https://natlabrockies.github.io/REopt.jl/dev/developer/documentation/

#### Documenting the Code

Besides the primary methods for using REopt.jl (which are documented in docs/reopt/methods.md) users need to know what inputs and outputs are available. The REopt.jl package and the REopt API v3 and later are designed to have the same input and output names so that a user can in theory use the same JSON or dictionary inputs to either REopt.jl or the API and get the same results (assuming that the same version of REopt.jl is used in both cases).

In many cases the REopt.jl package will lead the development of the API, that is a new capability in REopt is first developed in the Julia package, and then if necessary that capability is added to the API (and the webtool after that if necessary). This means that REopt.jl and the API will not always have the same inputs (and outputs).

#### Inputs

For each of the structs that are attached to the `Scenario` struct we document the input fields, their types, and default values if any. In some cases documenting inputs can be as simple as copying and pasting the function signature that builds the input struct into the doc string of the function. However, there are some cases in which a function contains input fields that are not meant to be provided/accessed by a user. For example, the `Site.latitude` input is used in many other input constructors, such as in `PV` to look up the PVWatts production factor, but the user does not need to provide a `PV.latitude` input. In these cases one should not include all of the function signature fields in the doc string.

Any new input function and/or struct must be added to the docs/reopt/inputs.md file for it to show up in the online documentation (see that file for examples).

For describing how to use more complicated inputs use a `note` admonition like:

#### Outputs

All of the results functions should have a list of output fields with descriptions in a bulleted list in the function doc string. When adding a new results function it should be added to the docs/reopt/outputs.md file so that it shows up in the online documentation. There is no need to include the function signature in the doc string.

#### Testing Documentation

Test documentation changes locally to confirm they are working as intended. See docs/README.md for instructions. If Documenter cannot find your doc strings, ensure that there is no extra line between the doc string and the function.

### 4. The REoptInputs structure

Source: https://natlabrockies.github.io/REopt.jl/dev/developer/inputs/

#### The REoptInputs structure

The REoptInputs structure uses the Scenario to build all of the data necessary to construct the JuMP mathematical model.

#### REoptInputs

`REopt.REoptInputs` — Type
```
REoptInputs
```

The data structure for all the inputs necessary to construct the JuMP model.

```julia
struct REoptInputs <: AbstractInputs
    s::ScenarioType
    techs::Techs
    min_sizes::Dict{String, <:Real}  # (techs)
    max_sizes::Dict{String, <:Real}  # (techs)
    existing_sizes::Dict{String, <:Real}  # (techs)
    cap_cost_slope::Dict{String, Any}  # (techs)
    om_cost_per_kw::Dict{String, <:Real}  # (techs)
    thermal_cop::Dict{String, <:Real}  # (techs.absorption_chiller)
    time_steps::UnitRange
    time_steps_with_grid::Array{Int, 1}
    time_steps_without_grid::Array{Int, 1}
    hours_per_time_step::Real
    months::UnitRange
    production_factor::DenseAxisArray{<:Real, 2}  # (techs, time_steps)
    levelization_factor::Dict{String, <:Real,}  # (techs)
    value_of_lost_load_per_kwh::Array{<:Real, 1}
    pwf_e::Real
    pwf_om::Real
    pwf_fuel::Dict{String, <:Real}
    pwf_emissions_cost::Dict{String, Float64} # Cost of emissions present worth factors for grid and onsite fuelburn emissions [unitless]
    pwf_grid_emissions::Dict{String, Float64} # Emissions [lbs] present worth factors for grid emissions [unitless]
    pwf_offtaker::Real
    pwf_owner::Real
    third_party_factor::Real
    pvlocations::Array{Symbol, 1}
    maxsize_pv_locations::DenseAxisArray{<:Real, 1}  # indexed on pvlocations
    pv_to_location::Dict{String, Dict{Symbol, Int64}}  # (techs.pv, pvlocations)
    ratchets::UnitRange
    techs_by_exportbin::Dict{Symbol, AbstractArray}  # keys can include [:NEM, :WHL, :CUR]
    export_bins_by_tech::Dict
    n_segs_by_tech::Dict{String, Int}
    seg_min_size::Dict{String, Dict{Int, <:Real}}
    seg_max_size::Dict{String, Dict{Int, <:Real}}
    seg_yint::Dict{String, Dict{Int, <:Real}}
    pbi_pwf::Dict{String, Any}  # (pbi_techs)
    pbi_max_benefit::Dict{String, Any}  # (pbi_techs)
    pbi_max_kw::Dict{String, Any}  # (pbi_techs)
    pbi_benefit_per_kwh::Dict{String, Any}  # (pbi_techs)
    boiler_efficiency::Dict{String, <:Real}
    fuel_cost_per_kwh::Dict{String, AbstractArray}  # Fuel cost array for all time_steps
    ghp_options::UnitRange{Int64}  # Range of the number of GHP options
    require_ghp_purchase::Int64  # 0/1 binary if GHP purchase is forced/required
    ghp_heating_thermal_load_served_kw::Array{Float64,2}  # Array of heating load (thermal!) profiles served by GHP
    ghp_cooling_thermal_load_served_kw::Array{Float64,2}  # Array of cooling load profiles served by GHP
    space_heating_thermal_load_reduction_with_ghp_kw::Array{Float64,2}  # Array of heating load reduction (thermal!) profile from GHP retrofit
    cooling_thermal_load_reduction_with_ghp_kw::Array{Float64,2}  # Array of cooling load reduction (thermal!) profile from GHP retrofit
    ghp_electric_consumption_kw::Array{Float64,2}  # Array of electric load profiles consumed by GHP
    ghp_installed_cost::Array{Float64,1}  # Array of installed cost for GHP options
    ghp_om_cost_year_one::Array{Float64,1}  # Array of O&M cost for GHP options
    tech_renewable_energy_fraction::Dict{String, <:Real} # union(techs.elec, techs.fuel_burning)
    tech_emissions_factors_CO2::Dict{String, <:Real} # (techs)
    tech_emissions_factors_NOx::Dict{String, <:Real} # (techs)
    tech_emissions_factors_SO2::Dict{String, <:Real} # (techs)
    tech_emissions_factors_PM25::Dict{String, <:Real} # (techs)
    techs_operating_reserve_req_fraction::Dict{String, <:Real} # (techs.all)
    heating_cop::Dict{String, Array{<:Real, 1}} # (techs.ashp)
    cooling_cop::Dict{String, Array{<:Real, 1}} # (techs.ashp)
    heating_cf::Dict{String, Array{<:Re

al, 1}} # (techs.ashp)
    cooling_cf::Dict{String, Array{<:Real, 1}} # (techs.ashp)
    heating_loads_kw::Dict{String, <:Real} # (heating_loads)
    unavailability::Dict{String, Array{Float64,1}}  # Dict by tech of unavailability profile
end
```
`REopt.REoptInputs` — Method
```julia
REoptInputs(fp::String)
```

Use `fp` to load in JSON scenario:

```julia
function REoptInputs(fp::String)
    s = Scenario(JSON.parsefile(fp))
    REoptInputs(s)
end
```

Useful if you want to manually modify REoptInputs before solving the model.

`REopt.REoptInputs` — Method
```julia
REoptInputs(s::AbstractScenario)
```

Constructor for REoptInputs. Translates the `Scenario` into all the data necessary for building the JuMP model.

#### Design Concepts for REoptInputs

At a high level the REoptInputs constructor does the following tasks:

- build index sets for the JuMP model decision variables,
- create maps from one set to another set,
- and generate coefficient arrays necessary for model constraints.

#### Index Sets

There are a few `String[]` that are built by REoptInputs that are then used as index sets in the model constraints. The primary index set is the `techs.all` array of strings, which contains all the technolgy names that are being modeled. With the `techs.all` array we can easily apply a constraint over all technolgies. For example:

```
@constraint(m, [t in p.techs.all],
    m[Symbol("dvSize"*_n)][t] <= p.max_sizes[t]
)
```

where `p` is the `REoptInputs` struct. There are a couple things to note from this last example:

1. The decision variable `dvSize` is accessed in the JuMP.Model `m` using the `Symbol` notation so that this constraint can be used in the multi-node case in addition to the single node case. The `_n` input value is an empty string by default and in the case of a multi-node model the `_n` string will be set by the `Site.node` integer. For example, if `Site.node` is `3` then `_n` is "_3".
2. The `p.max_sizes` array is also indexed on `p.techs.all`. The `max_sizes` is built in the REoptInputs constructor by using all the technologies in the `Scenario` that have `max_kw` values greater than zero.

Besides the `techs.all` array the are many sub-sets, such as `techs.pv`, `techs.gen`, `techs.elec`, `p.techs.segmented`, `techs.no_curtail`, that allow us to apply constraints to those sets. For example:

```
for t in p.techs.no_curtail
    for ts in p.time_steps
        fix(m[Symbol("dvCurtail"*_n)][t, ts] , 0.0, force=true)
    end
end
```

#### Set maps

The set maps are best explained with an example. The `techs_by_exportbin` map uses each technology'sattributes (eg. `PV`) to map each technology to which export bins that technology can access. The export bins include:

1. `:NEM` (Net Energy Metering)
2. `:WHL` (Wholesale)
3. `:EXC` (Excess, beyond NEM))

The bins that a technology can access are determined by the technologies attributes `can_net_meter`, `can_wholesale`, and `can_export_beyond_nem_limit`. So if `PV.can_net_meter = true`, `Wind.can_net_meter = true` and all the other attributes are `false` then the `techs_by_exportbin` will only have one non-empty key:

```
techs_by_exportbin = Dict(
    :NEM => ["PV", "Wind"],
    :WHL => [],
    :EXC => []
)
```

A use-case example for the `techs_by_exportbin` map is defining the net metering benefit:

```
NEM_benefit = @expression(m, p.pwf_e * p.hours_per_time_step *
    sum( sum(p.s.electric_tariff.export_rates[:NEM][ts] * m[Symbol("dvProductionToGrid"*_n)][t, :NEM, ts]
        for t in p.techs_by_exportbin[:NEM]) for ts in p.time_steps)
)
```

Other set maps include: `export_bins_by_tech` and `n_segs_by_tech`. The latter tells how many cost curve segments each technology has.

#### Coefficient Arrays

The JuMP model costs are formulated in net present value terms, accounting for all benefits (production, capacity, and investment incentives) and the total cost over the `analysis_period`. The `REoptInputs` constructor translates the raw input parameters, such as the operations and maintenance costs, into present value terms using the provided discount rate. For example, the `pwf_e` is the present worth factor for electricity that accounts for the `elec_cost_escalation_rate_fraction`, the `analysis_period`, and the `offtaker_discount_rate_fraction`. Note that tax benefits are applied directly in the JuMP model for clarity on which costs are tax-deductible and which are not.

Besides econimic parameters, the `REoptInputs` constructor also puts together the important `production_factor` array. The `production_factor` array is simple for continuously variable generators (such as the `Generator`), for which the `production_factor` is 1 in all time steps. However, for variable generators (such as `Wind` and `PV`) the `production_factor` varies by time step. If the user does not provide the `PV` production factor, for example, then the `REoptInputs` constructor uses the PVWatts API to download the location specific `PV` production factor. `REoptInputs` also accounts for the `PV.degradation_fraction` in building the `production_factor` array.

### 5. File Organization

Source: https://natlabrockies.github.io/REopt.jl/dev/developer/organization/

#### data

Contains static input values such as the DoE Commercial Reference Building load profiles

#### docs

Contains all of the files for constructing this package's documentation.

#### src/constraints

Mathematical model constraints organized by which high-level structures they primarily impact.

#### src/core

The code that is central to this package. These files are used to build the inputs and the JuMP model. Some highlights:

- `scenario.jl` is the entry point for user's inputs. It uses many of the other files in the core directory to construct the high level inputs (such `electric_load.jl`, `financial.jl`, and `electric_tariff.jl`).
- `reopt_inputs.jl` uses the Scenario to construct the inputs necessary to build the JuMP model
- `reopt.jl` contains the methods for building and runnning the mathematical model

#### src/lindistflow

Code for adding a LinDistFlow model to a multi-node REopt model.

#### src/mpc

A Model Predictive Control implementation of REopt.

#### src/outagesim

The outage simulator code, which calculates some resilience metrics such as the probability of surviving varying outage durations.

#### src/results

All of the code for post-processing an optimized model and creating the results dictionary returned to the user.

#### src/sam

System Advisor Model libraries used by this package for the Wind model.

#### test

Built-in tests for several different solvers.
