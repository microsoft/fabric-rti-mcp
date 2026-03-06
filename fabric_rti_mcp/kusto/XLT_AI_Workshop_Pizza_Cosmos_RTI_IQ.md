# 🍕 XLT AI Workshop: Build a Real-Time Pizza Empire

## Mission: Build a Real-Time Operations Intelligence System in 2 Hours

You are the CTO of **Pizza Cosmos** — a fast-growing pizza delivery chain with 50 locations. Orders are flying in, drivers are on the road, kitchens are at capacity, and customers are watching their delivery timers tick. Your job: build a **real-time monitoring and intelligence system** that keeps the empire running.

This maps directly to what RTI + IQ does for our customers at enterprise scale.

| Pizza Cosmos Concept | RTI + IQ Equivalent |
|---|---|
| Order stream | Real-Time Event Stream (EventStream) |
| Kitchen & driver metrics | Real-Time Dashboard (RTA) |
| "Driver is late" alert | Anomaly Detection / Activator |
| "Reroute to nearest driver" | Operational Agent / IQ Action |
| Order-Driver-Kitchen relationships | Ontology / Semantic Graph |
| Business rules & SLAs | IQ Intelligence Layer |

---

## How This Workshop Works

You will use **GitHub Copilot** as your coding agent to build this system step by step. You are not expected to know how to code. You are expected to learn how to **direct an AI agent** to code for you.

### The Rules

1. **You do NOT write code yourself.** You write prompts. Copilot writes code.
2. **You break the work into tasks.** Just like you'd assign work to an engineer.
3. **You review the output.** Just like you'd review a design doc or PR.
4. **You iterate.** If it's wrong, you tell Copilot what to fix.

### What You'll Learn

- How a PRD translates into working code through AI
- How to decompose a system into agent-friendly tasks
- How to prompt effectively (clear intent, constraints, examples)
- How fast a working system can come together with AI
- Why this changes everything about how we plan, staff, and invest

---

## PHASE 0: Setup (10 minutes)

### Prerequisites (complete before the workshop)

- [ ] VS Code installed with GitHub Copilot extension
- [ ] GitHub Copilot Chat enabled
- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed (for the dashboard)
- [ ] Run `pip install fastapi uvicorn websockets pydantic` in your terminal
- [ ] Run `npm install -g create-react-app` in your terminal

### Your First Copilot Interaction

Open VS Code. Open Copilot Chat. Type:

```
Hey Copilot, I'm building a real-time pizza delivery monitoring system.
I'll be giving you tasks one at a time. For each task, generate clean,
working Python code. Ask me if anything is unclear. Let's go.
```

You've just onboarded your AI engineer. That took 10 seconds.

---

## PHASE 1: The PRD (15 minutes)

Before we code, we define what we're building. This is the most important step. **A clear PRD is the difference between great AI output and garbage.**

### Task 1.1: Read the PRD

Below is your Product Requirements Document. Read it. Understand it. This is what Copilot will build for you.

---

### 📋 PRD: Pizza Cosmos Real-Time Operations Intelligence

**Product Name:** Pizza Cosmos RTI Dashboard

**Problem Statement:**
Pizza Cosmos operates 50 locations with 200+ active drivers. Today, operations managers monitor orders through spreadsheets and phone calls. Average response time to a late delivery is 12 minutes. Customer complaints about cold pizza are up 30% QoQ. We have no real-time visibility into kitchen throughput, driver location, or SLA compliance.

**Solution:**
A real-time operations intelligence system that:
1. Ingests live event streams (orders, driver GPS, kitchen status)
2. Displays a real-time operational dashboard
3. Detects anomalies (late drivers, kitchen bottlenecks, SLA breaches)
4. Recommends and triggers automated actions (reroute driver, alert manager, comp customer)

**Core Entities (Ontology):**

| Entity | Key Attributes |
|---|---|
| Order | order_id, customer, items, status, timestamp, estimated_delivery, actual_delivery |
| Driver | driver_id, name, location (lat/lng), status (available/delivering/returning), current_order |
| Kitchen | kitchen_id, location_name, orders_in_queue, avg_prep_time_min, capacity, status |
| Customer | customer_id, name, address, satisfaction_score, lifetime_orders |
| Alert | alert_id, type, severity, entity_id, message, recommended_action, auto_resolved |

**Real-Time Streams:**

| Stream | Frequency | Source |
|---|---|---|
| order_events | Per order (~200/hr across chain) | POS System |
| driver_location | Every 10 seconds per driver | GPS Tracker |
| kitchen_status | Every 30 seconds per kitchen | IoT Sensors |
| delivery_completed | Per delivery | Driver App |

**Intelligence Rules (IQ Layer):**

| Rule | Trigger | Action |
|---|---|---|
| Late Delivery Risk | estimated_delivery - now < 5 min AND driver > 2km away | Alert: "Delivery at risk" + recommend reroute |
| Kitchen Overload | queue > 80% capacity for > 10 min | Alert: "Kitchen bottleneck" + pause new orders |
| Cold Pizza Risk | prep_complete > 8 min ago AND not picked up | Alert: "Remake order" |
| VIP Customer Delay | customer.lifetime_orders > 50 AND delivery late | Auto-comp: free item on next order |
| Driver Idle | driver.status = available for > 15 min | Suggest: reposition to high-demand zone |

**Success Metrics:**
- Mean time to detect anomaly: < 30 seconds
- Mean time to recommend action: < 5 seconds
- Dashboard refresh rate: < 2 seconds
- SLA compliance visibility: 100% of active orders

---

### Task 1.2: Ask Copilot to Summarize the Architecture

Copy the PRD above into Copilot Chat and prompt:

```
Based on this PRD, propose a simple system architecture I can build in
under 2 hours using Python (FastAPI + WebSockets for backend) and a
simple HTML/JS dashboard for frontend. Keep it local, no cloud
services needed. Give me the file structure and a brief description
of each component.
```

**Review the output.** Does it make sense? Would you approve this design doc? If not, tell Copilot what to change.

---

## PHASE 2: Build the Event Simulator (20 minutes)

Real customers aren't ordering pizza during our workshop. So we'll build a simulator that generates realistic real-time events.

### Task 2.1: Order Event Generator

Prompt Copilot:

```
Create a Python module called event_simulator.py that generates
realistic pizza order events. Each order should have: order_id (UUID),
customer_name (random from a list of 20 names), items (1-4 random
pizzas from a menu of 10 types), kitchen_id (random from 5 kitchens),
timestamp, estimated_delivery (15-45 min from now), and status
("placed"). Generate a new order every 3-8 seconds randomly.
The function should yield events as a generator.
```

### Task 2.2: Driver Location Simulator

```
Add to event_simulator.py a driver location simulator. Create 10
drivers with names. Each driver has a status (available, delivering,
returning) and a lat/lng position that updates every 2 seconds.
Delivering drivers should move toward a random delivery address.
Available drivers should slowly drift. Return the updates as a
generator that yields driver_id, lat, lng, status, current_order_id.
```

### Task 2.3: Kitchen Status Simulator

```
Add to event_simulator.py a kitchen status simulator for 5 kitchens.
Each kitchen has a name (NYC Downtown, Brooklyn Heights, Queens Central,
Midtown East, Upper West Side), a queue size (0-20 orders), average
prep time (8-20 min), capacity (20 orders), and status (normal,
busy, overloaded). Queue sizes should fluctuate realistically every
5 seconds. When queue > 80% capacity, status = overloaded.
Yield updates as a generator.
```

**Checkpoint:** Run each generator independently. Are the events realistic? Do they look like real operational data? If not, tell Copilot what to fix.

---

## PHASE 3: Build the Real-Time Backend (25 minutes)

Now we connect the events to a backend that clients can subscribe to. This is the RTI layer.

### Task 3.1: WebSocket Server

```
Create a FastAPI application in server.py that:
1. Runs all three event simulators concurrently using asyncio
2. Maintains a WebSocket endpoint at /ws that streams all events
   to connected clients in real-time
3. Categorizes each event by type: "order", "driver", "kitchen"
4. Sends events as JSON with a "type" field and "data" field
5. Maintains an in-memory state of all current orders, drivers,
   and kitchens that updates as events come in
6. Exposes a REST endpoint GET /state that returns current state
```

### Task 3.2: The Intelligence Layer (IQ)

This is the brain. Prompt Copilot:

```
Create a module called intelligence.py that implements the IQ layer.
It should:
1. Accept the current system state (all orders, drivers, kitchens)
2. Evaluate these rules every 5 seconds:
   - Late Delivery Risk: estimated_delivery - now < 5 min AND
     driver distance > 2km from destination
   - Kitchen Overload: queue > 80% capacity for > 2 consecutive checks
   - Cold Pizza Risk: order status = "ready" for > 8 min and not picked up
   - VIP Customer Delay: customer lifetime_orders > 50 AND delivery is late
   - Driver Idle: driver status = available for > 3 consecutive checks
3. Generate alerts with: alert_id, type, severity (low/medium/high/critical),
   affected entity, message, and recommended_action
4. Send alerts through the same WebSocket as type: "alert"
```

**Checkpoint:** Start the server. Connect via WebSocket (Copilot can generate a quick test client). Are events flowing? Are alerts triggering? This is your RTI + IQ system running locally.

---

## PHASE 4: Build the Dashboard (30 minutes)

Time to make it visual. This is where it gets fun.

### Task 4.1: Real-Time Dashboard

```
Create a single HTML file called dashboard.html with embedded CSS and
JavaScript that:
1. Connects to the WebSocket at ws://localhost:8000/ws
2. Shows three panels side by side:
   - LEFT: Live Order Feed (scrolling list of new orders with status
     color coding: green=on-time, yellow=at-risk, red=late)
   - CENTER: Kitchen Status (5 cards, one per kitchen, showing queue
     size as a progress bar, avg prep time, and status with color
     coding: green=normal, orange=busy, red=overloaded)
   - RIGHT: Active Alerts (scrolling list with severity color coding
     and recommended actions)
3. Top bar showing: total active orders, total active drivers,
   average delivery time, SLA compliance percentage
4. Make it look modern and clean. Dark theme. Use CSS grid.
   No external frameworks needed.
5. Add a subtle animation when new alerts appear (pulse effect)
```

### Task 4.2: Driver Map

```
Add to the dashboard a section below the three panels that shows a
simple map visualization of driver positions. Use an HTML5 canvas
element. Plot the 5 kitchen locations as blue squares and the 10
driver positions as colored dots (green=available, orange=delivering,
grey=returning). Update positions in real-time as driver events come in.
Add a simple grid background to make it look like a map.
```

### Task 4.3: Alert Actions

```
Add to each alert in the dashboard a button that says the recommended
action (e.g., "Reroute Driver", "Pause Kitchen Orders", "Comp Customer").
When clicked, send a POST request to /action with the alert_id and
action type. In the server, create the /action endpoint that logs the
action and marks the alert as resolved. The alert should visually
change to show "Resolved" with a checkmark.
```

**Checkpoint:** Open dashboard.html in your browser while the server runs. You should see a live, updating, operational intelligence dashboard. Orders flowing. Kitchens pulsing. Alerts firing. Actions available.

**This is RTI + IQ. You just built it.**

---

## PHASE 5: The "Wow" Moment (15 minutes)

Let's add the thing that makes jaws drop.

### Task 5.1: Natural Language Ops Query

```
Add to the dashboard a text input at the top with placeholder
"Ask your operations AI anything..." and a Send button.
When the user types a question like "Which kitchen has the longest
wait time?" or "How many deliveries are at risk right now?" or
"What should I do about the Brooklyn bottleneck?", send the
question along with the current system state to a new endpoint
POST /ask. On the backend, use a simple rule-based response system
that parses the question for keywords (kitchen, driver, delivery,
risk, bottleneck, etc.) and returns a natural language answer
based on actual current state data. Display the answer below
the input field with a typing animation.
```

**This is the IQ agent experience.** A natural language interface on top of real-time operational data. This is what we're building for customers.

---

## PHASE 6: Reflect (5 minutes before group discussion)

Before we come together as a group, write down your answers:

1. **What surprised you?** About the speed? The quality? The process?

2. **What would have taken a team of engineers to build this?** How many people? How many sprints?

3. **Where did Copilot struggle?** What required the most iteration?

4. **How does this change how you think about:**
   - Sprint planning?
   - Headcount investment?
   - PM-Engineering collaboration?
   - What's possible in a hackathon vs. a semester plan?

5. **If every engineer on your team could build at this speed, what would you prioritize differently?**

---

## Quick Reference: Prompting Tips

| Do This | Not This |
|---|---|
| "Create a function that takes X and returns Y" | "Make something that handles orders" |
| "Use FastAPI with WebSocket support" | "Build a server" |
| "Each order has these fields: ..." | "Orders should have the usual stuff" |
| "When queue > 80%, set status to overloaded" | "Handle the overload case" |
| "Fix the bug: drivers don't update position" | "It's broken" |

**The golden rule:** Prompt Copilot like you'd write a design spec for a senior engineer. Clear inputs, clear outputs, clear constraints.

---

## Architecture Reference

```
┌─────────────────────────────────────────────────┐
│                  Dashboard (HTML/JS)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │  Orders   │ │ Kitchens │ │     Alerts       │ │
│  │  Feed     │ │ Status   │ │  + Actions       │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────────────────────────────────────────┐│
│  │            Driver Map (Canvas)                ││
│  └──────────────────────────────────────────────┘│
│  ┌──────────────────────────────────────────────┐│
│  │         "Ask your Ops AI" Input              ││
│  └──────────────────────────────────────────────┘│
└───────────────────────┬─────────────────────────┘
                        │ WebSocket + REST
┌───────────────────────┴─────────────────────────┐
│              FastAPI Server (Python)              │
│  ┌──────────────┐  ┌───────────────────────────┐│
│  │ Event         │  │   Intelligence Layer (IQ) ││
│  │ Simulator     │  │   - Rules Engine          ││
│  │ - Orders      │  │   - Alert Generator       ││
│  │ - Drivers     │  │   - Action Handler        ││
│  │ - Kitchens    │  │   - NL Query Engine       ││
│  └──────────────┘  └───────────────────────────┘│
│  ┌──────────────────────────────────────────────┐│
│  │         In-Memory State Store                 ││
│  └──────────────────────────────────────────────┘│
└──────────────────────────────────────────────────┘
```

---

## Bonus Challenge (if you finish early)

Add a "Chaos Mode" button to the dashboard that:
- Suddenly overloads 3 kitchens simultaneously
- Makes 5 drivers go "offline"
- Doubles the order rate

Watch how the intelligence layer responds. Watch the alerts cascade. Watch the system tell you exactly what to do.

**That's what RTI + IQ does under pressure. That's what our customers need.**

---

*Built with AI. In 2 hours. By leaders, not just engineers. That's the point.*
