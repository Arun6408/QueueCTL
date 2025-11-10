# PowerShell Commands for QueueCTL

PowerShell handles quotes differently than bash. Here are the correct commands:

## Enqueue Commands

### Option 1: Escape with Backticks (Recommended)
```powershell
queuectl enqueue "{\`"id\`":\`"live_demo_1\`",\`"command\`":\`"echo Hello This is a live Demo from QueueCTL\`",\`"max_retries\`":3}"
```

### Option 2: Use Single Quotes (Simpler)
```powershell
queuectl enqueue '{"id":"live_demo_1","command":"echo Hello This is a live Demo from QueueCTL","max_retries":3}'
```

### Option 3: Use Here-String (For Complex JSON)
```powershell
$json = @'
{"id":"live_demo_1","command":"echo Hello This is a live Demo from QueueCTL","max_retries":3}
'@
queuectl enqueue $json
```

## Complete Demo Commands for PowerShell

### Step 1: Clean Up
```powershell
Remove-Item queuectl.db -ErrorAction SilentlyContinue
Remove-Item .queuectl_*.lock -ErrorAction SilentlyContinue
```

### Step 2: Enqueue Jobs
```powershell
# Successful job
queuectl enqueue '{"id":"job1","command":"echo Hello World","priority":1}'

# Job that will fail
queuectl enqueue '{"id":"job2","command":"exit 1","max_retries":2}'

# High priority job
queuectl enqueue '{"id":"urgent","command":"echo Urgent Task","priority":10}'
```

### Step 3: Start Workers
```powershell
queuectl worker start --count 2
```

### Step 4: Check Status
```powershell
queuectl status
```

### Step 5: List Jobs
```powershell
queuectl list --state completed
queuectl list --state failed
```

### Step 6: Check DLQ
```powershell
queuectl dlq list
```

### Step 7: Start Dashboard
```powershell
queuectl dashboard
```

## Quick Test

Try this simple command first:
```powershell
queuectl enqueue '{"id":"test","command":"echo test"}'
```

If that works, the single quote method is working. If not, try the backtick escaping method.


