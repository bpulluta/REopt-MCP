# Examples Bundle

## Bundle Summary

- Documents: 2
- Chunks: 5

## Document Index

- 1. Examples (https://natlabrockies.github.io/REopt.jl/dev/mpc/examples/)
- 2. Examples (https://natlabrockies.github.io/REopt.jl/dev/reopt/examples/)

## Documents

### 1. Examples

Source: https://natlabrockies.github.io/REopt.jl/dev/mpc/examples/

#### Examples

The MPC capability provided by `REopt` is essentially the optimal sizing and dispatch capability that `REopt` is commonly used for, but with the sizing problem removed. Also, the MPC model can be built for an arbitrary time length, or "horizon" (whereas a `REopt` model always includes an entire calendar year). The MPC model also requires the user to provide load and resource forecasts as inputs (whereas the typical `REopt` model allows one to use built-in load profiles as well as other API's such as PVWatts for the solar resource).

```
using REopt, JuMP, Cbc
model = Model(Cbc.Optimizer)
results = run_mpc(model, "./test/scenarios/mpc.json")
```

See mpc.json for details on the Scenario.

### 2. Examples

Source: https://natlabrockies.github.io/REopt.jl/dev/reopt/examples/

#### Examples

To use REopt you will need to have a solver installed. This just requires adding one of the compatible open-source solver Julia packages to your Julia environment, along with the JuMP.jl optimization modeling package. If you want to use a commercial solver which requires a licenese, installation of that solver is required external to the Julia environment.

REopt.jl has been tested with HiGHS (preferred open-source), Xpress (commercial), Cbc, SCIP, and CPLEX (commercial) solvers, but it should work with other Linear Progam solvers (for PV and Storage scenarios) or Mixed Integer Linear Program solvers (for scenarios with outages and/or Generators).

#### Basic

A REopt optimization can be run with three lines:

```
using REopt, JuMP, HiGHS

m = Model(HiGHS.Optimizer)
results = run_reopt(m, "pv_storage.json")
```

The input file, in this case `pv_storage.json`, contains the set of user-defined inputs. For more on the inputs .json file, see the REopt Inputs section and find examples at test/scenarios. For more examples of how to run REopt, see `runtests.jl`. To adjust settings such as optimality tolerance and logging, see more about relevant `Model()` arguments here: open source solver setups.

To compare the optimized case to a "Business-as-usual" case (with existing techs or no techs), you can run the BAUScenario scenario in parallel by providing two `JuMP.Model`s like so:

```
m1 = Model(HiGHS.Optimizer)
m2 = Model(HiGHS.Optimizer)
results = run_reopt([m1,m2], "pv_storage.json")
```

When the BAUScenario is included as shown above, the outputs will include comparative results such as the net present value and emissions reductions of the optimal system as compared to the BAU Scenario.

#### Modifying the mathematical model

Using the `build_reopt!` method and `JuMP` methods one can modify the REopt model before optimizing. In the following example we add a cost for curtailed PV power.

```
using HiGHS
using JuMP
using REopt

m = JuMP.Model(HiGHS.Optimizer)

p = REoptInputs("pv_storage.json");

build_reopt!(m, p)

#### =

replace the original objective, which is to Min the Costs,
with the Costs + 100 * (total curtailed PV power)
=#
JuMP.@objective(m, Min, m[:Costs] + 100 * sum(m[:dvCurtail]["PV", ts] for ts in p.time_steps));

JuMP.optimize!(m)  # normally this command is called in run_reopt

results = reopt_results(m, p)
```

One can also add variables and constraints to the model before optimizing using the JuMP commands.
