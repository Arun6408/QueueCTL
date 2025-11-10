# Live Demo Steps - QueueCTL

## Pre-Demo Setup (Do this BEFORE recording)

1. **Clean Environment:**
   ```powershell
   Remove-Item queuectl.db -ErrorAction SilentlyContinue
   Remove-Item .queuectl_*.lock -ErrorAction SilentlyContinue
   ```

2. **Verify Installation:**
   ```powershell
   queuectl --version
   ```

3. **Test a Simple Command:**
   ```powershell
   $test = '{"id":"test","command":"echo test"}'
   queuectl enqueue $test
   queuectl list
   ```

---

## Live Demo Commands (In Order)

### Step 1: Enqueue Jobs (30 seconds)

**Copy and paste these commands one by one:**

```powershell
# Job 1: Simple successful job
$job1 = '{"id":"job1","command":"echo Hello World","priority":1}'
queuectl enqueue $job1

# Job 2: Job that will fail (for retry demo)
$job2 = '{"id":"job2","command":"exit 1","max_retries":2}'
queuectl enqueue $job2

# Job 3: High priority job
$job3 = '{"id":"urgent","command":"echo Urgent Task","priority":10}'
queuectl enqueue $job3
```

**What to say:** *"I'm enqueuing three jobs - a simple echo command, a job that will fail to demonstrate retries, and a high-priority job that should be processed first."*

---

### Step 2: Check Initial Status (10 seconds)

```powershell
queuectl status
```

**What to say:** *"Before starting workers, we can see all three jobs are in pending state."*

---

### Step 3: Start Workers (10 seconds)

```powershell
queuectl worker start --count 2
```

**What to say:** *"Now I'll start 2 worker processes to handle these jobs in parallel."*

---

### Step 4: Monitor Progress (20 seconds)

**Wait 3-4 seconds, then:**

```powershell
queuectl status
```

**What to say:** *"Let's check the status again. You can see workers are active, and jobs are being processed. The high-priority job was likely processed first."*

---

### Step 5: View Completed Jobs (10 seconds)

```powershell
queuectl list --state completed
```

**What to say:** *"Here are the completed jobs. Notice job1 and urgent are done."*

---

### Step 6: Check Failed Job (10 seconds)

```powershell
queuectl list --state failed
```

**What to say:** *"Job2 failed as expected. You can see it has 1 attempt out of 2 max retries. The system will automatically retry it with exponential backoff."*

---

### Step 7: Wait for Retry (10 seconds)

**Wait 5-6 seconds (or mention it's happening in background), then:**

```powershell
queuectl list --state failed
```

**What to say:** *"After the backoff delay, the job was retried. Since it failed again and reached max retries, it should move to the Dead Letter Queue."*

---

### Step 8: Show Dead Letter Queue (10 seconds)

```powershell
queuectl dlq list
```

**What to say:** *"Here's the Dead Letter Queue. Permanently failed jobs are stored here. We can retry them manually if needed."*

---

### Step 9: Retry DLQ Job (10 seconds)

```powershell
queuectl dlq retry job2
queuectl list --state pending
```

**What to say:** *"I can reset a DLQ job back to pending state. It will be processed again with a fresh attempt counter."*

---

### Step 10: Web Dashboard (20 seconds)

**Open a NEW terminal window/tab:**

```powershell
queuectl dashboard
```

**Then open browser to:** `http://localhost:8080`

**What to say:** *"Finally, QueueCTL includes a real-time web dashboard. It shows live statistics, worker status, and recent jobs, auto-refreshing every 5 seconds."*

**[Show dashboard for a few seconds]**

---

## Quick Demo (If Running Short on Time)

**Condensed 1-minute version:**

1. Enqueue 2 jobs (one success, one fail)
2. Start 1 worker
3. Show status
4. Show DLQ
5. Mention dashboard

---

## Troubleshooting During Demo

### If a command fails:
- **Stay calm** - say "Let me try that again"
- Have backup commands ready
- Can edit out mistakes in post-production

### If workers don't process:
- Check: `queuectl status`
- Restart: `queuectl worker stop` then `queuectl worker start --count 2`

### If JSON error:
- Use the variable method: `$job = '{"id":"test","command":"echo test"}'`
- Then: `queuectl enqueue $job`

---

## Post-Demo Checklist

- [ ] Stop workers: `queuectl worker stop`
- [ ] Stop dashboard (Ctrl+C)
- [ ] Clean up if needed for next recording

---

## Tips for Smooth Demo

1. **Practice first** - Run through the demo 2-3 times before recording
2. **Have commands ready** - Copy them to a text file for quick paste
3. **Use large font** - Make terminal text easily readable
4. **Pause after commands** - Give time to see output
5. **Speak clearly** - Explain what's happening
6. **Show enthusiasm** - This is your project, be proud!

---

## Alternative: Use Demo Script

If you want to automate parts:

```powershell
.\demo.ps1
```

Then manually show the interesting parts (status, DLQ, dashboard).


