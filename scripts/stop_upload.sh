#!/bin/bash
echo "🔍 Finding upload process..."
PID=$(ps aux | grep "[u]pload_chunked.py" | awk '{print \$2}')

if [ -z "$PID" ]; then
    echo "⚠️  No upload process found"
else
    echo "🛑 Stopping process $PID..."
    kill $PID
    sleep 2
    
    # Force kill if still running
    if ps -p $PID > /dev/null; then
        echo "💥 Force stopping..."
        kill -9 $PID
    fi
    
    echo "✅ Upload stopped!"
fi

# Show any remaining python processes
echo ""
echo "📋 Remaining Python processes:"
ps aux | grep python | grep -v grep
