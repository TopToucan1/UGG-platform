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
UGG connects all your gaming machines (slot machines, video poker, etc.) to one central system. Instead of visiting each machine or each location, you can see everything from your computer or tablet.

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

- **EGM** — Electronic Gaming Machine (slot machine, video poker, etc.)
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
