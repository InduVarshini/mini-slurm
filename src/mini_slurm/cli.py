"""Command-line interface for mini-slurm."""

import argparse
import json
from .core import MiniSlurm
from .utils import parse_mem, format_ts


def cmd_submit(args):
    ms = MiniSlurm()
    mem_mb = parse_mem(args.mem)
    command = " ".join(args.command)
    
    is_elastic = args.elastic
    min_cpus = args.min_cpus if args.min_cpus else None
    max_cpus = args.max_cpus if args.max_cpus else None
    
    if is_elastic:
        if min_cpus is None:
            min_cpus = args.cpus
        if max_cpus is None:
            max_cpus = ms.total_cpus
    
    job_id = ms.submit_job(
        cpus=args.cpus, 
        mem_mb=mem_mb, 
        command=command, 
        priority=args.priority,
        is_elastic=is_elastic,
        min_cpus=min_cpus,
        max_cpus=max_cpus
    )
    print(f"Submitted job {job_id}")
    if is_elastic:
        print(f"  [ELASTIC] cpus={args.cpus} (min={min_cpus}, max={max_cpus}), mem={mem_mb}MB, priority={args.priority}")
    else:
        print(f"  cpus={args.cpus}, mem={mem_mb}MB, priority={args.priority}")
    print(f"  command={command}")


def cmd_queue(args):
    ms = MiniSlurm()
    rows = ms.list_jobs(status=args.status)
    if not rows:
        print("No jobs found.")
        return
    print(f"{'ID':>4} {'STAT':>8} {'CPU':>3} {'MEM(MB)':>7} {'PRI':>3} {'WAIT(s)':>8} "
          f"{'RUN(s)':>8} {'ELASTIC':>8} {'SUBMIT':>19} COMMAND")
    for row in rows:
        if len(row) >= 15:  # New format with elastic fields
            (job_id, command, cpus, mem_mb, status, priority,
             submit_time, start_time, end_time, wait_time, runtime,
             is_elastic, min_cpus, max_cpus, current_cpus) = row
            elastic_str = ""
            if is_elastic:
                if current_cpus:
                    elastic_str = f"{current_cpus}/{max_cpus}"
                else:
                    elastic_str = f"{cpus}/{max_cpus}"
        else:  # Old format (backward compatibility)
            (job_id, command, cpus, mem_mb, status, priority,
             submit_time, start_time, end_time, wait_time, runtime) = row[:11]
            elastic_str = ""
        
        print(
            f"{job_id:>4} {status:>8} {cpus:>3} {mem_mb:>7} {priority:>3} "
            f"{(wait_time or 0):>8.1f} {(runtime or 0):>8.1f} "
            f"{elastic_str:>8} {format_ts(submit_time):>19} {command}"
        )


def cmd_show(args):
    ms = MiniSlurm()
    job = ms.get_job(args.job_id)
    if not job:
        print(f"Job {args.job_id} not found")
        return

    # Handle both old and new schema (with elastic fields and topology)
    if len(job) >= 23:  # New schema with elastic fields and nodes
        (
            job_id,
            command,
            cpus,
            mem_mb,
            status,
            priority,
            submit_time,
            start_time,
            end_time,
            wait_time,
            runtime,
            return_code,
            user,
            stdout_path,
            stderr_path,
            cpu_user_time,
            cpu_system_time,
            is_elastic,
            min_cpus,
            max_cpus,
            current_cpus,
            control_file,
            nodes,
        ) = job
    elif len(job) >= 22:  # Schema with elastic fields but no nodes
        (
            job_id,
            command,
            cpus,
            mem_mb,
            status,
            priority,
            submit_time,
            start_time,
            end_time,
            wait_time,
            runtime,
            return_code,
            user,
            stdout_path,
            stderr_path,
            cpu_user_time,
            cpu_system_time,
            is_elastic,
            min_cpus,
            max_cpus,
            current_cpus,
            control_file,
        ) = job
        nodes = None
    else:  # Old schema (backward compatibility)
        (
            job_id,
            command,
            cpus,
            mem_mb,
            status,
            priority,
            submit_time,
            start_time,
            end_time,
            wait_time,
            runtime,
            return_code,
            user,
            stdout_path,
            stderr_path,
            cpu_user_time,
            cpu_system_time,
        ) = job[:17]
        is_elastic = False
        min_cpus = None
        max_cpus = None
        current_cpus = None
        control_file = None
        nodes = None

    print(f"Job {job_id}")
    print(f"  User:        {user}")
    print(f"  Status:      {status}")
    print(f"  Priority:    {priority}")
    print(f"  Command:     {command}")
    if is_elastic:
        print(f"  Type:        ELASTIC")
        print(f"  CPUs:        {cpus} (current: {current_cpus or cpus}, min: {min_cpus}, max: {max_cpus})")
    else:
        print(f"  CPUs:        {cpus}")
    print(f"  Mem (MB):    {mem_mb}")
    if nodes:
        try:
            nodes_list = json.loads(nodes) if isinstance(nodes, str) else nodes
            print(f"  Nodes:       {','.join(nodes_list)}")
        except (json.JSONDecodeError, TypeError):
            if nodes:
                print(f"  Nodes:       {nodes}")
    print(f"  Submitted:   {format_ts(submit_time)}")
    print(f"  Started:     {format_ts(start_time)}")
    print(f"  Ended:       {format_ts(end_time)}")
    print(f"  Wait time:   {wait_time:.2f}s" if wait_time else "  Wait time:   -")
    print(f"  Runtime:     {runtime:.2f}s" if runtime else "  Runtime:     -")
    print(f"  Return code: {return_code}")
    print(f"  Stdout:      {stdout_path}")
    print(f"  Stderr:      {stderr_path}")
    if cpu_user_time is not None:
        print(f"  CPU user:    {cpu_user_time:.2f}s")
    if cpu_system_time is not None:
        print(f"  CPU system:  {cpu_system_time:.2f}s")
    if control_file:
        print(f"  Control:     {control_file}")


def cmd_cancel(args):
    ms = MiniSlurm()
    ok = ms.cancel_job(args.job_id)
    if ok:
        print(f"Cancelled job {args.job_id}")
    else:
        print(f"Could not cancel job {args.job_id} "
              f"(maybe it is not PENDING or does not exist)")


def cmd_scheduler(args):
    ms = MiniSlurm(
        total_cpus=args.total_cpus,
        total_mem_mb=parse_mem(args.total_mem) if args.total_mem else None,
        topology_config_path=args.topology_config,
    )
    ms.scheduler_loop(
        poll_interval=args.poll_interval,
        elastic_scale_threshold=args.elastic_threshold,
        enable_elastic_scaling=not args.disable_elastic
    )


def cmd_stats(args):
    ms = MiniSlurm(
        total_cpus=args.total_cpus,
        total_mem_mb=parse_mem(args.total_mem) if args.total_mem else None,
    )
    stats = ms.get_stats()
    
    print("=" * 60)
    print("Mini-SLURM Statistics")
    print("=" * 60)
    print()
    
    # System Resources
    print("System Resources:")
    print(f"  Total CPUs:     {stats['total_cpus']}")
    print(f"  Used CPUs:      {stats['used_cpus']} ({stats['used_cpus']/stats['total_cpus']*100:.1f}%)")
    print(f"  Available CPUs: {stats['total_cpus'] - stats['used_cpus']}")
    print(f"  Total Memory:   {stats['total_mem_mb']:.0f} MB ({stats['total_mem_mb']/1024:.1f} GB)")
    print(f"  Used Memory:    {stats['used_mem_mb']:.0f} MB ({stats['used_mem_mb']/stats['total_mem_mb']*100:.1f}%)")
    print(f"  Available Mem:  {stats['total_mem_mb'] - stats['used_mem_mb']:.0f} MB")
    if stats['cpu_percent'] is not None:
        print(f"  System CPU %:   {stats['cpu_percent']:.1f}%")
    if stats['mem_percent'] is not None:
        print(f"  System Mem %:   {stats['mem_percent']:.1f}%")
    print()
    
    # Job Statistics
    print("Job Statistics:")
    print(f"  Total Jobs:     {stats['total_jobs']}")
    print(f"  Running:        {stats['running_count']}")
    print(f"  Pending:        {stats['pending_count']}")
    for status in ['COMPLETED', 'FAILED', 'CANCELLED']:
        count = stats['status_counts'].get(status, 0)
        if count > 0:
            print(f"  {status:12} {count}")
    print()
    
    # Performance Metrics
    if stats['completed_count'] > 0:
        print("Performance Metrics (completed jobs):")
        print(f"  Average Wait Time:  {stats['avg_wait_time']:.2f} seconds")
        print(f"  Average Runtime:    {stats['avg_runtime']:.2f} seconds")
        print()
    
    # Status Breakdown
    if stats['status_counts']:
        print("Status Breakdown:")
        for status, count in sorted(stats['status_counts'].items()):
            percentage = (count / stats['total_jobs'] * 100) if stats['total_jobs'] > 0 else 0
            print(f"  {status:12} {count:4} ({percentage:5.1f}%)")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="mini-slurm",
        description="Mini-SLURM: a tiny local HPC-style job scheduler",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # submit
    p_submit = sub.add_parser("submit", help="Submit a job")
    p_submit.add_argument("--cpus", type=int, required=True, help="CPUs required (initial for elastic jobs)")
    p_submit.add_argument("--mem", type=str, required=True, help="Memory (e.g. 8GB, 1024MB)")
    p_submit.add_argument("--priority", type=int, default=0, help="Job priority (higher = earlier)")
    p_submit.add_argument("--elastic", action="store_true", help="Enable elastic scaling for this job")
    p_submit.add_argument("--min-cpus", type=int, help="Minimum CPUs for elastic job (default: initial cpus)")
    p_submit.add_argument("--max-cpus", type=int, help="Maximum CPUs for elastic job (default: total system CPUs)")
    p_submit.add_argument("command", nargs=argparse.REMAINDER, help="Command to run")
    p_submit.set_defaults(func=cmd_submit)

    # queue
    p_queue = sub.add_parser("queue", help="Show job queue")
    p_queue.add_argument("--status", choices=["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"],
                         help="Filter by status")
    p_queue.set_defaults(func=cmd_queue)

    # show
    p_show = sub.add_parser("show", help="Show job details")
    p_show.add_argument("job_id", type=int)
    p_show.set_defaults(func=cmd_show)

    # cancel
    p_cancel = sub.add_parser("cancel", help="Cancel a pending job")
    p_cancel.add_argument("job_id", type=int)
    p_cancel.set_defaults(func=cmd_cancel)

    # scheduler
    p_sched = sub.add_parser("scheduler", help="Run the scheduler loop")
    p_sched.add_argument("--total-cpus", type=int, help="Override detected total CPUs")
    p_sched.add_argument("--total-mem", type=str, help="Override total memory (e.g. 16GB)")
    p_sched.add_argument("--poll-interval", type=float, default=1.0, help="Scheduler poll interval (seconds)")
    p_sched.add_argument("--elastic-threshold", type=float, default=50.0, 
                        help="Cluster utilization threshold for elastic scaling (default: 50%%)")
    p_sched.add_argument("--disable-elastic", action="store_true", 
                        help="Disable elastic job scaling")
    p_sched.add_argument("--topology-config", type=str, 
                        help="Path to topology configuration file (default: ~/.mini_slurm_topology.conf)")
    p_sched.set_defaults(func=cmd_scheduler)

    # stats
    p_stats = sub.add_parser("stats", help="Show system statistics and job metrics")
    p_stats.add_argument("--total-cpus", type=int, help="Override detected total CPUs")
    p_stats.add_argument("--total-mem", type=str, help="Override total memory (e.g. 16GB)")
    p_stats.set_defaults(func=cmd_stats)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
