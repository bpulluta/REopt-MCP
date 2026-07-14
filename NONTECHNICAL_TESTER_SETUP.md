# REopt MCP Setup for Non-Technical Testers

This is the only setup guide testers should use for this repository.

## What this does

You will connect REopt MCP to:

- GitHub Copilot Chat in VS Code
- Claude Code

No coding is required after setup.

## Before you start

You need:

1. A GitHub account with GitHub Copilot access.
2. VS Code installed.
3. Node.js 18+ installed.
4. An NLR API key from https://developer.nlr.gov/signup/.

Important:

- Use the environment variable name `NLR_API_KEY`.

## Step 1: Download and install dependencies

Open Terminal and run:

```bash
git clone https://github.com/bpulluta/REopt-MCP.git
cd REopt-MCP
npm install
```

## Step 2: Add your API key

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and uncomment/set:

```bash
NLR_API_KEY=your_real_key_here
```

## Step 3: Configure VS Code MCP

1. Open the project in VS Code.
2. Open `./.vscode/mcp.json`.
3. Update the `cwd` value to your local project path.
4. Save the file.
5. Reload VS Code window.
6. Open Copilot Chat in Agent mode.

Expected config shape:

```json
{
  "servers": {
    "reopt": {
      "type": "stdio",
      "command": "npx",
      "args": ["tsx", "src/index.ts"],
      "cwd": "/absolute/path/to/REopt-MCP",
      "env": {
        "NODE_OPTIONS": "--use-system-ca"
      }
    }
  }
}
```

Important: do not add `NLR_API_KEY` inside `./.vscode/mcp.json`. The server
loads the key from your shell environment or from the project `.env` file at
startup.

## Step 4: Configure Claude Code MCP

1. Open `./.mcp.json`.
2. Update the `cwd` value to your local project path.
3. Save the file.
4. Ensure `./.claude/settings.json` includes `"reopt"` in `enabledMcpjsonServers`.
5. In Claude Code, run `/mcp` and confirm `reopt` is healthy.

## Step 5: Verify setup (required)

In Copilot Chat (Agent mode) or Claude Code, ask:

```text
What REopt tools are available?
```

You should see tools like:

- `submitAndWait`
- `validateScenario`
- `getScenarioHelp`
- `getSummary`
- `searchUrdbRates`

If these tools are visible, setup is complete.

## First test prompt

Use this exact prompt:

```text
I want to evaluate solar and battery for a medium office in Denver with 800000 kWh annual usage. Please gather any missing information and prepare the scenario.
```

The assistant should ask follow-up questions (location/rates) before running.

## Common fixes

1. Tool server does not appear:
   - Reload VS Code window.
   - Re-check the `cwd` path in `./.vscode/mcp.json` or `./.mcp.json`.
2. Authentication or 401 errors:
   - Confirm `.env` has a valid `NLR_API_KEY`.
3. Command errors for `npx` or `tsx`:
   - Run `npm install` again from project root.

## Current server stack

This repository currently runs:

- TypeScript server entrypoint: `src/index.ts`
- Launch command: `npx tsx src/index.ts`

Older Python/Pixi setup docs under `archive/` are for reference only and are not the canonical tester path.