"""
UGG Documentation Library — Operator-Friendly User Manual.
Written for non-technical route operators who need step-by-step hand-holding.
"""
from fastapi import APIRouter, Request, HTTPException
from auth import get_current_user

router = APIRouter(prefix="/api/library", tags=["library"])

DOC_SECTIONS = [
    {"id": "quick-start", "title": "Quick Start Guide", "icon": "Rocket", "docs": [
        {"id": "qs-welcome", "title": "Welcome to UGG", "content": """Welcome to the Universal Gaming Gateway! This guide will walk you through everything you need to know to manage your gaming route.

**What is UGG?**
UGG connects all your Electronic Gaming Machines (EGMs) to one central system. Instead of visiting each machine or each location, you can see everything from your computer or tablet.

**What can you do with UGG?**
- See which machines are online or offline — right now, in real-time
- Track how much money each machine is making (NOR — Net Operating Revenue)
- Get alerts when something goes wrong (machine offline, door open, handpay needed)
- Generate tax reports and EFT payment files automatically
- View your entire route on a map
- Run AI-powered analytics to predict problems before they happen

**Who is this guide for?**
This guide is written for route operators, distributors, and venue owners who manage gaming machines. You don't need to be a computer expert — we'll walk you through every step."""},

        {"id": "qs-first-login", "title": "Step 1: Your First Login", "content": """**How to log in for the first time:**

1. Open your web browser (Chrome, Safari, or Edge all work)
2. Go to your UGG website address (your administrator will give you this)
3. You'll see the login screen with the UGG logo
4. Enter your **email address** in the Email field
5. Enter your **password** in the Password field
6. Click the green **Sign In** button

**Trouble logging in?**
- Make sure your email is spelled correctly
- Passwords are case-sensitive (capital letters matter)
- If you've forgotten your password, contact your administrator
- After 5 wrong attempts, you'll be locked out for 15 minutes — just wait and try again

**First thing you'll see:**
After logging in, you'll land on the **Mission Control** dashboard. This is your home base — it shows the health of your entire operation at a glance."""},

        {"id": "qs-dashboard-tour", "title": "Step 2: Understanding Your Dashboard", "content": """**The Mission Control dashboard has 4 main areas:**

**Top Row — Summary Cards (the big numbers)**
These 4 cards give you the most important info at a glance:
- **Total Devices** — How many machines you have. The small text shows how many are online vs offline
- **Active Alerts** — Problems that need your attention. Red means urgent!
- **Command Queue** — Commands waiting to be sent to machines
- **Event Throughput** — How many events your machines are generating (higher = busier)

**Charts Area**
- **Event Volume** — A line chart showing activity over the last 24 hours
- **Protocol Mix** — A pie chart showing what types of machines you have (SAS, G2S, etc.)
- **Device Status** — Bar charts showing how many machines are in each state

**Device Health Map (the colorful grid)**
Each small box represents one of your machines:
- **Green** = Online and working perfectly
- **Red** = Offline or has an error — needs attention!
- **Yellow/Orange** = In maintenance mode
Click any box to go directly to that machine's details.

**Live Event Feed (right side)**
A real-time scrolling list of everything happening across your route. New events appear at the top automatically — you don't need to refresh the page.

**Alert Ticker (bottom)**
A scrolling bar showing active alerts. Click any alert to go to the Alert Console for more details."""},

        {"id": "qs-check-machines", "title": "Step 3: Checking Your Machines", "content": """**How to check on a specific machine:**

1. Click **Device Fleet** in the left sidebar
2. You'll see a list of all your machines
3. Use the **Search** box to find a specific machine by its ID number (e.g., EGM-1001)
4. Or use the **filter dropdowns** to narrow by status, protocol, or manufacturer

**Understanding the machine list:**
Each row shows:
- **Status dot** — Green (online), Red (offline/error), Yellow (maintenance)
- **Device Ref** — The machine's ID number (like EGM-1001)
- **Manufacturer** — Who made it (IGT, Aristocrat, etc.)
- **Model** — The specific model name
- **Protocol** — How it communicates (SAS or G2S)
- **Last Seen** — When the machine last reported in

**Getting machine details:**
Click on any machine to open the detail panel on the right side. This shows:
- **Overview tab** — Serial number, firmware, game title, denomination, and capabilities
- **Events tab** — Recent events from this machine
- **Commands tab** — Commands that have been sent to this machine
- **Connector tab** — Technical protocol information
- **Audit tab** — History of changes

**Quick actions from the detail panel:**
- Click **Disable** to remotely disable a machine (it will stop accepting play)
- Click **Enable** to turn it back on
- Click **Send Message** to display a message on the machine's screen"""},

        {"id": "qs-check-money", "title": "Step 4: Checking the Money", "content": """**How to see how much money your machines are making:**

1. Click **Financial** in the left sidebar
2. You'll see the Financial Dashboard with 6 summary cards at the top

**Understanding the numbers:**
- **Coin In** — Total money put into machines (bills, coins, vouchers)
- **Coin Out** — Total money paid out by machines (wins, jackpots)
- **House Hold** — The difference between Coin In and Coin Out (this is your profit before splits)
- **Jackpots** — Large wins that require hand-pay by an attendant
- **Voucher In** — Money loaded via TITO (Ticket-In, Ticket-Out) vouchers
- **Handpays** — Wins over $1,200 that require tax documentation

**The charts show:**
- **Hourly Revenue** — How money flows throughout the day (wagers vs payouts)
- **By Site** — Which locations are making the most money
- **Top Games** — Which game titles are the most popular

**The Transaction Ledger (table at bottom):**
Shows every individual transaction. You can filter by type (wager, payout, jackpot, etc.) using the dropdown.

**For your NOR (Net Operating Revenue) report:**
Click **Route Operations** in the sidebar, then the **NOR Accounting** tab. This shows your daily NOR trend, how much you owe in taxes, and a breakdown by distributor."""},

        {"id": "qs-handle-alerts", "title": "Step 5: Handling Alerts & Problems", "content": """**When something goes wrong, UGG tells you immediately.**

**How to check alerts:**
1. Click **Exceptions** in the left sidebar (or click the alert ticker at the bottom of the dashboard)
2. You'll see all active alerts sorted by urgency

**Alert types you'll see most often:**
- **DEVICE_OFFLINE** (Critical) — A machine has stopped communicating. Check the network cable, power, and site controller
- **DOOR_OPEN** (Warning) — Someone opened a machine door. Normal during service, but investigate if unexpected
- **HANDPAY_PENDING** (Warning) — A player won a jackpot that needs to be hand-paid by an attendant
- **ZERO_PLAY_TODAY** (Warning) — A machine hasn't had any play today. Could mean it's in a bad location or has a problem
- **INTEGRITY_VIOLATION** (Critical) — The machine's software doesn't match what's expected. This is serious — the machine is automatically disabled

**How to resolve an alert:**
1. Find the alert in the list
2. Read the description to understand what happened
3. Take the appropriate action (visit the site, call the venue, etc.)
4. Click the **Resolve** button and add a note about what you did

**Pro tip:** Check alerts at least 3 times a day — morning, midday, and evening. Critical alerts should be handled within 1 hour."""},

        {"id": "qs-view-map", "title": "Step 6: Viewing Your Route on the Map", "content": """**See all your locations on a real map:**

1. Click **Route Map** in the left sidebar
2. You'll see a map of Nevada (or your state) with colored dots for each venue

**Understanding the map:**
- **Green dots** = Venue is healthy (95%+ of machines online)
- **Yellow dots** = Some machines have issues (80-95% online)
- **Red dots** = Venue needs attention (less than 80% online)
- **Bigger dots** = More machines at that venue

**What you can do:**
- **Zoom in/out** using your mouse scroll wheel or the +/- buttons
- **Switch map views** using the toggle in the top-left: Dark (default), Satellite (aerial photos), Streets (road map)
- **Click a dot** to see venue details (name, address, device count, NOR, exceptions)
- **Click "View Venue Devices"** in the detail panel to see all machines at that location

**The venue list on the left:**
Shows all your venues with a quick summary. Click any venue to fly to it on the map.

**Bottom summary bar:**
Shows your total venues, total devices, percentage online, and today's NOR across all locations."""},
    ]},

    {"id": "daily-tasks", "title": "Daily Operations", "icon": "ChartBar", "docs": [
        {"id": "dt-morning", "title": "Morning Checklist", "content": """**Start every day with this 5-minute routine:**

1. **Log in** and check the Mission Control dashboard
2. **Look at the alert count** — Are there any new critical alerts (red)? Handle those first
3. **Check device count** — How many machines are online vs offline? Any unexpected dropoffs?
4. **Glance at NOR** — Is today's revenue tracking normally compared to recent days?
5. **Check the Route Map** — Any venues showing red? Those need a call or visit

**If everything looks normal:**
Great! Check back around lunchtime and again before end of day.

**If you see problems:**
- Critical alerts = Handle immediately
- Offline machines = Call the venue to check power/network
- Low NOR at a site = Check if machines are disabled or having issues"""},

        {"id": "dt-handling-offline", "title": "When a Machine Goes Offline", "content": """**Step-by-step troubleshooting for offline machines:**

**Step 1: Check the alert**
Go to Exceptions and find the DEVICE_OFFLINE alert. Note the device ID and location.

**Step 2: Call the venue**
Ask the venue manager:
- "Is the machine powered on? Is the light on?"
- "Has anything changed? Power outage? Network issues?"
- "Can you check if the network cable is plugged in behind the machine?"

**Step 3: If the venue says everything looks fine:**
The problem might be with the site controller (the small box that connects to your machines).
- Ask if the controller's lights are blinking normally
- Ask them to power-cycle the controller (unplug it, wait 10 seconds, plug it back in)

**Step 4: If the machine comes back online:**
Great! The alert will automatically resolve in UGG within a few minutes.

**Step 5: If it stays offline:**
Schedule a technician visit. Go to Route Operations > check the machine in the Device Fleet and note the last time it was seen.

**Important:** Machines that stay offline for 30 days will be automatically disabled by the system (this is a regulatory requirement)."""},

        {"id": "dt-handpay", "title": "Handling a Handpay", "content": """**When a player wins a jackpot over $1,200:**

1. You'll see a **HANDPAY_PENDING** alert in UGG
2. The machine locks up and waits for an attendant
3. A venue employee needs to:
   - Verify the win amount on the machine
   - Complete the W-2G tax form for the player
   - Reset (key-off) the handpay on the machine
4. Once the handpay is keyed off, UGG will automatically update
5. Go to Exceptions and resolve the HANDPAY_PENDING alert

**Tax reporting:**
All handpays are automatically recorded in UGG and included in your regulatory reports. You don't need to do anything extra — UGG tracks it all."""},

        {"id": "dt-reports", "title": "Running Your Reports", "content": """**UGG generates all the reports you need:**

**Daily Revenue Report:**
1. Go to **Route Operations** > **NOR Accounting** tab
2. The chart shows your daily NOR for the last 30 days
3. The table below shows NOR broken down by distributor with coin in, coin out, tax, and hold percentage

**Weekly EFT (Electronic Funds Transfer):**
1. Go to **Route Operations** > **EFT/NACHA** tab
2. Click **Generate NACHA-Compliant** to create a new payment file
3. UGG builds the proper ACH file format that your bank needs
4. All 6 validation checks should show green checkmarks
5. Download the file and submit to your bank

**Exporting Data to Excel/CSV:**
1. Go to **Export** in the sidebar
2. Choose what you want to export:
   - Financial Transactions — all money in/out
   - Player Sessions — session data
   - Device Inventory — your machine list
   - Events — everything that happened
   - Audit Trail — who did what and when
   - Jackpots — progressive jackpot data
3. Click **Download CSV** and open in Excel

**Tax Reports:**
Go to **Regulatory** in the sidebar for the full compliance dashboard that your state regulator sees."""},
    ]},

    {"id": "setup-guide", "title": "Setting Up Your Route", "icon": "MapPin", "docs": [
        {"id": "sg-adding-venue", "title": "Adding a New Venue", "content": """**When you get a new location for your machines:**

Your administrator will set up the venue in UGG. Here's what they need from you:

1. **Venue name** — The business name (e.g., "Joe's Bar & Grill")
2. **Address** — Full street address including city, state, and ZIP
3. **County** — This is required for state regulatory reporting
4. **Contact person** — Name and phone number at the venue
5. **Number of machines** — How many EGMs you're placing there
6. **Internet connection** — Does the venue have internet? If not, you'll need a cellular modem

**After the venue is set up:**
- It will appear on your Route Map
- You'll see it in the venue list
- Any machines assigned to it will show under that location"""},

        {"id": "sg-connecting-machine", "title": "Connecting a New Machine (SAS)", "content": """**How to connect a new SAS gaming machine to UGG:**

**What you'll need:**
- The UGG Agent box (Raspberry Pi) at the venue — it should already be installed
- An RS-232 serial cable (the gray cable with the wide connector)
- The machine's SAS address (usually 1-127, check the machine's setup menu)

**Step-by-step:**

1. **Power off the machine** (always disconnect power before plugging in cables)
2. **Connect the serial cable** from the machine's SAS port to the UGG Agent
3. **Power the machine back on**
4. **Wait 2-3 minutes** for the UGG Agent to discover the machine
5. **Check UGG** — go to Device Fleet and look for the new machine
   - It should appear with a green dot (online)
   - The protocol should show "sas"
   - Click it to verify the manufacturer and model are correct

**If the machine doesn't appear:**
- Check that the serial cable is firmly connected at both ends
- Verify the machine's SAS address isn't conflicting with another machine on the same cable
- Check the UGG Agent's lights — solid green means it's connected to the internet
- Call your technical support team

**After connecting:**
UGG will automatically start polling the machine's meters every few seconds. Within minutes, you'll see meter data (coin in, coin out, games played) in the device detail panel."""},

        {"id": "sg-connecting-g2s", "title": "Connecting a New Machine (G2S)", "content": """**How to connect a modern G2S gaming machine to UGG:**

G2S machines connect over the network (Ethernet) instead of serial cables. This is the newer, faster protocol.

**What you'll need:**
- An Ethernet cable connected from the machine to the venue's network
- The machine's IP address (check the machine's network settings)
- The machine's G2S endpoint URL (usually something like https://machine-ip:443/g2s)

**Step-by-step:**

1. **Make sure the machine is on the same network** as the UGG Agent
2. **Log into UGG** and go to the **Emulator Lab**
3. Click the **Live G2S** tab
4. Enter the machine's URL in the **EGM SOAP Endpoint** field
5. Enter a device ID for this machine (e.g., EGM-1050)
6. Click **Connect** — UGG will run the full G2S startup sequence
7. If successful, you'll see "ONLINE" and a list of completed startup steps

**What happens during startup:**
UGG sends a series of messages to the machine:
- "Hello, I'm here" (commsOnLine)
- "Here's what I need from you" (setCommsState)
- "What's your status?" (getDeviceStatus for each component)
- "Send me events as they happen" (setEventSub)

This all happens automatically — you just click Connect and wait."""},

        {"id": "sg-agent-setup", "title": "Setting Up a UGG Agent at a New Site", "content": """**The UGG Agent is the small box that sits at each venue and talks to your machines.**

**What's in the box:**
- Raspberry Pi 4 computer (small, about the size of a deck of cards)
- Power adapter
- SD card (already configured)
- Serial cable(s) for connecting to SAS machines
- Cellular modem (if the venue doesn't have internet)

**Installation steps:**

1. **Find a good location** — Near the machines, with access to a power outlet. Keep it out of public reach
2. **Plug in the power adapter** — The green light should come on
3. **Connect to the internet:**
   - **If the venue has internet:** Plug an Ethernet cable from the agent to the venue's router
   - **If using cellular:** The modem should already be configured — it will connect automatically
4. **Wait 3-5 minutes** for the agent to boot up and connect to UGG Central
5. **Check UGG** — Go to **Settings** > **Agents** tab. You should see the new agent with a green "connected" dot
6. **Connect your machines** (see "Connecting a New Machine" guides above)

**Provisioning package:**
If you need to set up a brand new agent, go to **Hardware** in UGG and use the **Provisioning Package Generator**. This creates a ZIP file with everything the agent needs — configuration, security certificates, and setup instructions."""},
    ]},

    {"id": "route-management", "title": "Route Management", "icon": "CurrencyDollar", "docs": [
        {"id": "rm-nor-explained", "title": "Understanding NOR (Your Revenue)", "content": """**NOR = Net Operating Revenue — this is the money your machines make**

**The simple formula:**
NOR = Money In - Money Out

More specifically:
NOR = Coin In - Coin Out - Handpays - Vouchers Out

**Example:**
If a machine takes in $1,000 in bills and coins, pays out $850 in wins and vouchers, and has $50 in handpays:
NOR = $1,000 - $850 - $50 = $100

That $100 is then split between everyone:
- **State** gets the tax (e.g., 5-7%)
- **Distributor** gets their share (e.g., 34%)
- **Operator** gets their share (e.g., 33%)
- **Retailer** (venue owner) gets their share (e.g., 33%)

**Where to see NOR in UGG:**
- **Route Operations > Overview** — Grand total NOR for the last 30 days
- **Route Operations > NOR Accounting** — Daily trend chart and by-distributor breakdown
- **Financial Dashboard** — Detailed coin in/out with charts
- **Route Map** — NOR shown for each venue

**The NOR Split:**
Go to Route Operations and you can see exactly how the NOR splits between all parties. UGG calculates this automatically with penny-perfect precision — the retailer absorbs any rounding so the totals always match exactly."""},

        {"id": "rm-eft", "title": "Generating Payment Files (EFT)", "content": """**UGG creates the bank payment files so you get paid:**

**What is an EFT file?**
EFT = Electronic Funds Transfer. It's a special file format (called NACHA/ACH) that tells the bank to move money from one account to another.

**How to generate a payment file:**

1. Go to **Route Operations** > **EFT/NACHA** tab
2. Click the blue **Generate NACHA-Compliant** button
3. UGG calculates how much each distributor owes based on NOR
4. A file is created with one payment entry per distributor
5. You'll see a **NACHA Validation** panel with 6 green checkmarks:
   - File Header Record ✅
   - File Control Record ✅
   - Record Length (94 chars) ✅
   - Blocking Factor (10) ✅
   - Batch Header/Control Pairs ✅
   - Entry Detail Records ✅

**If any check shows red:**
Don't submit the file to your bank! Contact support.

**Submitting to your bank:**
Download the .ach file and upload it through your bank's ACH portal. The bank will process the payments, usually within 1-2 business days.

**Important:**
Always generate a new file for each payment period. Never submit the same file twice — it could cause duplicate payments!"""},

        {"id": "rm-exceptions", "title": "Understanding All Alert Types", "content": """**Here's every type of alert UGG can show you and what to do about each one:**

**CRITICAL alerts (handle immediately):**
- **DEVICE_OFFLINE** — Machine stopped communicating. Check power and network at the venue
- **SITE_CONTROLLER_OFFLINE** — The UGG Agent box at a venue is down. All machines at that site will show offline. Check the agent's power and internet
- **INTEGRITY_VIOLATION** — Machine software doesn't match. Machine auto-disables. Contact your manufacturer
- **AUTO_DISABLED_30DAY** — Machine was offline for 30 days straight. Regulatory requirement forces disable
- **NSF_ALERT** — A bank payment bounced. The affected distributor's future payments are held until resolved

**WARNING alerts (handle within 24 hours):**
- **DEVICE_DISABLED** — A machine has been disabled (by you, the system, or a fault)
- **DOOR_OPEN** — A machine cabinet door is open. Normal during service — investigate if unexpected
- **HANDPAY_PENDING** — Jackpot waiting for attendant key-off
- **ZERO_PLAY_TODAY** — Machine had no play all day. Might be in a bad location or have a "game not available" error
- **REVENUE_ANOMALY** — Machine's revenue dropped below 40% of its 90-day average. Might indicate a problem

**INFO alerts (check when convenient):**
- **LOW_PLAY_ALERT** — Machine is getting less play than usual. Consider moving it to a better spot
- **EXCESSIVE_GAMEPLAY** — A player has been on a machine for 4+ hours (responsible gambling flag)
- **MAX_TERMINALS_EXCEEDED** — A venue has more machines than their license allows. Remove extras immediately
- **LICENSE_EXPIRY** — A distributor or operator's license is expiring within 30 days. Renew immediately"""},
    ]},

    {"id": "ai-features", "title": "AI Features (Smart Insights)", "icon": "Sparkle", "docs": [
        {"id": "ai-overview", "title": "How AI Helps You", "content": """**UGG has built-in artificial intelligence that works for you 24/7**

You don't need to understand AI or technology — UGG's AI automatically analyzes your data and tells you what to do in plain English.

**What the AI does:**

1. **Predicts machine failures** — "EGM-1023 has a 78% chance of failing this week. Schedule a preventive maintenance visit."
2. **Forecasts your revenue** — "Based on the last 30 days, your NOR next week should be around $266,000"
3. **Finds patterns in problems** — "3 machines at Joe's Bar keep going offline. The common factor is they're all on the same network switch"
4. **Answers your questions** — You can literally type questions like "Which machines are making the most money?" and get answers

**How to use it:**
Click **AI Analytics** in the sidebar. You'll see 3 colored buttons:
- **Red (Predictive Maintenance)** — Click to see which machines might fail soon
- **Green (NOR Forecast)** — Click to see revenue predictions
- **Yellow (Exception Patterns)** — Click to find patterns in your alerts

Or just type your question in the search bar at the top!"""},

        {"id": "ai-asking-questions", "title": "Asking the AI Questions", "content": """**You can ask UGG anything about your route in plain English:**

**How to ask:**
1. Go to **AI Analytics** in the sidebar
2. Type your question in the search bar at the top
3. Press Enter or click the blue send button
4. Wait 5-10 seconds — the AI is analyzing your real data

**Example questions you can ask:**
- "Which machines are most likely to fail this week?"
- "What will our NOR be next month?"
- "Why are we getting so many DEVICE_OFFLINE exceptions?"
- "Which venue is making the least money and why?"
- "How can we increase revenue by 10%?"
- "What's our average hold percentage across all distributors?"
- "Which game titles are most popular at our Las Vegas locations?"

**Understanding the answers:**
The AI gives you specific answers based on YOUR data:
- Dollar amounts are highlighted in green
- Percentages are highlighted in yellow
- Device IDs are shown so you know exactly which machines it's talking about

**The AI is not guessing** — it looks at your actual devices, NOR data, exceptions, and digital twin projections to give you data-driven answers."""},
    ]},

    {"id": "advanced", "title": "Advanced Features", "icon": "GearSix", "docs": [
        {"id": "adv-command-center", "title": "Using the Command Center", "content": """**The Command Center is a full-screen display for your operations room:**

**How to open it:**
Click **Command Center** in the sidebar. It takes over the entire screen — no sidebar, no header, just data.

**What you see:**
- Top row: 6 big number displays (Devices, Alerts, Coin In, Jackpot Liability, Events, Active Players)
- Left: Color-coded grid of all your devices
- Center: Event volume chart with severity breakdown
- Right: Live event feed streaming in real time
- Bottom-left: Progressive jackpot amounts with progress bars
- Bottom-center: VIP player alerts (when Platinum/Diamond members card in)
- Bottom-right: Currently active player sessions
- Very bottom: Scrolling alert ticker

**How to exit:**
Click the "Exit" arrow in the top-left corner to return to the normal dashboard.

**Best used on:**
A large TV or monitor in your office so you can always see your route status at a glance."""},

        {"id": "adv-regulatory", "title": "The Regulatory Dashboard", "content": """**This is what your state gaming regulator sees:**

The Regulatory Dashboard shows a compliance score and cross-distributor comparison. Only users with the State Regulator or Admin role can access it.

**Compliance Score (0-100):**
The circular gauge in the top-right shows your overall compliance. It's calculated from:
- 30% — Statutory field coverage (are all required data fields filled in?)
- 40% — Software integrity pass rate (are machines running approved software?)
- 20% — Exception management (are critical issues being resolved quickly?)
- 10% — System operational (is UGG itself running?)

**Score guide:**
- 90-100 = Green = Excellent compliance
- 70-89 = Yellow = Some issues to address
- Below 70 = Red = Needs immediate attention

**Distributor Compliance Matrix:**
A table comparing all distributors side-by-side: NOR, tax collected, hold%, integrity pass rate, active exceptions, and overall compliance score."""},

        {"id": "adv-export-data", "title": "Exporting Your Data", "content": """**How to get your data into Excel:**

1. Click **Export** in the sidebar
2. You'll see 6 report cards — one for each type of data
3. If needed, use the filter dropdown to narrow the data (e.g., only "wager" transactions)
4. Click the blue **Download CSV** button
5. The file downloads to your computer
6. Open it in Microsoft Excel, Google Sheets, or Numbers

**What each export contains:**
- **Financial Transactions** — Every money event (wagers, payouts, vouchers, jackpots) with timestamps, amounts, device IDs, player info, and game titles
- **Player Sessions** — Player card-in/card-out times, duration, games played, amount wagered, amount won, loyalty points
- **Device Inventory** — Your complete machine list with manufacturer, model, serial, protocol, status, firmware, game
- **Canonical Events** — Technical event log with type, severity, and payload data
- **Audit Trail** — Complete history of who did what and when (login, commands, configuration changes)
- **Progressive Jackpots** — Jackpot names, current amounts, base amounts, ceilings, hit history

**Tip:** Export your Financial Transactions weekly and keep them in a folder. This is your backup in case you ever need to verify numbers with your bank or regulator."""},

        {"id": "adv-marketplace", "title": "The Connector Marketplace", "content": """**UGG has a marketplace where you can find connectors for different machine types:**

Go to **Marketplace** in the sidebar. You'll see connector listings like:
- SAS adapters for different protocol versions
- G2S adapters for modern machines
- Vendor-specific connectors (Aristocrat, Konami, IGT, etc.)
- Analytics and compliance tools

**Each listing shows:**
- Name and description
- Who made it (vendor name)
- Star rating from other operators
- Number of installs
- Price (many are free!)
- Certification badge (green shield = officially certified)

**To install a connector:**
1. Click the connector card
2. Read the description and reviews in the detail panel on the right
3. Click the green **Install Connector** button
4. The connector will be added to your UGG instance

**Leaving a review:**
After using a connector, you can rate it 1-5 stars and leave a review to help other operators."""},
    ]},

    {"id": "troubleshooting", "title": "Troubleshooting", "icon": "Warning", "docs": [
        {"id": "ts-common", "title": "Common Problems & Solutions", "content": """**Here are the most common issues and how to fix them:**

**Problem: "I can't log in"**
- Clear your browser's cache (Settings > Clear Browsing Data)
- Make sure Caps Lock is off
- Try a different browser
- Wait 15 minutes if you've been locked out from too many attempts

**Problem: "A machine shows offline but the venue says it's on"**
- Ask the venue to check the cable connection between the machine and the UGG Agent
- Ask them to unplug the UGG Agent for 10 seconds, then plug it back in
- Check if other machines at the same venue are also offline (if yes, it's a network issue)

**Problem: "My NOR numbers look wrong"**
- Check if any machines were offline during the period (offline machines don't report meters)
- Go to Route Operations > Statutory tab and click "Enrich Events" to make sure all data has proper statutory fields
- Contact support if numbers still don't match your expectations

**Problem: "I see a lot of ZERO_PLAY_TODAY alerts"**
- This usually means machines are on but nobody is playing them
- Check if the venue is actually open
- Consider relocating machines with consistently zero play to busier locations

**Problem: "The map isn't showing"**
- Try refreshing the page (press F5 or Ctrl+R)
- Try a different browser
- Check your internet connection

**Problem: "AI Analytics gives an error"**
- The AI needs at least some data to analyze. If you just started, wait a few days for data to accumulate
- Try again in a minute — the AI service might be temporarily busy

**Still stuck?**
Contact your UGG administrator or technical support team with:
1. What you were trying to do
2. What you saw instead
3. The time it happened
4. Screenshots if possible"""},

        {"id": "ts-glossary", "title": "Glossary of Terms", "content": """**Common terms you'll see in UGG:**

- **EGM** — Electronic Gaming Machine
- **NOR** — Net Operating Revenue (money in minus money out = your profit)
- **SAS** — Slot Accounting System, the older serial cable protocol for machines
- **G2S** — Game-to-System, the newer network protocol for modern machines
- **TITO** — Ticket-In, Ticket-Out (the voucher system — machine prints tickets instead of paying coins)
- **Handpay** — A win over $1,200 that must be paid by an attendant and reported to the IRS
- **Hold Percentage** — The percent of money the house keeps (e.g., 8% hold means for every $100 in, the house keeps $8)
- **Coin In** — Total money inserted into machines (bills, coins, vouchers)
- **Coin Out** — Total money paid out by machines
- **Digital Twin** — UGG's real-time model of each machine's current state
- **Canonical Event** — A standardized event format that works the same regardless of machine brand or protocol
- **Integrity Check** — Verification that a machine is running approved, unmodified software
- **NACHA/ACH** — The standard file format for electronic bank transfers
- **mTLS** — Mutual TLS, a security protocol where both sides verify each other's identity with certificates
- **Progressive Jackpot** — A jackpot that grows every time someone plays, shared across linked machines
- **Site Controller** — The UGG Agent box at a venue that connects to the machines
- **Statutory Fields** — Data fields required by state law on every event (distributor ID, county, etc.)"""},
    ]},

    {"id": "egm-developer", "title": "EGM Developer Guide", "icon": "Plugs", "docs": [
        {"id": "dev-overview", "title": "Getting Your EGM Working with UGG", "content": """**Welcome, EGM Manufacturer!**

This guide is for you if you build Electronic Gaming Machines and want them to work with the UGG platform. Whether your EGM uses SAS, G2S, or your own proprietary protocol, UGG can connect to it.

**Three paths to integration:**

**Path 1: Your EGM already supports SAS**
You're ready! UGG connects via RS-232 serial cable and polls your machine using standard SAS long polls. No custom development needed. Skip to "Testing with the Emulator Lab."

**Path 2: Your EGM already supports G2S**
You're also ready! UGG connects via SOAP/HTTP and runs the standard G2S startup sequence. No custom development needed. Skip to "Testing with the Emulator Lab."

**Path 3: Your EGM has its own proprietary protocol**
This is where UGG's Vendor Connector Framework shines. You'll build a "connector" that translates your protocol into UGG's standard format. This guide walks you through every step.

**What you'll build:**
A Connector Manifest — a configuration file that tells UGG how to talk to your machine. You won't need to modify your EGM's software. The connector sits between your machine and UGG, translating messages in both directions.

**Time estimate:**
- Simple REST API connector: 1-2 days
- Database polling connector: 2-3 days
- Full bidirectional connector: 3-5 days
- Certification testing: 1-2 additional days"""},

        {"id": "dev-canonical-events", "title": "Understanding UGG Canonical Events", "content": """**Every EGM event in UGG follows one standard format, regardless of protocol.**

This is the key concept: your machine might report a "game ended" event differently than another manufacturer's machine, but UGG converts both into the same standard format called a Canonical Event.

**The Canonical Event format:**
Every event has these fields:
- **event_type** — What happened (e.g., "device.game.start", "device.game.end", "device.door.opened")
- **device_id** — Which machine it came from
- **occurred_at** — When it happened (UTC timestamp)
- **severity** — How important: "info", "warning", or "critical"
- **payload** — The detailed data (varies by event type)
- **protocol** — How it was received: "SAS", "G2S", or "PROPRIETARY"
- **integrity_hash** — A checksum proving the data hasn't been tampered with

**Common event types you need to map to:**
- device.game.start — Player started a game (includes bet amount)
- device.game.end — Game completed (includes win amount)
- device.meter.changed — Meter values updated (coin in, coin out, etc.)
- device.door.opened / device.door.closed — Cabinet door events
- device.tilt — Machine error or fault condition
- device.voucher.in / device.voucher.out — TITO ticket events
- device.jackpot.handpay — Large win requiring hand-pay
- device.player.card.in / device.player.card.out — Player tracking
- device.status.online / device.status.offline — Connection state changes
- device.bonus.triggered — Bonus game activated

**Your job:** Map your machine's events to these canonical types. UGG's AI Studio can help automate this."""},

        {"id": "dev-connector-types", "title": "Choosing Your Connector Type", "content": """**UGG supports 6 connector types. Pick the one that matches how your EGM communicates:**

**1. REST (most common for modern EGMs)**
Your EGM exposes an HTTP REST API that UGG polls at regular intervals.
- Best for: EGMs with built-in web servers, cloud-connected EGMs
- UGG sends: HTTP GET/POST requests to your endpoint
- You provide: API URL, authentication credentials, response format documentation
- Example: Your EGM has an API at https://egm-ip/api/meters that returns JSON

**2. DATABASE**
Your EGM writes data to a database that UGG reads from.
- Best for: EGMs that log to SQL databases, legacy systems with database access
- UGG does: Runs SQL queries at configured intervals
- You provide: Database connection string, table schema, query templates

**3. LOG**
Your EGM writes events to log files that UGG watches and parses.
- Best for: EGMs that generate text log files, syslog-based systems
- UGG does: Tails log files, parses each line using your format rules
- You provide: Log file path, line format (regex or delimiter-based)

**4. SDK**
Your EGM has a proprietary SDK that UGG wraps.
- Best for: EGMs with manufacturer SDKs (DLLs, shared libraries, Python packages)
- UGG does: Loads your SDK and calls its functions
- You provide: SDK package, API documentation, initialization sequence

**5. FILE**
Your EGM generates batch files (CSV, XML, fixed-width) at regular intervals.
- Best for: Batch-oriented systems, accounting exports, end-of-day reports
- UGG does: Watches a directory for new files, parses and imports them
- You provide: File format documentation, drop directory path, file naming convention

**6. MESSAGE_BUS**
Your EGM publishes events to a message broker (Kafka, AMQP, NATS).
- Best for: Modern event-driven architectures, real-time streaming systems
- UGG does: Subscribes to your topic and processes messages as they arrive
- You provide: Broker URL, topic name, message format documentation"""},

        {"id": "dev-build-connector", "title": "Step-by-Step: Building Your Connector", "content": """**Follow these steps to build a connector for your EGM:**

**Step 1: Document your EGM's data**
Write down every event and meter your EGM produces. For each one, note:
- The event name in your system
- The data fields included
- The data types (numbers, strings, timestamps)
- How often it occurs

Example for a REST EGM:
- Your event: "game_complete" with fields {game_id, bet_cents, win_cents, timestamp}
- Maps to: "device.game.end" with payload {game_id, bet: bet_cents/100, win: win_cents/100}

**Step 2: Use AI Studio for automatic discovery**
1. Go to **AI Studio** in UGG
2. Click the **Discovery** tab
3. Select your source type (REST API, Database, etc.)
4. Paste a sample of your data (a JSON response, a log line, a CSV row)
5. Click **Run Discovery**
6. The AI will automatically detect your fields and suggest canonical event mappings
7. Review the suggestions — the AI shows a confidence percentage for each mapping

**Step 3: Build the mapping in the Connector Builder**
1. Go to **Connectors** in UGG
2. Click the **+** button to create a new connector
3. Give it a name (e.g., "MyBrand REST Connector") and select the type (REST, DB, etc.)
4. Click your new connector to open the **Field Mapping** canvas
5. **Drag fields** from the left (your source fields) onto the right (canonical fields)
6. The center column shows your active mappings
7. Click **Save** when done

Example mappings:
- your "game_id" → canonical "payload.game_id"
- your "bet_cents" → canonical "payload.bet" (with transform: divide by 100)
- your "win_cents" → canonical "payload.win" (with transform: divide by 100)
- your "timestamp" → canonical "occurred_at"

**Step 4: Create a manifest**
In the Connector Builder right panel, click "Create Manifest" to save your mapping configuration. This manifest is what UGG uses to translate your data at runtime.

**Step 5: Test with the Emulator Lab**
See the next article for detailed testing instructions."""},

        {"id": "dev-testing", "title": "Testing Your Connector", "content": """**UGG has a complete testing workbench built in. Use it before deploying to production.**

**Test 1: SmartEGM Simulation**
1. Go to **Emulator Lab** > **SmartEGM** tab
2. Use the 12 Player Verb buttons to simulate player actions:
   - Click "Insert Bill" to put money in
   - Click "Push Play" to simulate a game
   - Click "Cash Out" to print a voucher
3. Watch the EGM State panel on the left — credits, coin in, coin out should update
4. This verifies the basic game cycle works

**Test 2: Run a Pre-Built Script**
1. Go to **Emulator Lab** > **Script Runner** tab
2. Select "Play Cycle Verify" from the Script Library
3. Click **Run Script**
4. The script automatically: inserts a $20 bill, plays 5 games, cashes out, and runs Balanced Meters Analysis
5. All 16 steps should show green (passed)
6. The Balanced Meters section shows 8 accounting tests (BM-01 through BM-08)

**Test 3: Protocol Trace**
1. Go to **Emulator Lab** > **Transcripts** tab
2. You'll see every message exchanged between UGG and the EGM
3. Click any row to expand and see the full XML with syntax highlighting
4. Use the **Find** bar to search for specific commands or values

**Test 4: Live G2S Connection (for G2S EGMs)**
1. Go to **Emulator Lab** > **Live G2S** tab
2. Enter your EGM's SOAP endpoint URL
3. Click **Full Startup** to run the complete G2S handshake
4. Send individual commands using the Command Builder
5. Click **Export ZIP** to save the entire session for review

**Test 5: Certification Suite**
1. Go to **Certification** in the sidebar
2. Select your test device
3. Choose a certification tier (start with Bronze)
4. Click **Run All Tests**
5. Review results per G2S class in the accordion
6. If you pass, you can generate a digitally signed certificate"""},

        {"id": "dev-certification", "title": "Getting Certified", "content": """**UGG has 4 certification tiers. Here's what you need to pass each one:**

**Bronze — Minimum for Route Deployment (6 classes, 44 tests, 80% pass rate)**
Your EGM must correctly handle:
- Cabinet events (power on/off, door open/close, tilt)
- Communications (startup sequence, keepalive)
- Event handling (subscribe, receive, acknowledge)
- Game play (game start, game end with correct amounts)
- Meters (all lifetime meters increment correctly, never decrease)
- Handpay (large win detection, key-off procedure)

**Silver — Casino Floor Deployment (10 classes, 85 tests, 90% pass rate)**
Everything in Bronze plus:
- Bonus (system-triggered bonus awards)
- Command handling (remote enable/disable)
- Download (software update capability)
- GAT (Game Authentication Terminal — software verification)

**Gold — Full Casino with Remote Config (12 classes, 112 tests, 95% pass rate)**
Everything in Silver plus:
- Note acceptor (bill validation, denomination tracking)
- Option configuration (remote parameter changes)

**Platinum — Highest Tier (14 classes, 131 tests, 98% pass rate)**
Everything in Gold plus:
- Progressive jackpots
- Cashless (electronic funds transfer)

**To get certified:**
1. Go to **Certification** in the sidebar
2. Select your device and tier
3. Click **Run All Tests**
4. Fix any failures and re-run
5. When you pass, click **View Certificate** to get your digitally signed certificate
6. The certificate has a public verification URL that anyone can check

**After certification:**
You can list your connector on the **Marketplace** for other operators to install. Go to Connectors > your connector > and your certification badge will be displayed."""},

        {"id": "dev-ai-tools", "title": "Using AI to Speed Up Integration", "content": """**UGG's AI can dramatically speed up your integration work:**

**AI Studio — Automatic Field Discovery**
Instead of manually mapping every field, paste a sample of your EGM's data into AI Studio and let the AI figure out the mappings. It handles:
- JSON REST API responses
- Database query results
- Log file lines
- XML messages
- CSV data files

The AI recognizes common patterns like "bet_amount" → "payload.bet", "machine_id" → "device_id", "timestamp" → "occurred_at" and suggests mappings with confidence scores.

**AI Studio — Connector Code Generation**
1. Go to AI Studio > **Generate** tab
2. Enter your connector name, type, and description
3. Click **Generate Connector**
4. The AI produces:
   - A complete connector manifest
   - Python code skeleton for your connector
   - Suggested test scenarios for the Emulator Lab
   - Deployment and configuration notes

**AI Studio — Chat Assistant**
Have questions about protocols, mapping, or testing? Just ask:
- "How do I map a custom door event to the UGG canonical format?"
- "What's the difference between SAS meter code 0000 and 0008?"
- "How should I handle a progressive jackpot hit in my connector?"
- "What does G2S class eventHandler do?"

The AI knows the complete SAS 6.03, G2S 2.1.0, and UGG specifications."""},

        {"id": "dev-publish", "title": "Publishing on the Marketplace", "content": """**Once your connector is certified, share it with other operators:**

**Step 1: Prepare your listing**
Gather:
- Connector name and description (clear, non-technical)
- Which EGM models it supports
- Which protocols it uses
- Screenshots or documentation
- Pricing model (free, per-device, subscription, one-time)

**Step 2: Your connector is already in the system**
When you built and certified your connector in the Connector Builder, it's already registered in UGG. The certification badge appears automatically.

**Step 3: Other operators find and install it**
Operators browse the Marketplace, filter by category (e.g., "Vendor REST"), read your description and reviews, and click **Install Connector**.

**Step 4: Reviews and ratings**
After operators use your connector, they can rate it 1-5 stars and leave reviews. Your average rating updates automatically. Verified Install badges show when the reviewer actually installed your connector.

**Step 5: Revenue sharing**
For paid connectors, UGG handles billing automatically:
- You keep **70%** of all revenue
- UGG platform fee is **30%**
- Billing runs monthly
- Payments are processed via the EFT system

**Tips for a successful marketplace listing:**
- Write your description for non-technical operators, not engineers
- Include the EGM model names operators will recognize
- Start with a free tier to build installs and reviews
- Respond to feedback and update your connector regularly"""},

        {"id": "dev-content-lab", "title": "Using the Content Lab for Your EGM", "content": """**If your EGM uses SWF (Flash) game content, UGG can analyze it automatically:**

**SWF Asset Analyzer**
1. Go to **Content Lab** in the sidebar
2. Click the **SWF Analyzer** tab
3. Upload your EGM's SWF game file (or .crdownload file)
4. UGG automatically:
   - Decompresses the file (supports zlib-compressed CWS format)
   - Extracts all ActionScript strings and identifiers
   - Classifies content into categories: slot mechanics, bonus features, player tracking, financial events, system commands
   - Suggests canonical event mappings for each identifier found
   - Shows confidence percentages for each mapping

**Binary Inspector**
1. Click the **Binary Inspector** tab
2. Upload any binary file (SWF, protocol dumps, firmware images)
3. UGG shows a hex dump with offset, hex values, and ASCII representation
4. Navigate with Prev/Next buttons to inspect different sections

**Content Registry**
1. After analyzing your SWF, click **Register to Content Registry**
2. Enter the game title, manufacturer, and version
3. UGG tracks which game content versions are deployed across the estate
4. This helps with regulatory compliance — you can prove exactly what software is running on each machine

**Why this matters:**
Regulators require that all game software is approved and unmodified. UGG's Content Lab gives you and the regulator a complete chain of custody for game content, from the binary file all the way to the integrity check on the live machine."""},

        {"id": "dev-device-template", "title": "Creating a Device Template XML", "content": """**A Device Template XML file defines your EGM's capabilities for the Emulator Lab:**

**What goes in a Device Template:**
- Manufacturer and model name
- Software version and signature
- Supported denominations (e.g., $0.01, $0.05, $0.25, $1.00)
- G2S device classes your EGM supports
- Game outcome probabilities (win levels and multipliers)
- Unsupported event patterns (events your EGM won't generate)

**Example template:**
```xml
<deviceTemplate version="1.0" manufacturer="YourBrand" model="GameKing-500" softwareVersion="2.1.0">
  <metadata>
    <serialNumber>SN-00001</serialNumber>
    <softwareSignature>abc123def456</softwareSignature>
    <g2sSchemaVersion>G2S_2.1.0</g2sSchemaVersion>
  </metadata>
  <denominations active="true">
    <denom value="100"/>   <!-- $1.00 -->
    <denom value="500"/>   <!-- $5.00 -->
    <denom value="2500"/>  <!-- $25.00 -->
  </denominations>
  <devices>
    <device class="G2S_cabinet" id="1" hostEnabled="true"/>
    <device class="G2S_gamePlay" id="1" hostEnabled="true"/>
    <device class="G2S_meters" id="1" hostEnabled="true"/>
    <device class="G2S_noteAcceptor" id="1" hostEnabled="true"/>
    <device class="G2S_voucher" id="1" hostEnabled="true"/>
  </devices>
  <gameOutcomes>
    <winLevel id="0" name="NoWin" probability="0.70" multiplier="0"/>
    <winLevel id="1" name="SmallWin" probability="0.20" multiplier="1.5"/>
    <winLevel id="2" name="BigWin" probability="0.09" multiplier="25"/>
    <winLevel id="3" name="Jackpot" probability="0.01" multiplier="250"/>
  </gameOutcomes>
</deviceTemplate>
```

**How to use it:**
1. Go to **Emulator Lab** > **Templates** tab
2. Paste your XML in the text area
3. Click **Parse Template**
4. UGG shows the parsed results: denominations, classes, win levels
5. Load the template into a SmartEGM session to test with your exact configuration

**This makes testing realistic** — instead of using generic settings, the Emulator Lab simulates YOUR exact EGM with YOUR denominations, YOUR supported classes, and YOUR win probability distribution."""},
    ]},

    {"id": "indie-nocode", "title": "Indie & NoCode Developers", "icon": "Rocket", "docs": [
        {"id": "indie-welcome", "title": "Welcome, Indie Game Developer!", "content": """**You built a game. Now you want it to work with real gaming systems. This guide is for you.**

If you built your game using a NoCode platform (like Bubble, Adalo, FlutterFlow, Buildship, Make, Zapier, n8n, or similar), or you're a solo developer who isn't a protocol engineer — this section will hold your hand through every single step.

**You do NOT need to know:**
- What SAS or G2S protocols are
- How serial ports work
- How to write Python or JavaScript code
- What SOAP or XML is
- Anything about gaming regulations

**What you DO need:**
- Your game running on a computer (Windows, Mac, or Linux)
- Your game can do ONE of these things:
  - Send data to a web address (HTTP/REST) — this is what most NoCode tools do
  - Write data to a database
  - Write data to a file (CSV, JSON, or text log)
- An internet connection

**The big picture:**
Your game produces data: "someone played," "someone won," "money went in," "money came out." UGG needs to receive that data in a specific format. We'll show you exactly what format, give you copy-paste templates, and walk you through connecting everything.

**Time to get connected: About 2-4 hours following this guide.**"""},

        {"id": "indie-what-ugg-needs", "title": "What UGG Needs From Your Game", "content": """**UGG needs your game to send 6 types of events. That's it.**

Think of these as messages your game sends to UGG every time something happens:

**1. Game Started** — "A player just started playing"
Send this when a player begins a new round/spin/hand.
Data needed: how much they bet

**2. Game Ended** — "The round is over"
Send this when the round finishes.
Data needed: how much they bet, how much they won (0 if they lost)

**3. Money In** — "Money was added to the machine"
Send this when a player inserts cash, loads credits, or redeems a voucher.
Data needed: amount added, type (cash, voucher, or electronic)

**4. Money Out** — "Money was removed from the machine"
Send this when a player cashes out or a voucher is printed.
Data needed: amount removed

**5. Machine Status** — "I'm online" or "I'm offline"
Send this when your game starts up and when it shuts down.

**6. Error/Alert** — "Something went wrong"
Send this if your game encounters a problem (optional but recommended).
Data needed: what went wrong

**That's the complete list.** If your game can send those 6 messages to a web address, you can connect to UGG."""},

        {"id": "indie-easiest-method", "title": "The Easiest Way to Connect (REST API)", "content": """**The simplest path: Send HTTP POST requests to UGG's API.**

Every NoCode platform can send HTTP requests. Here's exactly what to send:

**The UGG API endpoint your game will talk to:**
`https://your-ugg-server.com/api/events`

**What to send (JSON format):**
Every time something happens in your game, send a POST request with this format:

```json
{
  "device_id": "MY-GAME-001",
  "event_type": "device.game.end",
  "protocol": "PROPRIETARY",
  "occurred_at": "2026-01-15T14:30:00Z",
  "severity": "info",
  "payload": {
    "bet": 5.00,
    "win": 12.50,
    "game_id": 42
  }
}
```

**Let's break down each field:**
- **device_id** — A unique name for your game machine. Pick anything like "MY-GAME-001" or "LOBBY-KIOSK-3". Keep it the same every time for the same machine.
- **event_type** — What happened. Use these exact values:
  - `device.game.start` — Player started a round
  - `device.game.end` — Round finished
  - `device.voucher.in` — Money added
  - `device.voucher.out` — Money removed/cashed out
  - `device.status.online` — Game is running
  - `device.status.offline` — Game shut down
  - `device.tilt` — Error occurred
- **protocol** — Always use `"PROPRIETARY"` (this tells UGG you're not using SAS or G2S)
- **occurred_at** — The date and time. Use this format: YYYY-MM-DDTHH:MM:SSZ
- **severity** — How important: `"info"` for normal events, `"warning"` for alerts, `"critical"` for errors
- **payload** — The details. Different for each event type (see the templates below)"""},

        {"id": "indie-templates", "title": "Copy-Paste Event Templates", "content": """**Copy these templates and fill in your values. One for each event type:**

**Template 1: Game Started**
```json
{
  "device_id": "YOUR-GAME-ID",
  "event_type": "device.game.start",
  "protocol": "PROPRIETARY",
  "occurred_at": "PASTE-CURRENT-TIMESTAMP",
  "severity": "info",
  "payload": {
    "bet": 0.00,
    "denomination": 0.25,
    "game_title": "Your Game Name"
  }
}
```
Replace: YOUR-GAME-ID with your machine name, bet with the wager amount, denomination with the base credit value

**Template 2: Game Ended (with win/loss)**
```json
{
  "device_id": "YOUR-GAME-ID",
  "event_type": "device.game.end",
  "protocol": "PROPRIETARY",
  "occurred_at": "PASTE-CURRENT-TIMESTAMP",
  "severity": "info",
  "payload": {
    "bet": 5.00,
    "win": 12.50,
    "game_title": "Your Game Name",
    "credits_remaining": 100
  }
}
```
Replace: bet with wager amount, win with amount won (use 0 for a loss)

**Template 3: Money Inserted**
```json
{
  "device_id": "YOUR-GAME-ID",
  "event_type": "device.voucher.in",
  "protocol": "PROPRIETARY",
  "occurred_at": "PASTE-CURRENT-TIMESTAMP",
  "severity": "info",
  "payload": {
    "amount": 20.00,
    "type": "cash"
  }
}
```
Replace: amount with dollars inserted, type with "cash", "voucher", or "electronic"

**Template 4: Cash Out**
```json
{
  "device_id": "YOUR-GAME-ID",
  "event_type": "device.voucher.out",
  "protocol": "PROPRIETARY",
  "occurred_at": "PASTE-CURRENT-TIMESTAMP",
  "severity": "info",
  "payload": {
    "amount": 35.00
  }
}
```

**Template 5: Machine Online**
```json
{
  "device_id": "YOUR-GAME-ID",
  "event_type": "device.status.online",
  "protocol": "PROPRIETARY",
  "occurred_at": "PASTE-CURRENT-TIMESTAMP",
  "severity": "info",
  "payload": {
    "game_title": "Your Game Name",
    "version": "1.0"
  }
}
```

**Template 6: Error**
```json
{
  "device_id": "YOUR-GAME-ID",
  "event_type": "device.tilt",
  "protocol": "PROPRIETARY",
  "occurred_at": "PASTE-CURRENT-TIMESTAMP",
  "severity": "warning",
  "payload": {
    "reason": "Describe what went wrong"
  }
}
```"""},

        {"id": "indie-nocode-bubble", "title": "Connecting from Bubble.io", "content": """**Step-by-step for Bubble.io users:**

**Step 1: Set up the API connection**
1. In your Bubble app, go to **Plugins** > **API Connector**
2. Click **Add another API**
3. Name it "UGG Gaming Gateway"
4. Authentication: None (or Bearer Token if your UGG requires it)

**Step 2: Create the API call**
1. Click **Add another call**
2. Name it "Send Game Event"
3. Method: **POST**
4. URL: `https://your-ugg-server.com/api/events`
5. Headers: Add `Content-Type` = `application/json`
6. Body type: **JSON**
7. Body: Paste this and check "Private" for each parameter:

```
{
  "device_id": "<device_id>",
  "event_type": "<event_type>",
  "protocol": "PROPRIETARY",
  "occurred_at": "<occurred_at>",
  "severity": "info",
  "payload": {
    "bet": <bet>,
    "win": <win>
  }
}
```

8. Click **Initialize call** to test

**Step 3: Trigger from your game**
In your Bubble workflows:
1. When the player clicks "Spin" or "Play" → trigger "Send Game Event" with event_type = "device.game.start"
2. When the round result is calculated → trigger "Send Game Event" with event_type = "device.game.end" and include bet/win amounts
3. When the player adds credits → trigger with event_type = "device.voucher.in"
4. When the player cashes out → trigger with event_type = "device.voucher.out"

**Step 4: Verify in UGG**
Log into UGG, go to Device Fleet, and search for your device_id. You should see it appear with events flowing in!"""},

        {"id": "indie-nocode-make", "title": "Connecting from Make.com / Zapier / n8n", "content": """**Step-by-step for automation platforms (Make, Zapier, n8n):**

These platforms are perfect for connecting your game to UGG because they're designed to send HTTP requests between systems.

**Using Make.com (formerly Integromat):**

1. Create a new **Scenario**
2. Add a **Webhook** trigger (this receives events from your game)
3. Add an **HTTP** module → **Make a request**
4. Configure the HTTP module:
   - URL: `https://your-ugg-server.com/api/events`
   - Method: POST
   - Body type: Raw
   - Content type: JSON
   - Request content: Paste the event template from the previous article
   - Map your webhook fields to the template fields

**Using Zapier:**

1. Create a new **Zap**
2. Trigger: **Webhook by Zapier** → Catch Hook
3. Action: **Webhooks by Zapier** → POST
4. URL: `https://your-ugg-server.com/api/events`
5. Payload Type: JSON
6. Data: Map your fields to the UGG event template

**Using n8n:**

1. Create a new **Workflow**
2. Add a **Webhook** node (trigger)
3. Add an **HTTP Request** node
4. Method: POST
5. URL: `https://your-ugg-server.com/api/events`
6. Body Content Type: JSON
7. Body Parameters: Map from the webhook data to UGG event format

**Pro tip for all platforms:**
Create separate scenarios/zaps for each event type (game start, game end, money in, money out). This keeps things organized and easy to debug."""},

        {"id": "indie-nocode-prompts", "title": "AI Prompts for Your NoCode Platform", "content": """**Copy-paste these prompts into your NoCode platform's AI assistant (or ChatGPT) to generate the integration code:**

**Prompt 1: Generate the API connection setup**
```
I need to connect my NoCode game application to the UGG (Universal Gaming Gateway) REST API. The API endpoint is [YOUR-UGG-URL]/api/events and accepts POST requests with JSON body. The JSON format requires these fields: device_id (string, my machine's unique ID), event_type (string, one of: device.game.start, device.game.end, device.voucher.in, device.voucher.out, device.status.online, device.tilt), protocol (always "PROPRIETARY"), occurred_at (ISO 8601 UTC timestamp), severity (string: info, warning, or critical), and payload (object with event-specific data like bet amount and win amount). Please generate the complete API connection configuration for [YOUR NOCODE PLATFORM NAME].
```

**Prompt 2: Generate the game event workflow**
```
I have a game in [YOUR NOCODE PLATFORM]. When a player clicks the Play button, I need to: 1) Send a "device.game.start" event to my UGG API with the bet amount. 2) Calculate the game result. 3) Send a "device.game.end" event with both the bet and win amounts. The API endpoint is [YOUR-UGG-URL]/api/events, method POST, content-type JSON. My device_id is "[YOUR-DEVICE-ID]". Please generate the complete workflow with all HTTP request configurations.
```

**Prompt 3: Generate the meter tracking workflow**
```
I need to track money in and money out for my game connected to UGG. When a player adds credits (inserts money), send event_type "device.voucher.in" with the amount in the payload. When a player cashes out, send event_type "device.voucher.out" with the amount. The UGG API is at [YOUR-UGG-URL]/api/events, POST, JSON. Device ID is "[YOUR-DEVICE-ID]". Please create the complete workflow for both money-in and money-out tracking.
```

**Prompt 4: Generate startup/shutdown notifications**
```
My game application needs to notify UGG when it starts and stops. On application start, send a POST to [YOUR-UGG-URL]/api/events with event_type "device.status.online" and payload containing game_title and version. On application shutdown/close, send event_type "device.status.offline". Device ID is "[YOUR-DEVICE-ID]", protocol is "PROPRIETARY". Please generate the startup and shutdown event handlers for [YOUR NOCODE PLATFORM].
```

**Prompt 5: Generate error reporting**
```
When my game encounters any error, I need to report it to UGG for monitoring. Send a POST to [YOUR-UGG-URL]/api/events with event_type "device.tilt", severity "warning" (or "critical" for serious errors), and payload containing a "reason" field describing the error. Device ID is "[YOUR-DEVICE-ID]". Please generate an error handler that catches all errors and reports them to UGG.
```

**How to use these prompts:**
1. Copy the prompt
2. Replace [YOUR-UGG-URL] with your actual UGG server address
3. Replace [YOUR-DEVICE-ID] with your machine's ID
4. Replace [YOUR NOCODE PLATFORM] with your platform name (Bubble, Adalo, FlutterFlow, etc.)
5. Paste into your platform's AI assistant or ChatGPT
6. Follow the generated instructions"""},

        {"id": "indie-file-method", "title": "Alternative: File Drop Method (No Internet Needed)", "content": """**If your game can't send HTTP requests, use the File Drop method instead.**

This is the simplest possible integration — your game writes a text file, UGG picks it up.

**How it works:**
1. Your game writes a line to a CSV file every time something happens
2. UGG's File Connector watches that folder and reads new lines
3. That's it — no internet, no API, no HTTP requests

**Step 1: Create a CSV file**
Your game writes to a file called `game_events.csv` in a specific folder.

**The CSV format (one line per event):**
```
timestamp,device_id,event_type,bet,win,amount,reason
2026-01-15T14:30:00Z,MY-GAME-001,game_end,5.00,12.50,,
2026-01-15T14:30:15Z,MY-GAME-001,game_start,5.00,,,
2026-01-15T14:31:00Z,MY-GAME-001,money_in,,,20.00,cash
2026-01-15T14:45:00Z,MY-GAME-001,cash_out,,,35.00,
2026-01-15T14:45:01Z,MY-GAME-001,status,,,,offline
```

**Step 2: Tell UGG where the file is**
In UGG's Connector Builder, create a new FILE connector pointing to your CSV folder.

**Step 3: Map the columns**
In the Connector Builder mapping canvas:
- Drag "timestamp" → "occurred_at"
- Drag "device_id" → "device_id"
- Drag "event_type" → "event_type" (with transform: add "device." prefix)
- Drag "bet" → "payload.bet"
- Drag "win" → "payload.win"
- Drag "amount" → "payload.amount"

**For NoCode platforms that export to Google Sheets or Airtable:**
You can write your events to a spreadsheet instead! Then use Make.com or Zapier to forward the rows to UGG's API. This is a great approach if your NoCode platform doesn't support direct HTTP POST but can write to Google Sheets.

**Prompt for your NoCode AI assistant:**
```
Every time a game event happens in my application, I need to add a row to a Google Sheet (or CSV file) with these columns: timestamp (ISO 8601 UTC), device_id (always "[YOUR-DEVICE-ID]"), event_type (game_start, game_end, money_in, cash_out, or status), bet (number, the wager amount), win (number, the win amount), amount (number, for money in/out), reason (text, for errors). Please set up this event logging for all game actions.
```"""},

        {"id": "indie-testing", "title": "Testing Your NoCode Integration", "content": """**Before going live, verify your game is sending data correctly:**

**Quick Test (5 minutes):**
1. Log into UGG
2. Go to **Device Fleet**
3. Search for your device_id (whatever you set, like "MY-GAME-001")
4. If your game is connected correctly, you should see it in the list with a green dot
5. Click it to see the detail panel — check the Events tab for your recent events

**What to look for:**
- Events should appear within a few seconds of the action in your game
- The event_type should match what you sent
- The payload should contain the correct bet/win amounts
- Timestamps should be in UTC and close to the actual time

**If your device doesn't appear:**
- Check that your UGG API URL is correct (no typos!)
- Check that you're sending valid JSON (use jsonlint.com to validate)
- Check that the Content-Type header is set to application/json
- Look at your NoCode platform's error logs for failed HTTP requests
- Try the request manually using a tool like Reqbin.com (paste your URL and JSON)

**Full Integration Test:**
1. Go to **Emulator Lab** in UGG
2. Click the **Script Runner** tab
3. Select **Play Cycle Verify**
4. Click **Run Script**
5. Compare the Emulator Lab events with your game's events — they should follow the same pattern:
   - Money in → Game starts → Game ends (with win/loss) → Cash out

**Balanced Meters Check:**
After running your game for a while:
- Go to Route Operations > Overview
- Your device should show Coin In and Coin Out totals
- Coin In should equal the total money inserted by players
- If the numbers don't match, check your event amounts — they might be in cents instead of dollars or vice versa

**Congratulations!**
Once events are flowing, your game is connected to UGG. Operators on the route will be able to see your machine's performance alongside all their other EGMs, and it will be included in NOR reports, tax calculations, and regulatory filings."""},

        {"id": "indie-database-method", "title": "Alternative: Database Method", "content": """**If your NoCode platform uses a database (like Supabase, Firebase, or Airtable), UGG can read directly from it.**

**Step 1: Create an events table in your database**
Your table should have these columns:
- `id` — Unique ID for each event (auto-generated)
- `timestamp` — When it happened (date/time)
- `device_id` — Your machine ID (text)
- `event_type` — What happened (text)
- `bet` — Wager amount (number, nullable)
- `win` — Win amount (number, nullable)
- `amount` — Money in/out amount (number, nullable)
- `processed` — Whether UGG has read it yet (true/false, default false)

**Step 2: Your game writes to this table**
Every time something happens in your game, insert a new row.

**Step 3: Configure UGG's Database Connector**
In UGG's Connector Builder:
1. Create a new connector with type "DATABASE"
2. Enter your database connection details
3. UGG will poll your table every few seconds for rows where `processed = false`
4. After reading each row, UGG sets `processed = true`

**Prompt for Supabase/Firebase setup:**
```
I need a database table called "game_events" with columns: id (auto-increment), timestamp (timestamptz, default now()), device_id (text), event_type (text), bet (numeric nullable), win (numeric nullable), amount (numeric nullable), processed (boolean default false). Every time a player action happens in my game, I need to insert a row into this table. Please set up the table and the insert functions for each game action: game_start (with bet), game_end (with bet and win), money_in (with amount), cash_out (with amount), status_online, and error (with reason in a text column).
```

**This method is great because:**
- Your game just writes to a database (which most NoCode platforms already do)
- No HTTP configuration needed
- UGG handles all the polling and translation
- If UGG is temporarily unreachable, the events just queue up in your database"""},

        {"id": "indie-receive-messages", "title": "Receiving Messages from Operators", "content": """**Operators can send messages to your game screen — here's how to display them.**

Route operators need to push messages to your game: promotions ("Earn 2X points this weekend!"), maintenance notices ("Scheduled maintenance tonight"), responsible gambling reminders, or urgent alerts. Your game needs to check for these messages and show them to the player.

**How it works — 3 simple steps:**

**Step 1: Your game polls UGG every 30 seconds**
Send a GET request to this URL:
`https://your-ugg-server.com/api/device-messages/poll/YOUR-DEVICE-ID`

No login or authentication needed — just your device ID in the URL.

**The response looks like this:**
```json
{
  "device_id": "MY-GAME-001",
  "messages": [
    {
      "id": "abc-123-def",
      "text": "Earn 2X loyalty points this weekend!",
      "type": "PROMO",
      "duration_seconds": 30,
      "position": "BOTTOM",
      "background_color": "#00D97E",
      "text_color": "#FFFFFF",
      "priority": "NORMAL"
    }
  ],
  "count": 1,
  "poll_again_seconds": 30
}
```

**Step 2: Display the message on your game screen**
When you get messages back (count > 0), show them to the player:
- **position** tells you where: "TOP", "BOTTOM", "CENTER", or "FULLSCREEN"
- **duration_seconds** tells you how long to show it
- **type** tells you the style: "INFO" (blue), "PROMO" (green), "MAINTENANCE" (yellow), "RESPONSIBLE_GAMBLING" (orange), "URGENT" (red)
- **background_color** and **text_color** are optional custom colors

**Step 3: Tell UGG the message was shown**
After displaying the message, send a POST to:
`https://your-ugg-server.com/api/device-messages/displayed/MESSAGE-ID`

When the player dismisses it (clicks X or it times out), send:
`https://your-ugg-server.com/api/device-messages/acknowledged/MESSAGE-ID`

Replace MESSAGE-ID with the "id" field from the message.

**That's it!** The operator in UGG can see that your game received and displayed the message."""},

        {"id": "indie-message-prompts", "title": "Prompts: Adding Message Display to Your Game", "content": """**Copy-paste these prompts into your NoCode AI assistant to add message receiving:**

**Prompt 1: Set up message polling**
```
I need my game application to check for new messages every 30 seconds from the UGG gaming system. Send a GET request to [YOUR-UGG-URL]/api/device-messages/poll/[YOUR-DEVICE-ID] (no authentication needed). The response is JSON with a "messages" array. Each message has: id (string), text (string to display), type (INFO/PROMO/MAINTENANCE/RESPONSIBLE_GAMBLING/URGENT), duration_seconds (how long to show it), position (TOP/BOTTOM/CENTER/FULLSCREEN), background_color (optional hex color), text_color (optional hex color). If the messages array is not empty, display each message to the user. Please set up this polling mechanism in [YOUR NOCODE PLATFORM].
```

**Prompt 2: Display the message banner**
```
When my game receives a message from UGG (from the polling response), I need to display it as a banner overlay on the game screen. The banner should: appear at the position specified (TOP/BOTTOM/CENTER/FULLSCREEN), use the background_color and text_color if provided (otherwise use defaults based on type: INFO=blue, PROMO=green, MAINTENANCE=yellow, URGENT=red), show the "text" field as the message content, have a close/dismiss X button, auto-hide after "duration_seconds" seconds if the player doesn't dismiss it. After the banner appears, send a POST to [YOUR-UGG-URL]/api/device-messages/displayed/MESSAGE_ID (no body needed). When the player clicks dismiss or the timer expires, send a POST to [YOUR-UGG-URL]/api/device-messages/acknowledged/MESSAGE_ID. Please build this message display component for [YOUR NOCODE PLATFORM].
```

**Prompt 3: Simple version for Bubble.io**
```
In my Bubble.io game app, I need to: 1) Set up a recurring workflow that runs every 30 seconds. 2) In that workflow, make an API call (GET) to [YOUR-UGG-URL]/api/device-messages/poll/[YOUR-DEVICE-ID]. 3) If the response has messages (count > 0), show a floating group/popup with the message text, styled based on the message type. 4) After showing the popup, make an API call (POST) to [YOUR-UGG-URL]/api/device-messages/displayed/[message-id]. 5) When the user closes the popup, make an API call (POST) to [YOUR-UGG-URL]/api/device-messages/acknowledged/[message-id]. Please give me step-by-step instructions for setting this up in Bubble.
```

**Prompt 4: For Make.com/Zapier (polling approach)**
```
I need a Make.com scenario that runs every 30 seconds (or 1 minute). Step 1: HTTP GET request to [YOUR-UGG-URL]/api/device-messages/poll/[YOUR-DEVICE-ID]. Step 2: If response.count > 0, for each message: send a notification to my game (via webhook, push notification, or Slack/Discord). Step 3: After sending, POST to [YOUR-UGG-URL]/api/device-messages/displayed/[message-id] to confirm delivery. This way my game gets real-time messages from the operator through my automation platform.
```

**Message types your game should handle:**
- **INFO** — General information, show in blue/neutral style
- **PROMO** — Promotional offers, show in green/exciting style with maybe a special icon
- **MAINTENANCE** — System notices, show in yellow/warning style
- **RESPONSIBLE_GAMBLING** — Required by regulators, show prominently in orange
- **URGENT** — Critical alerts, show in red and don't auto-dismiss (require player to click)"""},

        {"id": "indie-message-examples", "title": "Real Examples: What Operators Will Send", "content": """**Here are real-world messages operators send to EGM screens:**

**Promotional messages (type: PROMO):**
- "Earn 2X loyalty points this weekend!"
- "Happy Hour: All wins doubled 4-6 PM"
- "Join our Player's Club — ask the attendant"
- "Progressive jackpot now over $50,000!"

**Maintenance notices (type: MAINTENANCE):**
- "Scheduled maintenance tonight 2:00-4:00 AM"
- "System update in progress — brief interruption expected"
- "Voucher printer maintenance — cash out may be delayed"

**Responsible gambling (type: RESPONSIBLE_GAMBLING):**
- "Know your limit. Play within it."
- "Need help? Call 1-800-522-4700"
- "You've been playing for over 2 hours. Consider taking a break."
- "Set a spending limit before you play"
These are REQUIRED by most state gaming regulators. Your game MUST be able to display these.

**Urgent alerts (type: URGENT):**
- "This machine is being taken out of service"
- "Please see an attendant"
- "Credit meter error — do not insert additional funds"

**What your game display should look like:**
- A semi-transparent banner overlaying your game
- Clear, readable text (at least 16px font)
- An X or "Close" button so the player can dismiss it
- For RESPONSIBLE_GAMBLING and URGENT types, consider making the banner more prominent (larger, centered, maybe with a sound)

**Minimum requirements for regulatory compliance:**
1. Messages must be displayed within 30 seconds of being sent
2. RESPONSIBLE_GAMBLING messages must be displayed prominently (not tiny text in a corner)
3. URGENT messages should not auto-dismiss — require player action
4. Your game must acknowledge receipt (the POST to /displayed/ endpoint)

**Test your message display:**
1. Log into UGG as an operator
2. Go to Messages in the sidebar
3. Create a new campaign targeting your device ID
4. Send it
5. Your game should show the message within 30 seconds (on its next poll)"""},
    ]},

    {"id": "going-live", "title": "Going Live (Production)", "icon": "Rocket", "docs": [
        {"id": "live-overview", "title": "Launching UGG for Real Operations", "content": """**Ready to go from demo mode to live production? Here's everything you need to know.**

UGG has two modes:
- **Demo Mode** — What you've been using. Filled with sample data (85 fake devices, fake NOR data, test players). Perfect for learning the system.
- **Production Mode** — A clean, empty database. You add real distributors, real venues, and connect real EGMs.

**You do NOT lose anything by switching.** Production mode starts fresh — your demo data stays until you explicitly clear it.

**The transition takes about 30 minutes following this guide.**"""},

        {"id": "live-step1-clean", "title": "Step 1: Clear Demo Data", "content": """**Before going live, clear out all the fake data:**

1. Log in as admin
2. The system has a reset function that clears all demo data while keeping your admin account
3. After reset, the system is completely empty — no fake devices, no fake money, no test players

**What gets cleared:**
- All 85 demo devices and their events
- All fake financial transactions
- All demo NOR data
- All test players and PIRS data
- All demo alerts and exceptions
- All demo marketplace data

**What is preserved:**
- Your admin account (you stay logged in)
- Your PIRS configuration settings (if you've customized them)
- System settings

**Important:** This cannot be undone! Make sure you're ready before clearing. You can always reload demo data later if you want to show someone how the system works."""},

        {"id": "live-step2-company", "title": "Step 2: Set Up Your Company", "content": """**Now add your real business information:**

1. Go to **Settings** in the sidebar
2. In the **Tenants** tab, your company should already be listed (if you set it up during initialization)
3. If not, your administrator will create your tenant with:
   - Company name
   - Timezone
   - Currency

4. In the **Sites** tab, add your real locations:
   - Site name (e.g., "Starlight Las Vegas Main Floor")
   - Address
   - Timezone

5. Go to **Route Operations** > **RBAC Portal** tab to create user accounts:
   - Your distributor admin accounts
   - Your retailer/venue viewer accounts
   - Your manufacturer viewer accounts (if applicable)

**Each person gets their own login** with permissions matching their role. A retailer can only see their own venue's data."""},

        {"id": "live-step3-devices", "title": "Step 3: Connect Your Real EGMs", "content": """**Now the exciting part — connecting real machines!**

**For SAS machines (older, serial cable):**
1. Make sure the UGG Agent box is installed at each venue (see Hardware > Setting Up a UGG Agent)
2. Connect the RS-232 serial cable from the EGM to the agent
3. The machine should appear in Device Fleet within 2-3 minutes
4. Verify the machine's status shows green (online)
5. Click the machine to verify manufacturer, model, and serial are correct

**For G2S machines (newer, network):**
1. Ensure the machine is on the same network as the UGG Agent
2. Go to Emulator Lab > Live G2S tab
3. Enter the machine's SOAP endpoint URL
4. Click Connect — watch the startup sequence complete
5. The machine appears in Device Fleet

**For indie/NoCode EGMs:**
Follow the Indie Developer Guide in the Documentation. Your game sends HTTP POST requests to UGG's API.

**Add machines one at a time.** Verify each one works before connecting the next. This makes troubleshooting much easier.

**After all machines are connected:**
- Go to Mission Control — you should see your real device count
- Check the Route Map — your real venues should appear at their actual locations
- Verify Route Operations > Overview shows your real NOR data (it will start at $0 and grow as players play)"""},

        {"id": "live-step4-pirs", "title": "Step 4: Configure PIRS for Real Players", "content": """**Set up your reward system before real players start using loyalty cards:**

1. Go to **PIRS Rewards** > **Settings** tab
2. Set your real budgets:
   - Start conservative: **$100-$200 daily** until you see ROI data
   - Per player daily: **$25-$50**
   - Per player session: **$15-$25**
3. Review the default bonus rules in the **Bonus Rules** tab:
   - Turn OFF any rules you don't want active yet
   - Edit POC amounts to match your budget ($5-$10 for starters)
   - Enable the Welcome Bonus (card_in rule) with $5-$10 for new players
4. Turn ON the auto-engine: Settings > Auto-run reward rules = ON
5. Set auto-scale: ON (so churn scores adjust as players grow)

**Start with just 2-3 rules active:**
- Welcome Bonus ($5 on card-in for score 60+)
- Session Length ($10 at 45 minutes for score 65+)
- Lapse Prevention ($15 for lapse risk 70+)

**After 1-2 weeks:**
Check Business Impact tab. If ROI is above 8:1, start enabling more rules and increasing amounts. If below 5:1, tighten the churn score requirements (raise minimum from 60 to 70)."""},

        {"id": "live-step5-verify", "title": "Step 5: Verify Everything Works", "content": """**Before you walk away, verify these 10 things:**

1. **Mission Control loads** with your real device count and zero alerts (or only real ones)
2. **All EGMs show green** in Device Fleet — click each one to verify status
3. **Route Map shows your real venues** at correct geographic locations
4. **NOR starts tracking** — play a few games on a test machine, then check Route Operations > NOR. You should see small amounts within minutes
5. **Alerts work** — Open a machine door, verify DOOR_OPEN alert appears within 30 seconds
6. **PIRS is running** — Insert a loyalty card, verify the player appears in PIRS Rewards
7. **Messages work** — Go to Messages, create a test campaign targeting one machine, verify the message appears on screen
8. **Export works** — Go to Export, download a Devices CSV, verify your real machines are listed
9. **Other users can log in** — Have your distributor admin log in and verify they see only their route
10. **Documentation is accessible** — Click Documentation in the sidebar, verify all guides load

**If everything checks out — congratulations! Your UGG system is live!**

**First week routine:**
- Check Mission Control 3x daily (morning, midday, evening)
- Handle any alerts within 1 hour for critical, 24 hours for warnings
- Review PIRS Business Impact every 2-3 days
- Run your first EFT at the end of the week
- Export your first NOR report for your records"""},

        {"id": "live-switching-modes", "title": "Switching Between Demo and Production", "content": """**You can switch between demo data and production at any time.**

**To load demo data (for training or demonstrations):**
An admin can trigger demo data loading. This adds the 85 sample devices, fake NOR data, and test players alongside any real data you have.

**Warning:** Only do this on a separate demo instance, NOT on your production system. Mixing demo and real data makes reports inaccurate.

**To go back to clean production:**
The reset function clears everything except your admin account. Then reconnect your real devices.

**Best practice:**
Keep two UGG instances:
1. **Production** — Your live system with real data. SEED_MODE=production
2. **Demo/Training** — A separate instance with sample data for training new staff. SEED_MODE=demo

Your deployment team can set the SEED_MODE in the environment configuration:
- SEED_MODE=demo — Loads sample data on startup (default)
- SEED_MODE=production — Starts clean, no demo data, first-run setup wizard"""},
    ]},

    {"id": "pirs-rewards", "title": "PIRS Player Rewards", "icon": "Crown", "docs": [
        {"id": "pirs-what-is", "title": "What is PIRS?", "content": """**PIRS (Players Intelligence Rewards System) is your secret weapon for keeping players coming back.**

Think of PIRS as a smart loyalty manager that watches how every player behaves and automatically rewards the ones most likely to keep playing. It uses artificial intelligence to figure out which players are your most valuable, and sends them bonus credits at exactly the right moment.

**What PIRS does for you:**
- Tracks every player who uses a loyalty card
- Calculates a "Churn Score" (0-100) for each player — higher means they play back more of their winnings instead of cashing out
- Automatically sends Play Only Credits (POC) — bonus money that can be played but not cashed out
- Monitors Return-to-Player (RTP) rates and flags players who've been unlucky
- Groups players into tiers (Bronze → Silver → Gold → Platinum → Diamond) so your best players get the best rewards
- Tracks the ROI of every bonus dollar you spend

**The bottom line:** For every $1 you invest in POC, PIRS players typically generate $10-15 in additional play. That's a 10-15x return on your investment.

**Where to find it:**
Click **PIRS Rewards** in the left sidebar (look for the crown icon)."""},

        {"id": "pirs-dashboard-tour", "title": "Understanding the PIRS Dashboard", "content": """**The PIRS dashboard has 6 tabs. Here's what each one does:**

**Tab 1: Fleet Overview**
The big picture of your entire player base:
- **7 KPI cards at top:** Total Players, Active Now (playing right now), Average Churn Score, Lifetime Coin-In, POC awarded today, Awards today, Players at risk of leaving
- **Churn Score Distribution chart:** Bar chart showing how many players are in each segment (Elite, High Value, Mid Value, Developing, Casual, Low Value)
- **Tiers:** Your loyalty tiers and their POC multipliers
- **Live Bonus Feed:** Real-time list of POC being awarded right now

**Tab 2: Player Intelligence**
Deep dive into individual players:
- Left side: Leaderboard ranked by Churn Score
- Right side: Click any player to see their full profile — play-back rate, cash-out rate, lapse risk, POC ROI, session history, recent awards
- Quick POC buttons to send $5-$50 directly to a player

**Tab 3: Bonus Rules**
All your reward rules — create, edit, toggle, delete (see separate article)

**Tab 4: RTP Compensation**
Find and help players who've been unlucky (see separate article)

**Tab 5: Business Impact**
Your return on investment — how much POC you've invested vs how much coin-in it generated

**Tab 6: Settings**
Configure budgets, multipliers, and engine controls (see separate article)"""},

        {"id": "pirs-churn-score", "title": "Understanding Churn Scores", "content": """**The Churn Score is the most important number in PIRS. Here's what it means.**

Every player gets a score from 0 to 100. A higher score means the player is more valuable because they tend to play back their winnings instead of cashing out.

**How it's calculated (you don't need to remember this — the AI does it automatically):**
- **25% Play-Back Rate** — What percentage of their credits do they keep playing vs cashing out?
- **20% Cash-Out Behavior** — How often and how quickly do they cash out?
- **15% Coin-In Ratio** — How much do they feed back in relative to their losses?
- **10% Session Extension** — Do they keep playing when their credits get low?
- **10% Visit Frequency** — How often do they come back?
- **10% POC Response** — When you give them bonus credits, do they use them?
- **10% Recency** — How recently did they last play?

**What the segments mean:**
- **Elite Churner (80-100)** — Your BEST players. They play back almost everything. Invest heavily in these players.
- **High Value (65-79)** — Very good players. Worth significant POC investment.
- **Mid Value (50-64)** — Solid players with room to grow. Moderate POC.
- **Developing (35-49)** — Players who could become more valuable with the right incentives.
- **Casual (20-34)** — Occasional players. Small POC to encourage more visits.
- **Low Value (0-19)** — New or infrequent players. Welcome bonuses only.

**What the tiers mean:**
Tiers determine the POC multiplier — higher tier players get more bonus per dollar:
- **Bronze** — 1.0x (base rate)
- **Silver** — 1.15x (15% more POC)
- **Gold** — 1.3x (30% more)
- **Platinum** — 1.5x (50% more)
- **Diamond** — 2.0x (double POC!)

Example: If a rule awards $10 POC, a Diamond player actually gets $20."""},

        {"id": "pirs-managing-rules", "title": "Creating & Editing Bonus Rules", "content": """**Bonus rules are the heart of PIRS — they decide who gets rewarded, when, and how much.**

**To see your rules:**
Go to PIRS Rewards > **Bonus Rules** tab

**To create a new rule:**
1. Click the yellow **"+ Create Rule"** button at the top right
2. Fill in the form:
   - **Rule Name** — Something descriptive like "Weekend High Roller Bonus"
   - **Trigger** — When should this rule fire? Options:
     - **card_in** — When the player inserts their loyalty card
     - **coin_in_milestone** — When they've put in a certain dollar amount
     - **session_duration** — When they've been playing for a certain number of minutes
     - **post_win_playback** — When they keep playing after winning instead of cashing out
     - **lapse_risk** — When the AI predicts they might stop coming
     - **return_visit** — When they come back after being away
     - **churn_threshold** — When their score reaches a certain level
   - **POC Amount ($)** — How much bonus to give (e.g., $10, $25, $50)
   - **Min Churn Score** — Only give this bonus to players with at least this score
   - **Max Per Day** — How many times can one player get this bonus per day
   - **Cooldown (min)** — Minimum minutes between awards of this rule for the same player
   - **Time Window** — When is this rule active: always, weekdays only, weekends only, or happy hour only
   - **Message Template** — The message shown on the EGM screen. Use {amount} and it will be replaced with the actual dollar value
3. Click **"Create Rule"**

**To edit an existing rule:**
1. Find the rule in the list
2. Click the **blue pencil icon** on the right
3. The rule expands into an edit form — change anything you want
4. Click **"Save Changes"** when done, or **"Cancel"** to discard

**To turn a rule on or off:**
Click the **green toggle switch** on the left side of any rule. Green = active, gray = off.

**To delete a custom rule:**
1. Click the **red trash icon** (only appears on rules you created)
2. A red confirmation bar appears: "Are you sure you want to delete this? This cannot be undone."
3. Click **"Yes, Delete"** to confirm, or **"Cancel"** to keep it

**Important:** You cannot delete the built-in system rules — only toggle them off.

**To run all rules immediately:**
Click the green **"Run Engine Now"** button at the top. This evaluates every active rule against every player and awards POC where conditions are met."""},

        {"id": "pirs-rtp-compensation", "title": "RTP Compensation — Helping Unlucky Players", "content": """**Sometimes players have really bad luck. PIRS helps you identify and compensate them.**

**What is RTP?**
RTP = Return To Player. If a player puts in $1,000 and wins back $800, their RTP is 80%. Most EGMs are designed to return 88-96% over time, but in the short term, some players get much less.

**Why compensate?**
A player who puts in $1,000 and only gets back $500 (50% RTP) is having a terrible experience. If you don't do something, they'll stop coming. A small $20-$50 bonus can keep that player loyal and they'll eventually return to normal play — worth thousands in future revenue.

**How to find unlucky players:**
1. Go to PIRS Rewards > **RTP Compensation** tab
2. Click the blue **"Scan Players"** button
3. UGG scans every player's history and shows anyone below 70% RTP

**What you'll see for each flagged player:**
- Their actual RTP percentage (shown in large text — red if very low, amber if borderline)
- Total wagered and total won
- Dollar deficit (how much below 70% they are)
- Their churn score and tier
- Whether they already have pending compensation

**Two ways to compensate:**

**Option 1: Auto Compensate (recommended)**
Click the yellow **"Auto Compensate"** button next to the player. The system automatically:
- Calculates 10% of their RTP deficit as POC
- Caps it at $5 minimum, $100 maximum
- Credits it to their player wallet
- When they next card in at any EGM, the POC loads automatically
- A message appears on screen: "We appreciate your loyalty! You have $XX in bonus credits waiting!"

**Option 2: Manual amount**
Click **"Send $25 POC"** (or go to Player Intelligence tab and use the quick POC buttons) to send a specific amount you choose.

**The POC goes to their WALLET, not a specific machine.** This means:
- You can send it anytime — the player doesn't need to be at a machine
- It waits until they next card in
- When they card in at ANY machine, all pending POC loads automatically
- They see the welcome message on screen
- The POC is Play Only — they can play with it but can't cash it out directly"""},

        {"id": "pirs-settings", "title": "Configuring PIRS Settings", "content": """**The Settings tab lets you control everything about how PIRS operates.**

Go to PIRS Rewards > **Settings** tab

**Budget Controls (IMPORTANT — set these first!)**
These prevent the system from spending more than you want:
- **Daily Budget ($)** — Maximum total POC the engine can award in one day. Default: $500. If you have 100 EGMs, maybe set this to $200-$500 depending on your profit margins.
- **Weekly Budget ($)** — Weekly cap. Default: $2,500
- **Monthly Budget ($)** — Monthly cap. Default: $10,000
- **Per Player Daily ($)** — No single player can receive more than this per day. Default: $50. Prevents one player from getting too much.
- **Per Player Session ($)** — Cap per playing session. Default: $25
- **Max POC Amount ($)** — Largest single award the system can give. Default: $100

**Time-Based Multipliers (drive traffic when you need it)**
- **Happy Hour:** Check the box to enable, then set start time, end time, and multiplier. Example: 4:00 PM to 6:00 PM with 1.5x multiplier = all POC awards are 50% bigger during that window
- **Weekend Multiplier:** Set a number like 1.25 to give 25% more POC on Saturday and Sunday. Set 1.0 for no weekend boost.

**Engine Controls**
- **Auto-run reward rules:** When ON, the system automatically evaluates rules and awards POC without you clicking anything. When OFF, you must click "Run Engine Now" manually.
- **Auto-scale rewards:** When ON, the system recalculates every player's churn score on each engine run. Turn this on — it keeps scores accurate as players' behavior changes.
- **New Player Welcome POC ($):** Bonus amount for first-time loyalty card users. Default: $10
- **Min POC Amount ($):** Smallest award the system will give. Default: $5. Awards calculated below this are rounded up.

**After changing settings:**
Click the yellow **"Save All Configuration Changes"** button at the bottom. Changes take effect immediately on the next engine run.

**Recommended starting configuration for a new route:**
- Daily Budget: $200 (conservative — increase as you see ROI)
- Per Player Daily: $30
- Happy Hour: Enable, 4-6 PM, 1.5x
- Weekend Multiplier: 1.25
- Auto-run: ON
- Auto-scale: ON
- New Player Welcome: $10

Monitor your Business Impact tab for a week. If ROI is above 8:1, consider increasing budgets."""},

        {"id": "pirs-sending-poc", "title": "Sending POC to Players", "content": """**There are 4 ways to send POC to players:**

**Way 1: Automatic (engine runs rules)**
The PIRS engine evaluates all your active rules against all players. When a player meets a rule's conditions, they get POC automatically. This happens every time the engine runs (automatic or manual).

**Way 2: Quick Send from Player Profile**
1. Go to PIRS > Player Intelligence tab
2. Click a player in the leaderboard
3. In the detail panel, click one of the dollar buttons ($5, $10, $15, $25, $50)
4. Click **"Send $X POC"**
5. POC is awarded immediately (if they're at a machine) or goes to their wallet

**Way 3: RTP Compensation**
1. Go to PIRS > RTP Compensation tab
2. Click "Scan Players"
3. Click "Auto Compensate" or "Send $25 POC" for any flagged player
4. POC goes to their wallet — loads on next card-in

**Way 4: Wallet Credit (send anytime, player doesn't need to be playing)**
Use this when you want to reward a player who isn't currently at a machine — maybe they called to complain, or you want to bring back someone who hasn't visited in a while.
The POC sits in their wallet and auto-delivers when they next card in.

**What happens when POC is delivered to an EGM:**
1. A golden message appears on the machine screen: "Welcome back! $XX in bonus credits loaded!"
2. The credits are added to the machine as non-cashable credits
3. The player can use them to play but cannot cash them out
4. If they win using POC credits, the winnings ARE cashable
5. UGG tracks the delivery in the POC History"""},

        {"id": "pirs-monitoring-roi", "title": "Monitoring Your Investment", "content": """**The Business Impact tab tells you if PIRS is making you money.**

Go to PIRS Rewards > **Business Impact** tab

**The Big Number: ROI**
This shows your return on investment as a ratio. For example:
- **12.6:1** means for every $1 of POC you gave away, players generated $12.60 in additional play
- **Target: 10:1** — anything above this is excellent
- Below 5:1 — you might be giving POC to the wrong players. Check your rule conditions.

**The breakdown shows:**
- **Total POC Invested** — How much bonus money you've given out
- **Coin-In Generated** — How much additional play that POC created
- **Awards Count** — Number of individual POC awards
- **Net Return per $1 POC** — The dollar return on each dollar invested

**How to improve your ROI:**
1. **Focus on high-churn players:** Set rule conditions to require Churn Score 60+ for most bonuses
2. **Use time multipliers wisely:** Happy Hour drives traffic to slow periods
3. **Watch the lapse risk:** Players about to leave are the most cost-effective to retain
4. **Don't over-reward casuals:** Low-score players rarely generate enough play to justify large POC
5. **Check individual player ROI:** In the Player Intelligence tab, each player shows their lifetime POC ROI. If a player's ROI is below 3:1, reduce their POC.

**Check Business Impact at least weekly.** If ROI drops below 5:1, review your rules and tighten the churn score thresholds."""},

        {"id": "pirs-best-practices", "title": "PIRS Best Practices", "content": """**Follow these guidelines to get the most out of PIRS:**

**1. Start conservative, then increase**
Begin with a $200 daily budget and $10-$15 POC awards. Watch the ROI for 2 weeks. If it's above 8:1, gradually increase budgets and award amounts.

**2. Your top 20% of players generate 80% of revenue**
Focus your POC investment on Elite and High Value churners (score 65+). These players play back most of what they receive.

**3. Lapse prevention is the highest-ROI activity**
A $15 bonus to a player who's about to stop coming is worth more than a $50 bonus to someone who's going to play anyway. Enable the LAPSE_PREVENTION rule and set it to trigger at 70+ lapse risk.

**4. Happy Hour drives traffic**
Enable the Happy Hour multiplier during your slowest hours. If your venues are quiet from 2-5 PM, set that as happy hour with 1.5x POC. Players will come during those hours to get better bonuses.

**5. Compensate unlucky players FAST**
Check the RTP Compensation tab weekly. Players below 60% RTP are at extreme risk of never returning. A quick $20-$30 POC can save a customer worth $5,000+ per year.

**6. Don't reward cash-out behavior**
If a player's cash-out rate is above 80%, they're taking money out, not playing it back. PIRS already accounts for this — high cash-out players get low churn scores and less POC.

**7. Monitor your engine status daily**
The engine status bar at the bottom of the Bonus Rules tab shows:
- How much budget you've spent today
- How much is remaining
- How many awards were given
If you see "Budget Remaining: $0" early in the day, consider increasing your daily budget.

**8. Create weekend-specific rules**
Player behavior changes on weekends. Create rules with "weekends" time window that offer slightly higher POC to capture weekend traffic.

**9. Review and adjust monthly**
Every month, look at Business Impact and ask: Which rules generated the highest ROI? Which player segments are growing? Should I adjust tier thresholds or POC amounts?

**10. Trust the AI but verify**
PIRS's churn scoring is powerful but it's based on historical behavior. Occasionally check the Player Intelligence tab and verify that top-scored players match your real-world experience. If the AI is rating a player highly that you know is actually low-value, check their play-back rate data."""},
    ]},

    {"id": "pin-player-tracking", "title": "PIN Player Tracking", "icon": "IdentificationCard", "docs": [
        {"id": "pin-overview", "title": "What is PIN Player Tracking?", "content": """**UGG does not use physical player cards.** Instead, players log in at the machine using a **PIN number** (4 to 8 digits) tied to an account in our system.

**Why PINs instead of cards?**
- No plastic cards to print, lose, damage, or replace
- Players can't forget their card at home — their PIN is in their head
- No magnetic stripe or chip to wear out
- No card reader hardware to install or maintain
- Faster enrollment — you can set up a player in under a minute

**How it works at a high level:**
1. An operator creates a player account in UGG and sets a 4–8 digit PIN
2. Player walks up to any EGM on the route
3. Player enters their PIN on the machine
4. UGG recognizes the player and starts tracking their play
5. When the player is done, they log out at the machine (or walk away and auto-logout happens)

**What UGG tracks about each player:**
- How much money they put in (bills and tickets)
- How much they cashed out
- How many games they played
- Which machines they played on and for how long
- Whether their behavior looks suspicious (more on that below)

**Important:** UGG tracks TWO different kinds of "sessions" and you need to understand the difference — it affects what reports mean."""},

        {"id": "pin-two-layers", "title": "The Two Kinds of Sessions", "content": """UGG tracks two kinds of sessions at the same time. They overlap, but they are NOT the same thing.

**1. Credit Session — The Money**
A credit session is about the MONEY on a machine, not about who is playing.
- **Starts** when someone drops a bill (or redeems a ticket) into a machine that had **zero credits** on it
- **Ends** when the credits on the machine go back to zero — by any means (played down, cashed out, ticket printed, credits transferred away)
- A credit session can be **anonymous** — if no PIN is entered, the session still gets tracked, just without a player's name attached

**2. PIN Session — The Player**
A PIN session is about WHICH PLAYER is at a machine.
- **Starts** when a player enters their PIN at the machine
- **Ends** when the player logs out OR when the credit session on that machine ends (whichever comes first)
- Always tied to a specific player account

**Why two different sessions?**
Because players do weird things. Here are real scenarios:
- Player A logs in, plays, logs out while still having $30 in credits, walks away. Player B comes along 2 minutes later, logs in with their own PIN, and plays down those $30 before cashing out. → Same credit session. Two PIN sessions.
- Someone drops $20 into a machine without logging in (anonymous), then decides to log in with their PIN mid-session. → One credit session. One PIN session, but it only counts play from when they logged in.
- Player drops a bill at zero credits, plays, cashes out to $0 balance, then drops another bill 30 seconds later. → Two credit sessions (because balance hit zero between them).

**How to think about it:**
- Use **Credit Sessions** for money reconciliation — how much came in, how much went out, what the machine did financially
- Use **PIN Sessions** for player behavior — who was playing, how long, how much they played"""},

        {"id": "pin-create-player", "title": "How to Create a PIN Player", "content": """**To add a new player to the system:**

1. Click **PIN Players** in the left sidebar
2. Click the green **New Player** button in the top right
3. Fill in the form:
   - **Name** (required) — The player's full name
   - **PIN** (required) — A number between 4 and 8 digits. Tell them to pick something they'll remember but isn't obvious (not 1234, not their birthday year)
   - **Account Ref** (optional) — A customer ID from your own system, if you use one
   - **Email** (optional) — For future marketing or alerts
   - **Phone** (optional) — For future SMS rewards
4. Click **Create**

**That's it.** The player can now walk up to any EGM on your route and log in with their PIN.

**Important security notes:**
- Once you save a PIN, UGG stores it encrypted — even YOU as an operator cannot see it later
- If a player forgets their PIN, you cannot look it up. You have to **Change PIN** to a new one
- Never write PINs down or email them
- If you suspect a PIN has been compromised, change it immediately

**Changing a player's PIN:**
1. Go to **PIN Players**
2. Find the player in the list (use the search box if you have many)
3. Click the **key icon** next to their name
4. Enter the new 4–8 digit PIN
5. Click **Update PIN**
6. Tell the player their new PIN in person — never by email or text

**Deactivating a player:**
Click the red **trash icon** next to a player's name. This sets them to "inactive" — their PIN stops working, but their history is kept. You can reactivate them later if needed."""},

        {"id": "pin-viewing-sessions", "title": "Viewing Active and Historical Sessions", "content": """**To see who is currently playing on your route:**

1. Click **PIN Sessions** in the left sidebar
2. You'll see a dashboard with summary cards at the top:
   - **Active Credit** — How many machines currently have money in them
   - **Active PIN** — How many players are currently logged in
   - **Total Credit** / **Total PIN** — Lifetime counts
   - **Open Anomalies** — Flagged suspicious behavior (red if any)
3. Below the cards, there are two tabs:
   - **Active Now** — Real-time view of what's happening RIGHT NOW (refreshes every 5 seconds automatically)
   - **Recent History** — The last 100 credit and PIN sessions

**The two columns:**
- **Left column (Credit Sessions)** — Each card shows a machine with money in it, what was put in, what came out, and how many games were played
- **Right column (PIN Sessions)** — Each card shows a player, which machine they're on, and their running stats

**Clicking for details:**
Click any Credit Session card to open a **detail panel** showing:
- Full session timeline (when it started, when it ended, how)
- Total money in vs. out
- Coin in, coin out, games played, net win/loss
- **All PIN Sessions that happened during this credit session** — so you can see if multiple players shared one session

**Finding a specific player's activity:**
Currently you view sessions from this main page. To look up a specific player's history, you'd use the API (your administrator can help). A dedicated "player profile" view is on the roadmap."""},

        {"id": "pin-anomalies", "title": "Session Anomalies — Spotting Suspicious Play", "content": """**UGG automatically watches for players trying to game the system.** When it sees something suspicious, it raises an **anomaly** that you can review.

**To see anomalies:**
Click **Session Anomalies** in the left sidebar.

**The five things UGG watches for:**

**1. MICRO SESSION (Low Severity)**
- A session that ended in under 60 seconds with 0 or 1 game played
- Usually harmless — a player changed their mind or made a mistake
- Worth looking at if you see many from the same player

**2. LOW PLAY FLIP (High Severity) — ⚠️ This is the big one**
- A player dropped $50 or more, played 3 or fewer games, then cashed out 90%+ of what they put in
- **This is the classic "money movement" pattern** — someone using the machine as an ATM, possibly to launder cash or move funds between accounts
- Always investigate these. Check who the player is and see if they have other flags

**3. RAPID CYCLING (High Severity)**
- Same player started 4 or more credit sessions on the same machine within 30 minutes
- Can indicate bonus farming, promotion abuse, or unusual behavior
- Legitimate players don't usually start and stop this many times on one machine

**4. DEVICE HOPPING (High Severity)**
- Same player active on 3 or more different machines within 60 minutes
- May indicate someone jumping between machines looking for loose ones (not illegal, but unusual) OR a stolen/shared PIN (someone gave their PIN to a friend)
- Investigate the pattern — are they trying to qualify for multiple promotions at once?

**5. PIN CHURN (Medium Severity)**
- A player logged out 5+ times in an hour while still having credits on the machine
- Could mean the PIN is being shared across people at the same machine, or the player is indecisive
- Lower priority but worth watching

**What to do with an anomaly:**
Each anomaly has two buttons on the right side:
- **Acknowledge (green checkmark)** — "I've seen this and I'm looking into it"
- **Dismiss (gray X)** — "This is a false positive, ignore it"

**Filtering:**
Use the dropdowns at the top of the page to filter by:
- Status (Open, Acknowledged, Dismissed, or All)
- Severity (High, Medium, Low)

By default you see all **Open** anomalies — the ones that still need attention.

**Best practice:**
- Review **High severity** anomalies every day at minimum
- If you see the same player triggering multiple rules, that's a red flag — consider deactivating their PIN until you can talk to them
- Dismiss false positives so your list stays clean and manageable"""},

        {"id": "pin-one-pin-one-egm", "title": "One PIN, One Machine (at a Time)", "content": """**UGG enforces a rule: a PIN can only be logged in at ONE machine at a time.**

This prevents PIN sharing abuse where a player gives their PIN to a friend and they both try to earn rewards on different machines simultaneously.

**How it works:**
- If Player A is logged in at Machine 1
- And then someone tries to log in with Player A's PIN at Machine 2
- UGG accepts the new login at Machine 2 and **automatically logs out Player A from Machine 1**

This is called **"last wins"** — whichever machine saw the most recent login is the one that counts.

**What operators will see:**
- The PIN Session for Machine 1 will end with reason `forced_logout_other_device`
- A new PIN Session opens at Machine 2
- If this happens repeatedly for the same player, the **DEVICE HOPPING** anomaly rule will fire (see Session Anomalies article)

**Why this matters:**
- If you see a lot of `forced_logout_other_device` end reasons in the session history, it might indicate PIN sharing
- Legitimate players rarely trigger this — they finish at one machine before going to another
- Pair this with the DEVICE HOPPING anomaly to catch organized PIN abuse

**Machine also only hosts one PIN:**
The reverse is also true — a machine can only have one PIN logged in at a time. If Player B tries to log in at a machine where Player A is already active, Player A gets logged out and Player B takes over. Player A's PIN session ends with reason `forced_logout_pin_swap`. The credit session on the machine continues — whoever is logged in gets tracked against that session."""},

        {"id": "pin-best-practices", "title": "Best Practices for Route Operators", "content": """**Daily routine (5 minutes):**
1. Open **Session Anomalies** page — check for any new HIGH severity flags
2. Open **PIN Sessions** → Active Now tab — see who's playing right now, spot anything unusual
3. If anything looks off, click through to the detail view and investigate

**Weekly routine (15 minutes):**
1. Review all anomalies from the past 7 days — look for repeat offenders (same player ID showing up in multiple flags)
2. Check your **PIN Players** list — any players you haven't seen in weeks who should be deactivated?
3. Spot-check a few random credit sessions in the history view — do the numbers look right? Total in, total out, games played?

**Setting up a new venue on the route:**
1. Create PIN player accounts for any existing loyalty members BEFORE you install the machines
2. Give them a printed card with just their name and a note saying "Your PIN is on file with management — ask if you forgot it" — NEVER print the actual PIN
3. Train venue staff to verify player identity before any PIN reset request

**Handling a lost/forgotten PIN:**
1. Verify the player's identity in person (ID required)
2. Use the **key icon** next to their name in PIN Players to set a new PIN
3. Tell them the new PIN verbally in person
4. Write a note in their account (notes field) with the date of the reset

**Signs of PIN abuse to watch for:**
- Same player showing up in multiple anomalies in the same week
- Lots of `forced_logout_other_device` endings
- DEVICE HOPPING flags firing often for the same person
- LOW PLAY FLIP with round numbers (e.g., $100 in, $99 out, 1 game played)
- PINs that are very simple (1111, 1234, birthday years) — encourage players to pick better ones

**What to tell your players:**
- "Your PIN is like your bank PIN — don't share it with anyone, not even family"
- "If you forget your PIN, come see us in person with ID"
- "If you think someone knows your PIN, tell us immediately so we can change it"
- "You can only be logged in on one machine at a time — if you walk to another machine, log out first"

**If the worst happens (PIN compromise):**
1. Deactivate the player's account immediately (trash icon)
2. Check their session history for the last 24 hours — what did the attacker do?
3. Look at anomalies filed against that player
4. Create a new account with a new PIN when you've verified the real player's identity
5. Document the incident in the notes field of the new account"""},
    ]},
]


@router.get("")
async def list_doc_sections():
    return {"sections": [{"id": s["id"], "title": s["title"], "icon": s["icon"], "doc_count": len(s["docs"])} for s in DOC_SECTIONS]}

@router.get("/section/{section_id}")
async def get_doc_section(section_id: str):
    section = next((s for s in DOC_SECTIONS if s["id"] == section_id), None)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return section

@router.get("/article/{doc_id}")
async def get_doc_article(doc_id: str):
    for s in DOC_SECTIONS:
        for d in s["docs"]:
            if d["id"] == doc_id:
                return {**d, "section_id": s["id"], "section_title": s["title"]}
    raise HTTPException(status_code=404, detail="Article not found")

@router.get("/search")
async def search_docs(q: str = ""):
    if not q:
        return {"results": [], "total": 0}
    ql = q.lower()
    results = []
    for s in DOC_SECTIONS:
        for d in s["docs"]:
            if ql in d["title"].lower() or ql in d["content"].lower():
                results.append({"id": d["id"], "title": d["title"], "section": s["title"], "snippet": d["content"][:200]})
    return {"results": results, "total": len(results), "query": q}
