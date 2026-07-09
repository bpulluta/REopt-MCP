# Installation Bundle

## Bundle Summary

- Documents: 1
- Chunks: 2

## Document Index

- 1. REopt.jl (https://natlabrockies.github.io/REopt.jl/dev/)

## Documents

### 1. REopt.jl

Source: https://natlabrockies.github.io/REopt.jl/dev/

#### Installing

REopt evaluations for all system types except GHP (see below) can be performed using the following installation instructions from the package manager mode (`]`) of the Julia REPL:

```
(active_env) pkg> add REopt JuMP HiGHS
```

#### Additional package loading for GHP

GHP evaluations must load in the `GhpGhx.jl` package separately because it has a more restrictive license and is not a registered Julia package.

Install gcc via homebrew (if running on a Mac).

Add the GhpGhx.jl package to the project's dependencies from the package manager (`]`):

```
(active_env) pkg> add "https://github.com/NatLabRockies/GhpGhx.jl"
```

Load in the package from the script where `run_reopt()` is called:

```
using GhpGhx
```
