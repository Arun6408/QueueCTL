# QueueCTL - 2-Minute Video Script

## Timing Breakdown
- **0:00-0:15** - Introduction & Problem
- **0:15-0:30** - Key Features Overview
- **0:30-1:30** - Live Demo
- **1:30-2:00** - Conclusion & Highlights

---

## Script

### [0:00-0:15] Introduction

**"Hi! I'm [Your Name], and today I'm presenting QueueCTL - a production-grade CLI-based background job queue system I built for my backend developer internship assignment."**

**[Show terminal/IDE]**

**"QueueCTL solves a critical problem: managing background jobs with automatic retries, worker processes, and a Dead Letter Queue - all accessible through a simple CLI interface."**

---

### [0:15-0:30] Key Features

**"Let me highlight the core features:"**

**[Switch to README or feature list]**

**"First, it supports multiple parallel workers that process jobs concurrently. Second, failed jobs automatically retry with exponential backoff. Third, permanently failed jobs move to a Dead Letter Queue. And finally, everything persists across restarts using SQLite."**

**"Plus, I've added bonus features like priority queues, scheduled jobs, job timeouts, execution metrics, and a real-time web dashboard."**

---

### [0:30-1:30] Live Demo

**[Switch to terminal - have commands ready]**

**"Let's see it in action!"**

#### Demo Step 1: Enqueue Jobs (0:30-0:45)

**"First, I'll enqueue a few jobs - one that succeeds, one that will fail and retry, and a high-priority job."**

**For PowerShell (use variables):**
```powershell
$job1 = '{"id":"job1","command":"echo Hello World","priority":1}'
$job2 = '{"id":"job2","command":"exit 1","max_retries":2}'
$job3 = '{"id":"urgent","command":"echo Urgent Task","priority":10}'
queuectl enqueue $job1
queuectl enqueue $job2
queuectl enqueue $job3
```

**For Bash/Linux (direct quotes):**
```bash
queuectl enqueue '{"id":"job1","command":"echo Hello World","priority":1}'
queuectl enqueue '{"id":"job2","command":"exit 1","max_retries":2}'
queuectl enqueue '{"id":"urgent","command":"echo Urgent Task","priority":10}'
```

**[Show output]**

**"Notice the high-priority job will be processed first."**

#### Demo Step 2: Start Workers (0:45-0:50)

**"Now let's start 2 workers to process these jobs."**

```bash
queuectl worker start --count 2
```

**[Show "Started 2 worker(s)"]**

#### Demo Step 3: Monitor Status (0:50-1:00)

**"Let's check the status to see jobs being processed."**

```bash
queuectl status
```

**[Show status output - point out pending/processing/completed counts]**

**"You can see workers are active and jobs are moving through the system."**

#### Demo Step 4: View Jobs (1:00-1:10)

**"Let's list the completed jobs."**

```bash
queuectl list --state completed
```

**[Show completed jobs]**

**"And check the failed job that's being retried."**

```bash
queuectl list --state failed
```

**[Show failed job with attempts]**

#### Demo Step 5: Dead Letter Queue (1:10-1:20)

**"After retries are exhausted, failed jobs move to the Dead Letter Queue."**

**[Wait a moment, then show]**

```bash
queuectl dlq list
```

**[Show DLQ jobs]**

**"We can retry a DLQ job if needed."**

```bash
queuectl dlq retry job2
```

#### Demo Step 6: Web Dashboard (1:20-1:30)

**"Finally, let's start the web dashboard for real-time monitoring."**

```bash
queuectl dashboard
```

**[Open browser to http://localhost:8080]**

**"The dashboard shows live statistics, worker status, and recent jobs - auto-refreshing every 5 seconds."**

**[Show dashboard briefly]**

---

### [1:30-2:00] Conclusion

**[Switch back to terminal or project overview]**

**"To summarize: QueueCTL provides a complete job queue solution with workers, retries, DLQ, persistence, and monitoring - all through a clean CLI interface."**

**"The architecture is modular, thread-safe, and production-ready. It handles concurrency safely, persists data across restarts, and includes comprehensive error handling."**

**"The code is well-documented, includes test scenarios, and demonstrates best practices in backend development."**

**"Thank you for watching! The full source code and documentation are available in the GitHub repository."**

---

## Tips for Recording

1. **Preparation:**
   - Have terminal ready with QueueCTL installed
   - Pre-clear any existing database: `rm queuectl.db` (if exists)
   - Have browser ready for dashboard demo
   - Test all commands beforehand

2. **Terminal Setup:**
   - Use a clean terminal with good contrast
   - Increase font size for visibility
   - Use a readable color scheme
   - Clear terminal between sections (optional)

3. **Pacing:**
   - Speak clearly and at moderate pace
   - Pause briefly after commands to show output
   - Don't rush - 2 minutes is enough time

4. **Visuals:**
   - Zoom in on terminal when showing commands
   - Use screen annotations to highlight important parts
   - Show file structure briefly if time permits

5. **Backup Plan:**
   - If something fails, have screenshots ready
   - Can edit out mistakes in post-production
   - Keep demo simple - don't try to show everything

---

## Alternative Shorter Script (If Running Long)

If you're running over 2 minutes, use this condensed version:

- **0:00-0:20**: Intro + Features
- **0:20-1:20**: Quick demo (enqueue → workers → status → DLQ)
- **1:20-2:00**: Dashboard + Conclusion

Skip the detailed job listing and focus on the key flows.

