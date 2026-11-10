import os
import shutil
import time
import tkinter as tk
from tkinter import ttk
from pathlib import Path


class SystemMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("URI System Monitor")
        self.root.geometry("620x470")
        self.root.minsize(520, 420)
        self.root.configure(bg="#101827")

        self.previous_cpu = self.read_cpu_times()
        self.started_at = time.time()
        self.labels = {}
        self.bars = {}

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Monitor.Horizontal.TProgressbar",
            troughcolor="#263449",
            background="#38bdf8",
            bordercolor="#263449",
            lightcolor="#38bdf8",
            darkcolor="#38bdf8",
        )

        header = tk.Frame(root, bg="#101827")
        header.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(
            header, text="URI SYSTEM MONITOR",
            font=("DejaVu Sans", 19, "bold"),
            fg="#e5f3ff", bg="#101827"
        ).pack(anchor="w")
        tk.Label(
            header, text="パソコンの状態をリアルタイムで確認",
            font=("Sans", 10), fg="#91a4bd", bg="#101827"
        ).pack(anchor="w", pady=(4, 0))

        self.status = tk.Label(
            root, text="● MONITORING", font=("Sans", 9, "bold"),
            fg="#4ade80", bg="#101827"
        )
        self.status.pack(anchor="w", padx=26, pady=(5, 8))

        panel = tk.Frame(root, bg="#1b293d", padx=18, pady=16)
        panel.pack(fill="both", expand=True, padx=22, pady=8)

        self.add_metric(panel, "CPU 使用率", "cpu")
        self.add_metric(panel, "メモリ使用率", "memory")
        self.add_metric(panel, "ホームディスク使用率", "disk")

        info = tk.Frame(panel, bg="#1b293d")
        info.pack(fill="x", pady=(18, 0))
        self.info_label = tk.Label(
            info, text="", justify="left", anchor="w",
            font=("DejaVu Sans", 10), fg="#c6d5e8", bg="#1b293d"
        )
        self.info_label.pack(fill="x")

        footer = tk.Label(
            root, text="更新間隔: 1秒  |  Linux / Ubuntu 向け",
            font=("Sans", 9), fg="#71849e", bg="#101827"
        )
        footer.pack(pady=(3, 12))

        self.update_metrics()

    def add_metric(self, parent, title, key):
        row = tk.Frame(parent, bg="#1b293d")
        row.pack(fill="x", pady=8)

        top = tk.Frame(row, bg="#1b293d")
        top.pack(fill="x")
        tk.Label(
            top, text=title, font=("Sans", 11, "bold"),
            fg="#e5f3ff", bg="#1b293d"
        ).pack(side="left")
        value = tk.Label(
            top, text="--%", font=("DejaVu Sans", 12, "bold"),
            fg="#7dd3fc", bg="#1b293d"
        )
        value.pack(side="right")
        self.labels[key] = value

        bar = ttk.Progressbar(
            row, maximum=100, mode="determinate",
            style="Monitor.Horizontal.TProgressbar"
        )
        bar.pack(fill="x", pady=(7, 0))
        self.bars[key] = bar

    @staticmethod
    def read_cpu_times():
        try:
            with open("/proc/stat", "r", encoding="utf-8") as file:
                values = [int(v) for v in file.readline().split()[1:]]
            idle = values[3] + (values[4] if len(values) > 4 else 0)
            return sum(values), idle
        except (OSError, ValueError, IndexError):
            return None

    def cpu_percent(self):
        current = self.read_cpu_times()
        if current is None or self.previous_cpu is None:
            self.previous_cpu = current
            return 0.0

        total_delta = current[0] - self.previous_cpu[0]
        idle_delta = current[1] - self.previous_cpu[1]
        self.previous_cpu = current
        if total_delta <= 0:
            return 0.0
        return max(0.0, min(100.0, (1 - idle_delta / total_delta) * 100))

    @staticmethod
    def memory_percent():
        values = {}
        try:
            with open("/proc/meminfo", "r", encoding="utf-8") as file:
                for line in file:
                    parts = line.split()
                    if len(parts) >= 2:
                        values[parts[0].rstrip(":")] = int(parts[1])
            total = values["MemTotal"]
            available = values.get("MemAvailable", values.get("MemFree", 0))
            used = total - available
            return used / total * 100 if total else 0.0, used, total
        except (OSError, ValueError, KeyError):
            return 0.0, 0, 0

    @staticmethod
    def format_gib(kib):
        return f"{kib / 1024 / 1024:.1f} GB"

    def update_metrics(self):
        cpu = self.cpu_percent()
        memory, memory_used, memory_total = self.memory_percent()
        disk = shutil.disk_usage(Path.home())
        disk_percent = disk.used / disk.total * 100 if disk.total else 0

        for key, value in (
            ("cpu", cpu), ("memory", memory), ("disk", disk_percent)
        ):
            self.labels[key].config(text=f"{value:.1f}%")
            self.bars[key]["value"] = value

        uptime_text = "取得できません"
        try:
            with open("/proc/uptime", "r", encoding="utf-8") as file:
                seconds = int(float(file.read().split()[0]))
            hours, remainder = divmod(seconds, 3600)
            minutes = remainder // 60
            uptime_text = f"{hours}時間 {minutes}分"
        except (OSError, ValueError, IndexError):
            pass

        self.info_label.config(
            text=(
                f"メモリ: {self.format_gib(memory_used)} / "
                f"{self.format_gib(memory_total)}\n"
                f"ディスク空き容量: {self.format_gib(disk.free // 1024)}\n"
                f"稼働時間: {uptime_text}"
            )
        )
        self.root.after(1000, self.update_metrics)


def main():
    root = tk.Tk()
    SystemMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
