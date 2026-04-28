import asyncio
import logging
import os

from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/api/system", tags=["system"])


def _format_uptime(uptime_sec: float) -> str:
    days = int(uptime_sec // 86400)
    hours = int((uptime_sec % 86400) // 3600)
    minutes = int((uptime_sec % 3600) // 60)
    if days > 0:
        return f"{days}d {hours}h"
    return f"{hours}h {minutes}m"


def _fallback_stats() -> dict:
    try:
        load_1m, load_5m, load_15m = os.getloadavg()
    except (AttributeError, OSError):
        load_1m, load_5m, load_15m = 0.0, 0.0, 0.0

    mem_total_gb = 0.0
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        phys_pages = os.sysconf("SC_PHYS_PAGES")
        mem_total_gb = round(page_size * phys_pages / 1024 / 1024 / 1024, 1)
    except (AttributeError, OSError, ValueError):
        pass

    return {
        "cpu_percent": 0.0,
        "mem_total_gb": mem_total_gb,
        "mem_used_gb": 0.0,
        "mem_percent": 0.0,
        "load_1m": float(load_1m),
        "load_5m": float(load_5m),
        "load_15m": float(load_15m),
        "uptime": "n/a",
        "uptime_seconds": 0,
    }


@router.get("/stats")
async def get_system_stats():
    """读取宿主机真实系统状态（CPU、内存、负载、运行时间）。"""
    try:
        proc_path = "/host_proc"
        # fallback：如果没挂载 host_proc 则用容器自身的 /proc
        if not os.path.exists(f"{proc_path}/stat"):
            proc_path = "/proc"
        if not os.path.exists(f"{proc_path}/stat"):
            return {"success": True, "data": _fallback_stats()}

        stats = {}

        def read_cpu_times(p):
            with open(f"{p}/stat") as f:
                line = f.readline()
            fields = line.split()[1:]
            values = [int(x) for x in fields[:8]]
            idle = values[3] + values[4]
            total = sum(values)
            return total, idle

        t1_total, t1_idle = read_cpu_times(proc_path)
        await asyncio.sleep(0.1)
        t2_total, t2_idle = read_cpu_times(proc_path)

        diff_total = t2_total - t1_total
        diff_idle = t2_idle - t1_idle
        cpu_pct = (1 - diff_idle / diff_total) * 100 if diff_total > 0 else 0
        stats["cpu_percent"] = round(cpu_pct, 1)

        mem_info = {}
        with open(f"{proc_path}/meminfo") as f:
            for line in f:
                parts = line.split()
                key = parts[0].rstrip(":")
                val = int(parts[1])
                mem_info[key] = val

        mem_total = mem_info.get("MemTotal", 0)
        mem_available = mem_info.get("MemAvailable", 0)
        mem_used = mem_total - mem_available
        mem_pct = (mem_used / mem_total * 100) if mem_total > 0 else 0

        stats["mem_total_gb"] = round(mem_total / 1024 / 1024, 1)
        stats["mem_used_gb"] = round(mem_used / 1024 / 1024, 1)
        stats["mem_percent"] = round(mem_pct, 1)

        with open(f"{proc_path}/loadavg") as f:
            load_parts = f.read().split()
        stats["load_1m"] = float(load_parts[0])
        stats["load_5m"] = float(load_parts[1])
        stats["load_15m"] = float(load_parts[2])

        with open(f"{proc_path}/uptime") as f:
            uptime_sec = float(f.read().split()[0])
        stats["uptime"] = _format_uptime(uptime_sec)
        stats["uptime_seconds"] = int(uptime_sec)

        return {"success": True, "data": stats}
    except Exception as e:
        logging.exception("获取系统状态失败")
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {e}")
