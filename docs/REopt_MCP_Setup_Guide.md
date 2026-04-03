# REopt MCP Setup Guide for Non-Technical Users

**A Complete Step-by-Step Guide to Using REopt Energy Optimization Through AI Chat**

---

## 📋 Table of Contents

1. [What is REopt MCP?](#what-is-reopt-mcp)
2. [What You'll Be Able to Do](#what-youll-be-able-to-do)
3. [Before You Begin - Complete Checklist](#before-you-begin)
4. [Step 1: Create a GitHub Account](#step-1-create-a-github-account)
5. [Step 2: Request GitHub Copilot Access](#step-2-request-github-copilot-access)
6. [Step 3: Install VS Code](#step-3-install-vs-code)
7. [Step 4: Connect VS Code to GitHub](#step-4-connect-vs-code-to-github)
8. [Step 5: Install Pixi](#step-5-install-pixi)
9. [Step 6: Get Your NREL API Key](#step-6-get-your-nrel-api-key)
10. [Step 7: Download the REopt MCP](#step-7-download-the-reopt-mcp)
11. [Step 8: Configure REopt MCP in VS Code](#step-8-configure-reopt-mcp-in-vs-code)
12. [Step 9: Test Your Setup](#step-9-test-your-setup)
13. [How to Use REopt MCP](#how-to-use-reopt-mcp)
14. [Troubleshooting](#troubleshooting)

---

## What is REopt MCP?

**In Simple Terms:**

REopt is a powerful energy optimization tool created by the National Renewable Energy Laboratory (NREL). It helps you figure out if solar panels, batteries, wind turbines, or other energy technologies make economic sense for your building.

**The Challenge:** REopt is traditionally very technical - you need to know programming and understand complex energy terminology.

**The Solution:** REopt MCP lets you talk to REopt using **normal conversational language** through an AI assistant (GitHub Copilot) in VS Code. Instead of writing code or filling out complex forms, you just chat!

**Example:**
- **Old Way:** Learn programming, understand JSON files, manually format data, submit complex API requests
- **New Way:** Type "Should I install solar panels on my office building in Denver?" and the AI guides you through the analysis

---

## What You'll Be Able to Do

Once setup is complete, you can have conversations like:

💬 **"I want to analyze solar panels for my building in Austin, Texas"**
- The AI will ask you simple questions about your building
- Gather the information it needs
- Run the optimization
- Explain the results in plain English

💬 **"Should I add battery storage to my retail store in Denver?"**
- Get economic analysis
- Understand payback periods
- See recommended system sizes

💬 **"Compare solar-only vs solar+battery for my hospital"**
- Run multiple scenarios
- See side-by-side comparisons
- Get actionable recommendations

**No programming required. Just natural conversation.**

---

## Before You Begin

**Total Time Estimate:** 45-60 minutes (one-time setup)

**What You'll Need:**

- ✅ A computer (Windows or Mac)
- ✅ Internet connection
- ✅ Email address (for GitHub account)
- ✅ About 1 hour of time
- ✅ Administrator access to your computer (to install software)

**Optional but Helpful:**
- 📝 Notepad to write down usernames/passwords
- ☕ Coffee or tea for the setup process!

---

## Step 1: Create a GitHub Account

**⏱️ Time: 5 minutes**

**What is GitHub?** Think of it as a platform where software is stored and shared. You need an account to access GitHub Copilot (the AI assistant).

### Instructions:

1. **Go to GitHub:**
   - Open your web browser
   - Go to: **https://github.com**

2. **Sign Up:**
   - Click the **"Sign up"** button (top right corner)
   - Enter your email address
   - Create a password (write it down!)
   - Choose a username (write it down!)
   - Follow the verification steps

3. **Verify Your Email:**
   - Check your email inbox
   - Click the verification link GitHub sends you
   - This confirms your account

### ✅ Success Check:
- You can log into https://github.com with your username and password
- Your email is verified (you'll see a green checkmark on GitHub)

---

## Step 2: Request GitHub Copilot Access

**⏱️ Time: 5-10 minutes (approval may take hours to days)**

**What is GitHub Copilot?** It's an AI assistant that lives inside VS Code and helps you with coding and complex tasks. The MCP tool works through Copilot.

### Instructions:

**Option A: If Your Organization Provides Copilot**

1. **Contact Your IT Department or Manager:**
   - Ask: "Can I get access to GitHub Copilot for my work?"
   - They may already have organizational licenses

2. **Wait for Approval:**
   - Your admin will add you to the organization's Copilot
   - You'll receive an email notification

**Option B: Individual Access**

1. **Go to GitHub Copilot Page:**
   - Visit: **https://github.com/features/copilot**

2. **Start Free Trial or Purchase:**
   - Click **"Start free trial"** (if available)
   - Or click **"Buy GitHub Copilot"**
   - Follow the payment/trial setup process

3. **Enable Copilot:**
   - Log into GitHub
   - Go to Settings (click your profile picture → Settings)
   - Click **"Copilot"** in the left sidebar
   - Enable GitHub Copilot

### ✅ Success Check:
- When you log into GitHub, go to Settings → Copilot
- You should see "GitHub Copilot: Active" or similar confirmation

### ⏰ Important:
If you're waiting for organizational approval, you can continue with the next steps while you wait!

---

## Step 3: Install VS Code

**⏱️ Time: 10 minutes**

**What is VS Code?** Visual Studio Code (VS Code) is a free text editor made by Microsoft. Think of it like Microsoft Word, but for code and technical work. It's where you'll chat with the AI.

### Instructions:

#### For Mac:

1. **Download VS Code:**
   - Go to: **https://code.visualstudio.com**
   - Click the big **"Download for Mac"** button
   - The file will download (called something like `VSCode-darwin.zip`)

2. **Install:**
   - Find the downloaded file (usually in your Downloads folder)
   - Double-click to unzip it
   - Drag **Visual Studio Code** to your **Applications** folder

3. **Open VS Code:**
   - Go to Applications folder
   - Double-click **Visual Studio Code**
   - If you see a security warning, click **"Open"**

#### For Windows:

1. **Download VS Code:**
   - Go to: **https://code.visualstudio.com**
   - Click the big **"Download for Windows"** button
   - The file will download (called something like `VSCodeUserSetup-x64.exe`)

2. **Install:**
   - Find the downloaded file (usually in your Downloads folder)
   - Double-click to run the installer
   - Click **"Next"** through the installation wizard
   - **Important:** On the "Select Additional Tasks" screen:
     - ✅ Check "Add to PATH" (very important!)
     - Click **"Next"** then **"Install"**

3. **Open VS Code:**
   - It should open automatically after installation
   - Or find it in your Start Menu

### ✅ Success Check:
- VS Code opens and you see a welcome screen
- The window has a dark or light theme with a sidebar on the left

---

## Step 4: Connect VS Code to GitHub

**⏱️ Time: 5 minutes**

**Why?** VS Code needs to know who you are on GitHub to access Copilot.

### Instructions:

1. **Install GitHub Copilot Extension:**
   - In VS Code, look at the left sidebar
   - Click the **Extensions** icon (looks like 4 squares) OR
   - **Mac:** Press `Cmd + Shift + X`
   - **Windows:** Press `Ctrl + Shift + X`

2. **Search for Copilot:**
   - In the search box that appears, type: **GitHub Copilot**
   - Look for the extension by **GitHub** (it should be the first result)
   - Click the **"Install"** button (blue button)

3. **Sign In to GitHub:**
   - After installation, you'll see a **"Sign in to use GitHub Copilot"** notification
   - Click **"Sign in to GitHub"**
   - Your web browser will open
   - Click **"Authorize Visual Studio Code"**
   - You may need to enter your GitHub password

4. **Return to VS Code:**
   - Go back to VS Code
   - You should see confirmation that you're signed in

### ✅ Success Check:
- Look at the bottom-right corner of VS Code
- You should see your GitHub username or a Copilot icon
- No error messages about Copilot

### 📝 Note:
If you haven't been approved for Copilot yet (from Step 2), you might see a message saying "Waiting for Copilot access." That's okay - continue with the remaining steps!

---

## Step 5: Install Pixi

**⏱️ Time: 5-10 minutes**

**What is Pixi?** Pixi is a tool that helps manage software dependencies. The REopt MCP needs it to run properly. Think of it like a recipe manager that makes sure all the ingredients (software pieces) are available.

### Instructions:

#### For Mac:

1. **Open Terminal:**
   - Press `Cmd + Space` (opens Spotlight search)
   - Type: **Terminal**
   - Press Enter

2. **Install Pixi:**
   - Copy this command (click to select, then `Cmd + C`):
   ```bash
   curl -fsSL https://pixi.sh/install.sh | bash
   ```
   - In Terminal, right-click and select **"Paste"** (or press `Cmd + V`)
   - Press **Enter**
   - Wait for the installation to complete (may take 1-2 minutes)

3. **Restart Terminal:**
   - Close the Terminal window
   - Open a new Terminal window

4. **Verify Installation:**
   - Type: `pixi --version`
   - Press Enter
   - You should see a version number (like `pixi 0.30.0`)

#### For Windows:

1. **Open PowerShell:**
   - Click the Start button
   - Type: **PowerShell**
   - Click **"Windows PowerShell"** (not PowerShell ISE)

2. **Install Pixi:**
   - Copy this command:
   ```powershell
   iwr -useb https://pixi.sh/install.ps1 | iex
   ```
   - Right-click in PowerShell to paste
   - Press **Enter**
   - Wait for installation (may take 1-2 minutes)

3. **Restart PowerShell:**
   - Close PowerShell
   - Open a new PowerShell window

4. **Verify Installation:**
   - Type: `pixi --version`
   - Press Enter
   - You should see a version number

### ✅ Success Check:
- Terminal/PowerShell shows a version number when you type `pixi --version`
- No error messages

### 🔧 Troubleshooting:
If you see "command not found" or "not recognized":
1. Close and reopen Terminal/PowerShell
2. Try typing the full path:
   - **Mac:** `~/.pixi/bin/pixi --version`
   - **Windows:** `%USERPROFILE%\.pixi\bin\pixi --version`

---

## Step 6: Get Your NREL API Key

**⏱️ Time: 3 minutes**

**What is this?** The National Renewable Energy Laboratory (NREL) provides the REopt tool. To use it, you need a free API key - think of it like a library card that gives you access.

### Instructions:

1. **Go to NREL Developer Portal:**
   - Open your browser
   - Go to: **https://developer.nrel.gov/signup/**

2. **Sign Up:**
   - Fill out the simple form:
     - First Name
     - Last Name
     - Email address
     - Organization (your company name)
     - Check the agreement box
   - Click **"Sign up"**

3. **Get Your API Key:**
   - NREL will immediately show you your API key
   - It looks like a long string of random letters and numbers
   - **IMPORTANT:** Copy this and save it somewhere safe!
   - Example: `xjU7g8KLpQ3mN9vR2tY5wA1sD6fH8jK4`

4. **Save It:**
   - Open Notepad (Windows) or TextEdit (Mac)
   - Paste your API key
   - Save the file as: **NREL_API_Key.txt** on your desktop
   - You'll need this in Step 8!

### ✅ Success Check:
- You have a long string of random characters (32+ characters)
- It's saved in a text file you can find easily

### 📧 Email Backup:
NREL also emails you the API key. Check your email inbox!

---

## Step 7: Download the REopt MCP

**⏱️ Time: 10 minutes**

**What are we doing?** Getting the REopt MCP software from GitHub and putting it on your computer.

### Instructions:

1. **Open VS Code**

2. **Open Terminal in VS Code:**
   - **Mac:** Press `Control + ` ` (the key above Tab, with ~)
   - **Windows:** Press `Ctrl + ` `
   - OR from menu: **Terminal** → **New Terminal**
   - You'll see a terminal panel appear at the bottom

3. **Navigate to a Good Location:**
   - We'll put the REopt MCP in your Documents folder
   - Type this command:
   
   **Mac:**
   ```bash
   cd ~/Documents
   ```
   
   **Windows:**
   ```powershell
   cd ~\Documents
   ```
   
   - Press **Enter**

4. **Download REopt MCP:**
   - Copy this command:
   ```bash
   git clone https://github.com/bpulluta/REopt-MCP.git
   ```
   - Right-click in the terminal and paste (or `Cmd/Ctrl + V`)
   - Press **Enter**
   - Wait for the download (30 seconds to 2 minutes depending on internet speed)

5. **Navigate into the Folder:**
   - Type:
   ```bash
   cd REopt-MCP
   ```
   - Press **Enter**

6. **Install Dependencies:**
   - Type:
   ```bash
   pixi install
   ```
   - Press **Enter**
   - This will download and install everything REopt MCP needs
   - **This might take 3-5 minutes** - be patient!
   - You'll see lots of text scrolling by - this is normal

### ✅ Success Check:
- No error messages in red
- You see "Project successfully installed" or similar success message
- The terminal prompt shows you're in the `REopt-MCP` directory

### 🔧 Troubleshooting:

**"git is not recognized" or "command not found":**
- You need to install Git first
- **Mac:** Open Terminal and type: `xcode-select --install`
- **Windows:** Download from https://git-scm.com/download/win

---

## Step 8: Configure REopt MCP in VS Code

**⏱️ Time: 10 minutes**

**What are we doing?** Telling VS Code about REopt MCP and giving it your API key so it can run optimizations.

### Instructions:

1. **Find Your Full Path:**
   - In the VS Code terminal (from Step 7), type:
   
   **Mac:**
   ```bash
   pwd
   ```
   
   **Windows:**
   ```powershell
   pwd
   ```
   
   - Press **Enter**
   - You'll see a full path like:
     - **Mac:** `/Users/yourname/Documents/REopt-MCP`
     - **Windows:** `C:\Users\yourname\Documents\REopt-MCP`
   - **Copy this path** (select it and `Cmd/Ctrl + C`)
   - Write it down or paste into Notepad - you need it in a moment!

2. **Open VS Code Settings:**
   - **Mac:** Press `Cmd + Shift + P`
   - **Windows:** Press `Ctrl + Shift + P`
   - A search box appears at the top
   - Type: **MCP: Open user configuration**
   - Click on it when it appears in the list

3. **Add Configuration:**
   - This opens a file called something like `mcp-config.json`
   - If the file has `{}` or is empty, **replace everything** with this:

   ```json
   {
     "mcpServers": {
       "reopt": {
         "type": "stdio",
         "command": "pixi",
         "args": [
           "run",
           "--manifest-path",
           "PASTE_YOUR_PATH_HERE/pixi.toml",
           "server"
         ],
         "env": {
           "NREL_API_KEY": "PASTE_YOUR_API_KEY_HERE"
         }
       }
     }
   }
   ```

4. **Customize the Configuration:**
   
   **Part A - Fix the Path:**
   - Find the line: `"PASTE_YOUR_PATH_HERE/pixi.toml"`
   - Replace `PASTE_YOUR_PATH_HERE` with your actual path from step 1
   - **Mac example:**
     ```json
     "/Users/yourname/Documents/REopt-MCP/pixi.toml"
     ```
   - **Windows example:** (note the forward slashes!)
     ```json
     "C:/Users/yourname/Documents/REopt-MCP/pixi.toml"
     ```
   
   **Part B - Add Your API Key:**
   - Find the line: `"NREL_API_KEY": "PASTE_YOUR_API_KEY_HERE"`
   - Replace `PASTE_YOUR_API_KEY_HERE` with your actual NREL API key from Step 6
   - Example:
     ```json
     "NREL_API_KEY": "xjU7g8KLpQ3mN9vR2tY5wA1sD6fH8jK4"
     ```

5. **Final Check:**
   - Your configuration should look something like:
   
   ```json
   {
     "mcpServers": {
       "reopt": {
         "type": "stdio",
         "command": "pixi",
         "args": [
           "run",
           "--manifest-path",
           "/Users/yourname/Documents/REopt-MCP/pixi.toml",
           "server"
         ],
         "env": {
           "NREL_API_KEY": "xjU7g8KLpQ3mN9vR2tY5wA1sD6fH8jK4"
         }
       }
     }
   }
   ```
   
   - Make sure:
     - ✅ No "PASTE_YOUR" text remains
     - ✅ All quotes are matching (`"`)
     - ✅ Commas are in the right places
     - ✅ Path ends with `/pixi.toml`

6. **Save the File:**
   - **Mac:** Press `Cmd + S`
   - **Windows:** Press `Ctrl + S`

7. **Reload VS Code:**
   - **Mac:** Press `Cmd + Shift + P`
   - **Windows:** Press `Ctrl + Shift + P`
   - Type: **Developer: Reload Window**
   - Click it
   - VS Code will restart

### ✅ Success Check:
After VS Code reloads:
- No error notifications appear
- VS Code opens normally

### ⚠️ Common Mistakes:

❌ **Using backslashes in Windows paths:**
- Wrong: `C:\Users\name\Documents\REopt-MCP`
- Right: `C:/Users/name/Documents/REopt-MCP`

❌ **Missing quotes:**
- Every path and value must be in quotes: `"like this"`

❌ **Missing commas:**
- Need commas between sections (but NOT after the last item)

---

## Step 9: Test Your Setup

**⏱️ Time: 5 minutes**

**Let's make sure everything works!**

### Instructions:

1. **Open Copilot Chat:**
   - Look for the chat icon in the left sidebar (looks like a speech bubble)
   - Click it
   - OR keyboard shortcut:
     - **Mac:** `Cmd + Shift + I`
     - **Windows:** `Ctrl + Shift + I`

2. **Check for REopt:**
   - In the Copilot Chat panel, look for a ⚙️ (gear) icon
   - Click the ⚙️ icon
   - You should see a list of available tools/servers
   - Look for **"reopt"** in the list
   - It should have a ✓ checkmark next to it

3. **Test with a Simple Question:**
   - In the chat box, type:
   ```
   @reopt what tools do you have available?
   ```
   - Press Enter
   - Wait a few seconds

4. **Check the Response:**
   - You should get a response listing tools like:
     - `get_example_scenarios`
     - `submit_job`
     - `check_job_status`
     - `get_results`
   - If you see this - **SUCCESS!** 🎉

### ✅ Success Check:
- ⚙️ menu shows "reopt" with a checkmark
- @reopt responds to your question
- No error messages about "server not found" or "failed to connect"

### 🔧 Troubleshooting:

**"reopt" doesn't show up in the ⚙️ menu:**
1. Double-check your configuration file (Step 8)
2. Make sure the path is correct
3. Try reloading VS Code again

**Red error message when you type @reopt:**
1. Check that your NREL API key is correct
2. Make sure `pixi install` completed successfully (Step 7)
3. Check the terminal for error messages

---

## How to Use REopt MCP

**Now for the fun part - actually using it!**

### Understanding the Conversation Pattern

REopt MCP is designed to **gather information first, optimize second**. It will NEVER just guess or run random optimizations. Instead:

1. **You mention what you want** (general idea)
2. **MCP asks questions** (to gather required information)
3. **You provide specifics** (answer the questions)
4. **MCP builds and runs** (creates the scenario and optimizes)
5. **MCP explains results** (in plain language)

### The 3 Things REopt Always Needs:

1. **📍 Location** - Where is your building?
   - City and state, OR
   - Full address, OR
   - Latitude/longitude

2. **⚡ Energy Use** - How much electricity does your building use?
   - Annual kWh consumption, OR
   - Building type (office, retail, hospital, etc.) - REopt uses standard profiles

3. **🔌 Utility Rates** - What do you pay for electricity?
   - Utility company name, OR
   - Rate code, OR
   - Upload your own rates

### Example Conversation 1: Complete Solar Analysis

```
You: I want to analyze solar for my building in Denver

MCP: Great! To set up your solar analysis, I need a few details:
     1. Energy consumption: Do you have your annual kWh usage, or 
        should I use a standard profile for a building type?
     2. Which utility company provides your electricity?

You: It's a medium office building, about 500,000 kWh per year. 
     The utility is Xcel Energy.

MCP: Perfect! Let me set this up:
     - Location: Denver, CO
     - Energy: 500,000 kWh/year
     - Utility: Xcel Energy
     - Technology: Solar PV
     
     Running optimization now...
     
     [2 minutes later]
     
     Results are in! Here's what REopt found:
     
     ✅ RECOMMENDED SYSTEM:
     - Solar Array Size: 245 kW
     - System Cost: $612,500
     - Federal Tax Credit: $183,750 (30%)
     - Net Cost: $428,750
     
     💰 ECONOMICS:
     - Annual Savings: $42,300
     - Payback Period: 10.1 years
     - 25-Year Net Present Value: $285,000
     - Internal Rate of Return: 9.2%
     
     ⚡ ENERGY:
     - Solar will cover 38% of your annual electricity use
     - Reduces grid purchases by 190,000 kWh/year
     - Reduces CO2 emissions by 135 tons/year
     
     Would you like to explore adding battery storage as well?
```

### Example Conversation 2: Solar + Battery

```
You: What if I add batteries to that solar system?

MCP: Good question! Let me run a solar + battery optimization...
     
     [Running with same location/energy data, adding battery storage]
     
     Results with battery storage:
     
     ✅ RECOMMENDED SYSTEM:
     - Solar: 245 kW (same as before)
     - Battery: 85 kW / 170 kWh
     - Combined Cost: $765,000
     - Federal Tax Credit: $229,500
     - Net Cost: $535,500
     
     💰 ECONOMICS:
     - Annual Savings: $54,800 (vs $42,300 solar-only)
     - Payback Period: 9.8 years (better than solar-only!)
     - 25-Year NPV: $412,000 (vs $285,000 solar-only)
     
     📊 COMPARISON:
     Adding batteries increases your NPV by $127,000 over 25 years
     and shortens payback by 0.3 years. The battery provides:
     - Peak demand charge reduction
     - Energy arbitrage (store cheap, use when expensive)
     - Backup power capability
     
     Recommendation: Solar + battery is economically superior for your site.
```

### Example Conversation 3: Building Type Profile

```
You: Should I get solar for my retail store in Phoenix?

MCP: I'd be happy to help! To analyze solar for your Phoenix retail store:
     1. Do you know your annual electricity consumption in kWh?
     2. Or should I use the DOE reference profile for a typical retail store?

You: Just use the typical retail store profile

MCP: Perfect! Using DOE RetailStore reference profile.
     What's your utility company in Phoenix?

You: APS (Arizona Public Service)

MCP: Great! Running optimization for:
     - Location: Phoenix, AZ
     - Building: DOE RetailStore reference profile
     - Utility: Arizona Public Service
     - Technology: Solar PV
     
     [Optimization running...]
     
     Excellent news! Phoenix is an ideal location for solar.
     
     ✅ RECOMMENDED SYSTEM:
     - Solar Size: 156 kW
     - Covers 42% of your energy needs
     - Annual Savings: $28,400
     - Payback: 7.8 years
     - 25-Year NPV: $312,000
     
     The strong Phoenix sun and APS rate structure make this 
     very economically attractive!
```

### Example Conversation 4: Setting Constraints

```
You: I can only fit 150 kW of solar on my roof. Run an analysis 
     for my Denver office with that limit.

MCP: Got it! I'll limit solar to 150 kW maximum.
     
     For your Denver office, I need:
     1. Annual energy consumption or building size?
     2. Utility provider?

You: 500,000 kWh/year, Xcel Energy

MCP: Running constrained optimization:
     - Max Solar: 150 kW (your roof limit)
     - Location: Denver
     - Energy: 500,000 kWh/year
     - Utility: Xcel Energy
     
     [Results]
     
     With your 150 kW roof constraint:
     - System installs at maximum: 150 kW
     - Annual savings: $26,100
     - Payback: 9.8 years
     
     Note: The unconstrained optimal would be 245 kW, but your
     roof limit of 150 kW still provides solid economics!
```

### Helpful Tips for Conversations:

✅ **DO:**
- Start with your general goal: "analyze solar," "compare technologies," etc.
- Answer the questions MCP asks
- Ask for clarifications: "What does NPV mean?" "Why did you recommend batteries?"
- Request comparisons: "How does this compare to solar-only?"
- Set constraints: "I can only spend $200,000" or "roof space for 100 kW max"

❌ **DON'T:**
- Worry about technical jargon - just describe in your own words
- Provide too much info at once - answer questions as asked
- Expect instant results - optimization takes 1-3 minutes per run
- Be afraid to ask "why" - MCP can explain its recommendations!

### Common Questions to Ask:

- "What's the payback period?"
- "How much will this reduce my electricity bill?"
- "What does this system cost before and after tax credits?"
- "How much of my energy will come from solar?"
- "Should I include batteries?"
- "What if electricity prices increase faster than expected?"
- "Can you compare three scenarios: solar only, solar + battery, and wind + solar?"

---

## Troubleshooting

### Problem: @reopt doesn't appear when I type @

**Solution:**
1. Make sure GitHub Copilot is active (check bottom-right status bar)
2. Check that "reopt" has a checkmark in the ⚙️ menu in Copilot Chat
3. Try reloading VS Code: `Cmd/Ctrl + Shift + P` → "Developer: Reload Window"
4. Verify your MCP configuration (Step 8) - especially the path

---

### Problem: "Server failed to start" error

**Possible Causes & Solutions:**

1. **Pixi not installed correctly:**
   - Open Terminal in VS Code
   - Type: `pixi --version`
   - If error, reinstall Pixi (Step 5)

2. **Wrong path in configuration:**
   - Open your MCP config: `Cmd/Ctrl + Shift + P` → "MCP: Open user configuration"
   - Check that the path ends with `/pixi.toml`
   - **Mac:** Should start with `/Users/`
   - **Windows:** Should start with `C:/` (use forward slashes!)

3. **pixi install didn't complete:**
   - In VS Code terminal, navigate to REopt-MCP folder:
     ```bash
     cd ~/Documents/REopt-MCP
     ```
   - Run again:
     ```bash
     pixi install
     ```

---

### Problem: "Invalid API key" error

**Solution:**
1. Check your NREL API key is correct
2. Open your MCP config: `Cmd/Ctrl + Shift + P` → "MCP: Open user configuration"
3. Verify the API key has no extra spaces
4. Try requesting a new API key from https://developer.nrel.gov/signup/
5. Update the config with the new key
6. Reload VS Code

---

### Problem: Optimization takes forever / never completes

**Possible Causes:**

1. **Internet connection issue:**
   - REopt runs on NREL servers, needs internet
   - Check your connection

2. **NREL servers are busy:**
   - Sometimes NREL servers are under heavy load
   - Wait 5-10 minutes and try again

3. **Job actually failed:**
   - Ask MCP: "@reopt what's the status of my last job?"
   - It can check and tell you if there was an error

---

### Problem: Can't find the REopt-MCP folder

**Solution:**
- It should be in your Documents folder
- **Mac:** Open Finder → Go to Documents → look for "REopt-MCP"
- **Windows:** Open File Explorer → Documents → look for "REopt-MCP"
- If missing, repeat Step 7 to download it again

---

### Problem: VS Code won't let me edit the MCP configuration file

**Solution:**
1. Make sure you opened the correct file:
   - `Cmd/Ctrl + Shift + P` → "MCP: Open user configuration"
2. If the file is read-only:
   - **Mac:** Check file permissions in Finder
   - **Windows:** Right-click file → Properties → uncheck "Read-only"

---

### Problem: After setup, Copilot doesn't have my organizational access

**Solution:**
1. Make sure your organization admin has added you to Copilot
2. In VS Code: Sign out of GitHub and sign back in
   - Click your profile (bottom left)
   - "Sign out"
   - Sign in again
3. Reload VS Code

---

### Still Having Problems?

**Get Help:**

1. **Check the detailed documentation:**
   - In the REopt-MCP folder, open: `dev-docs/TROUBLESHOOTING.md`

2. **Check GitHub Issues:**
   - Go to: https://github.com/bpulluta/REopt-MCP/issues
   - Search to see if others have had the same problem
   - Post a new issue with details about your error

3. **Contact your team lead or IT:**
   - They may have organization-specific setup requirements

---

## Next Steps & Resources

### You're All Set! 🎉

You can now:
- ✅ Have natural conversations about energy optimization
- ✅ Run REopt analyses without programming
- ✅ Compare different technology scenarios
- ✅ Get economic and technical recommendations

### Learn More:

**About REopt:**
- Official NREL REopt Page: https://reopt.nrel.gov
- What REopt Can Do: https://reopt.nrel.gov/tool

**About the Technologies:**
- Solar PV basics
- Battery energy storage
- Demand charges and time-of-use rates

**Advanced Usage:**
- Check `dev-docs/GUIDED_WORKFLOW_EXAMPLE.md` in the REopt-MCP folder
- See example scenarios and advanced options

### Share Your Success!

Once you've run your first optimization:
- Share the results with your team
- Discuss economic feasibility
- Consider next steps for your building

---

## Document Information

**Version:** 1.0  
**Last Updated:** January 2026  
**Created For:** Non-technical users setting up REopt MCP  
**Prerequisites:** None - complete beginner-friendly guide  

---

## Converting This Document

### To Microsoft Word:

**Option 1: Using Pandoc (Recommended)**
```bash
pandoc REopt_MCP_Setup_Guide.md -o REopt_MCP_Setup_Guide.docx
```

**Option 2: Using Microsoft Word Directly**
1. Open Microsoft Word
2. File → Open
3. Select this `.md` file
4. Word will convert it automatically
5. File → Save As → choose .docx format

**Option 3: Online Converter**
- Go to: https://cloudconvert.com/md-to-docx
- Upload this file
- Download the converted .docx

### To HTML:

**Using Pandoc:**
```bash
pandoc REopt_MCP_Setup_Guide.md -o REopt_MCP_Setup_Guide.html
```

**Using Online Converter:**
- Go to: https://cloudconvert.com/md-to-html
- Upload this file
- Download the converted .html

### To PDF:

**Using Pandoc:**
```bash
pandoc REopt_MCP_Setup_Guide.md -o REopt_MCP_Setup_Guide.pdf
```

---

**Happy Optimizing! 🌞🔋⚡**
