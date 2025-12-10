#!/bin/bash
# Quick test script for Mini-SLURM

set -e

echo "=========================================="
echo "Mini-SLURM Local Testing Script"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if scheduler is running
if pgrep -f "mini-slurm.py scheduler" > /dev/null; then
    echo -e "${GREEN}✓ Scheduler is running${NC}"
else
    echo -e "${YELLOW}⚠ Scheduler is not running${NC}"
    echo "Start it with: python3 mini-slurm.py scheduler &"
    echo ""
    read -p "Start scheduler now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 mini-slurm.py scheduler > /dev/null 2>&1 &
        echo -e "${GREEN}Scheduler started in background${NC}"
        sleep 2
    else
        echo "Please start the scheduler manually and run this script again"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}Test 1: Submit a simple job${NC}"
python3 mini-slurm.py submit --cpus 1 --mem 512MB "echo 'Test 1: Simple job' && sleep 2"
JOB1=$(python3 mini-slurm.py queue | tail -1 | awk '{print $1}')
echo "Submitted job $JOB1"
sleep 1

echo ""
echo -e "${BLUE}Test 2: Submit a high-priority job${NC}"
python3 mini-slurm.py submit --cpus 1 --mem 512MB --priority 10 "echo 'Test 2: High priority' && sleep 2"
JOB2=$(python3 mini-slurm.py queue | tail -1 | awk '{print $1}')
echo "Submitted job $JOB2"

echo ""
echo -e "${BLUE}Test 3: View queue${NC}"
python3 mini-slurm.py queue

echo ""
echo -e "${BLUE}Test 4: View statistics${NC}"
python3 mini-slurm.py stats

echo ""
echo -e "${BLUE}Test 5: Submit job exceeding resources (should stay pending)${NC}"
python3 mini-slurm.py submit --cpus 100 --mem 100GB "echo 'This should wait'"
JOB3=$(python3 mini-slurm.py queue | tail -1 | awk '{print $1}')
sleep 1
python3 mini-slurm.py queue --status PENDING

echo ""
echo -e "${BLUE}Test 6: Cancel pending job${NC}"
python3 mini-slurm.py cancel $JOB3
python3 mini-slurm.py queue --status CANCELLED

echo ""
echo -e "${BLUE}Test 7: View job details${NC}"
python3 mini-slurm.py show $JOB1

echo ""
echo -e "${BLUE}Waiting for jobs to complete...${NC}"
sleep 5

echo ""
echo -e "${BLUE}Final queue status:${NC}"
python3 mini-slurm.py queue

echo ""
echo -e "${BLUE}Final statistics:${NC}"
python3 mini-slurm.py stats

echo ""
echo -e "${GREEN}=========================================="
echo "All tests completed!"
echo "==========================================${NC}"
echo ""
echo "View logs: ls -lh ~/.mini_slurm_logs/"
echo "View database: sqlite3 ~/.mini_slurm.db 'SELECT * FROM jobs;'"

