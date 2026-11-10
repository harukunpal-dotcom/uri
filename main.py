import glob
import shutil
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk


BG = "#101827"
PANEL = "#1b293d"
TEXT = "#e5f3ff"
MUTED = "#91a4bd"
BLUE = "#38bdf8"
GREEN = "#4ade80"
ORANGE = "#fbbf24"
PURPLE = "#c4b5fd"


class SystemMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("URI System Monitor")
        self.root.geometry("850x720")
        self.root.minsize(650, 600)
        self.root.configure(bg=BG)

        self.previous_cpu = self.read_cpu_times()
        self.previous_network = self.read_network()
        self.previous_time = time.monotonic()
        self.history_cpu = [0.0] * 60
        self.history_memory = [0.0] * 60
        self.history_rx = [0.0] * 60
        self.history_tx = [0.0] * 60
        self.labels = {}
        self.bars = {}

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Monitor.Horizontal.TProgressbar",
            troughcolor="#263449", background=BLUE,
            bordercolor="#263449", lightcolor=BLUE, darkcolor=BLUE,
        )

        header = tk.Frame(root, bg=BG)
        header.pack(fill="x", padx=24, pady=(18, 8))
        tk.Label(
            header, text="URI SYSTEM MONITOR",
            font=("DejaVu Sans", 20, "bold"), fg=TEXT, bg=BG,
        ).pack(anchor="w")
        tk.Label(
            header, text="Linux PC の状態をリアルタイムでチェック",
            font=("Sans", 10), fg=MUTED, bg=BG,
        ).pack(anchor="w", pady=(4, 0))

        self.status = tk.Label(
            root, text="● MONITORING", font=("Sans", 9, "bold"),
            fg=GREEN, bg=BG,
        )
        self.status.pack(anchor="w", padx=26, pady=(3, 5))

        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=6)

        left = tk.Frame(body, bg=PANEL, padx=16, pady=12)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.configure(width=290)
        left.pack_propagate(False)

        self.add_metric(left, "CPU 使用率", "cpu", BLUE)
        self.add_metric(left, "メモリ使用率", "memory", GREEN)
        self.add_metric(left, "ホームディスク使用率", "disk", PURPLE)

        tk.Label(
            left, text="ハードウェア情報", font=("Sans", 11, "bold"),
            fg=TEXT, bg=PANEL,
        ).pack(anchor="w", pady=(20, 8))
        self.temperature_label = self.make_info_label(left)
        self.memory_detail_label = self.make_info_label(left)
        self.disk_detail_label = self.make_info_label(left)
        self.uptime_label = self.make_info_label(left)

        right = tk.Frame(body, bg=PANEL, padx=14, pady=12)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(
            right, text="使用率の履歴（直近60回）",
            font=("Sans", 11, "bold"), fg=TEXT, bg=PANEL,
        ).pack(anchor="w")
        self.usage_canvas = tk.Canvas(
            right, height=210, bg="#142033", highlightthickness=0,
        )
        self.usage_canvas.pack(fill="x", pady=(8, 16))

        tk.Label(
            right, text="ネットワーク速度",
            font=("Sans", 11, "bold"), fg=TEXT, bg=PANEL,
        ).pack(anchor="w")
        self.network_label = tk.Label(
            right, text="受信 0 KB/s   |   送信 0 KB/s",
            font=("DejaVu Sans", 10, "bold"), fg=BLUE, bg=PANEL,
        )
        self.network_label.pack(anchor="w", pady=(5, 0))
        self.network_canvas = tk.Canvas(
            right, height=170, bg="#142033", highlightthickness=0,
        )
        self.network_canvas.pack(fill="x", pady=(8, 4))

        legend = tk.Frame(right, bg=PANEL)
        legend.pack(anchor="w", pady=(5, 0))
        self.legend_item(legend, BLUE, "CPU")
        self.legend_item(legend, GREEN, "メモリ")
        self.legend_item(legend, ORANGE, "受信")
        self.legend_item(legend, PURPLE, "送信")

        tk.Label(
            root, text="更新間隔: 1秒  |  Linux / Ubuntu 向け  |  情報の表示のみ",
            font=("Sans", 9), fg="#71849e", bg=BG,
        ).pack(pady=(4, 12))

        self.root.after(500, self.update_metrics)

    def make_info_label(self, parent):
        label = tk.Label(
            parent, text="取得中...", font=("Sans", 9),
            fg="#c6d5e8", bg=PANEL, anchor="w", justify="left",
        )
        label.pack(fill="x", pady=3)
        return label

    def add_metric(self, parent, title, key, color):
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", pady=9)
        top = tk.Frame(row, bg=PANEL)
        top.pack(fill="x")
        tk.Label(
            top, text=title, font=("Sans", 10, "bold"),
            fg=TEXT, bg=PANEL,
        ).pack(side="left")
        value = tk.Label(
            top, text="--%", font=("DejaVu Sans", 12, "bold"),
            fg=color, bg=PANEL,
        )
        value.pack(side="right")
        self.labels[key] = value
        bar = ttk.Progressbar(
            row, maximum=100, mode="determinate",
            style="Monitor.Horizontal.TProgressbar",
        )
        bar.pack(fill="x", pady=(7, 0))
        self.bars[key] = bar

    @staticmethod
    def legend_item(parent, color, name):
        item = tk.Frame(parent, bg=PANEL)
        item.pack(side="left", padx=(0, 12))
        tk.Label(item, text="●", fg=color, bg=PANEL).pack(side="left")
        tk.Label(item, text=name, fg=MUTED, bg=PANEL, font=("Sans", 8)).pack(side="left")

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
    def memory_info():
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
            percent = used / total * 100 if total else 0.0
            return percent, used, total
        except (OSError, ValueError, KeyError):
            return 0.0, 0, 0

    @staticmethod
    def read_network():
        totals = {"rx": 0, "tx": 0}
        try:
            with open("/proc/net/dev", "r", encoding="utf-8") as file:
                for line in file.readlines()[2:]:
                    if ":" not in line:
                        continue
                    interface, data = line.split(":", 1)
                    if interface.strip() == "lo":
                        continue
                    values = data.split()
                    if len(values) >= 9:
                        totals["rx"] += int(values[0])
                        totals["tx"] += int(values[8])
            return totals
        except (OSError, ValueError, IndexError):
            return None

    def network_speeds(self):
        now = time.monotonic()
        current = self.read_network()
        elapsed = max(now - self.previous_time, 0.001)
        self.previous_time = now
        if current is None or self.previous_network is None:
            self.previous_network = current
            return 0.0, 0.0
        rx = max(0, current["rx"] - self.previous_network["rx"]) / elapsed
        tx = max(0, current["tx"] - self.previous_network["tx"]) / elapsed
        self.previous_network = current
        return rx, tx

    @staticmethod
    def read_cpu_temperature():
        # Linux thermal zones and hwmon sensors may expose CPU temperature.
        candidates = glob.glob("/sys/class/thermal/thermal_zone*/temp")
        candidates += glob.glob("/sys/class/hwmon/hwmon*/temp*_input")
        readings = []
        for filename in candidates:
            try:
                with open(filename, "r", encoding="utf-8") as file:
                    raw = int(file.read().strip())
                value = raw / 1000 if raw > 1000 else float(raw)
                if 0 < value < 125:
                    readings.append(value)
            except (OSError, ValueError):
                continue
        return max(readings) if readings else None

    @staticmethod
    def format_bytes(value):
        units = ["B", "KB", "MB", "GB", "TB"]
        amount = float(value)
        for unit in units:
            if amount < 1024 or unit == units[-1]:
                return f"{amount:.1f} {unit}"
            amount /= 1024

    @staticmethod
    def format_gib(kib):
        return f"{kib / 1024 / 1024:.1f} GB"

    def draw_graph(self, canvas, series, colors, maximum=100):
        canvas.delete("all")
        width = max(canvas.winfo_width(), 250)
        height = max(canvas.winfo_height(), 100)
        margin = 24
        graph_height = height - margin * 2
        graph_width = width - margin * 2

        for percent in (0, 25, 50, 75, 100):
            y = margin + graph_height * (1 - percent / 100)
            canvas.create_line(margin, y, width - margin, y, fill="#2b3a50")
            canvas.create_text(
                5, y, text=str(percent), anchor="w",
                fill="#71849e", font=("Sans", 7),
            )

        for values, color in zip(series, colors):
            if len(values) < 2:
                continue
            points = []
            for index, value in enumerate(values):
                x = margin + graph_width * index / (len(values) - 1)
                y = margin + graph_height * (1 - min(value, maximum) / maximum)
                points.extend((x, y))
            canvas.create_line(*points, fill=color, width=2, smooth=True)

    def update_metrics(self):
        cpu = self.cpu_percent()
        memory, memory_used, memory_total = self.memory_info()
        disk = shutil.disk_usage(Path.home())
        disk_percent = disk.used / disk.total * 100 if disk.total else 0
        rx, tx = self.network_speeds()

        for key, value in (("cpu", cpu), ("memory", memory), ("disk", disk_percent)):
            self.labels[key].config(text=f"{value:.1f}%")
            self.bars[key]["value"] = value

        self.history_cpu.append(cpu)
        self.history_memory.append(memory)
        self.history_rx.append(rx / 1024)
        self.history_tx.append(tx / 1024)
        for history in (self.history_cpu, self.history_memory, self.history_rx, self.history_tx):
            del history[:-60]

        temperature = self.read_cpu_temperature()
        if temperature is None:
            temp_text = "CPU温度: センサー情報を取得できません"
        else:
            temp_text = f"CPU温度: {temperature:.1f} °C"
        self.temperature_label.config(text=temp_text)
        self.memory_detail_label.config(
            text=f"メモリ: {self.format_gib(memory_used)} / {self.format_gib(memory_total)}"
        )
        self.disk_detail_label.config(
            text=f"ディスク空き: {self.format_bytes(disk.free)}"
        )

        try:
            with open("/proc/uptime", "r", encoding="utf-8") as file:
                seconds = int(float(file.read().split()[0]))
            hours, remainder = divmod(seconds, 3600)
            self.uptime_label.config(text=f"稼働時間: {hours}時間 {remainder // 60}分")
        except (OSError, ValueError, IndexError):
            self.uptime_label.config(text="稼働時間: 取得できません")

        self.network_label.config(
            text=f"受信 {self.format_bytes(rx)}/s   |   送信 {self.format_bytes(tx)}/s"
        )
        self.draw_graph(
            self.usage_canvas,
            [self.history_cpu, self.history_memory],
            [BLUE, GREEN],
        )
        network_max = max(1024, max(self.history_rx + self.history_tx, default=0) * 1.2)
        self.draw_graph(
            self.network_canvas,
            [self.history_rx, self.history_tx],
            [ORANGE, PURPLE],
            maximum=network_max,
        )
        self.root.after(1000, self.update_metrics)


def main():
    root = tk.Tk()
    SystemMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
