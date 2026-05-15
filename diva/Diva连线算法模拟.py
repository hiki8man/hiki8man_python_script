
from dataclasses import dataclass
import math
from enum import Enum
from collections import Counter
from turtle import right
from functools import cmp_to_key

class Shape(Enum):
    POLYGON = 0
    LINE = 1
    POINT = -1

@dataclass(frozen=True)
class Vector:
    x:float
    y:float

    def __add__(self, other) -> "Vector":
        # a + b
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        elif isinstance(other, (int, float)):
            return Vector(self.x + other, self.y + other)
        else:
            raise TypeError()
    def __sub__(self, other) -> "Vector":
        # a - b
        if isinstance(other, Vector):
            return Vector(self.x - other.x, self.y - other.y)
        elif isinstance(other, (int, float)):
            return Vector(self.x - other, self.y - other)
        else:
            raise TypeError()

    def __truediv__(self, other) -> "Vector":
        # a / b
        if isinstance(other, (int, float)):
            return Vector(self.x / other, self.y / other)
        else:
            raise TypeError()

    def dot(self, other) -> float:
        # a.b
        if isinstance(other, Vector):
            return self.x * other.x + self.y * other.y
        else:
            raise TypeError()
    
    def cross(self, other) -> float:
        # a.b
        if isinstance(other, Vector):
            return self.x * other.y - self.y * other.x
        else:
            raise TypeError()
    
    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))

def get_shape_type(multi_note: list[Vector]) -> Shape:
    same_count_dict = Counter(multi_note)

    is_line = True
    is_same = False
    diva_check = False

    note_pre2: None|Vector = multi_note[0]
    note_pre1: None|Vector = multi_note[1]

    for i in range(2, len(multi_note)):
        note_cur = multi_note[i]
        if is_line:
            vet1 = note_pre1 - note_pre2
            vet2 = note_cur - note_pre2
            is_line = (vet1.cross(vet2) == 0)
        else:
            break
        
    if len(same_count_dict) == 1:
        is_same = True
    
    if len(same_count_dict) == 2:
        single:None|Vector = None
        multi:None|Vector = None

        keys:list[Vector] = list(same_count_dict.keys())
        
        if same_count_dict[keys[0]] > same_count_dict[keys[1]]:
            single, multi = keys[1], keys[0]
            
        elif same_count_dict[keys[0]] < same_count_dict[keys[1]]:
            single, multi = keys[0], keys[1]

        if isinstance(single, Vector) and isinstance(multi, Vector):
            diva_check = (multi.y - single.y) < 0

    if is_line == False and is_same == False:
        return Shape.POLYGON

    elif diva_check:
        return Shape.POLYGON

    elif is_same:
        return Shape.POINT

    else:
        return Shape.LINE

def polar_angle_sort(multi_note: list[Vector]) -> list[Vector]:
    count = len(multi_note)
    centorid = Vector(0,0)

    for note in multi_note:
        centorid = centorid + note
    centorid = centorid / count

    def sorted_func(note) -> float:
        angle = math.atan2(note.y - centorid.y, note.x - centorid.x)
        if angle < 0:
            return angle + 2 * math.pi

        return angle

    multi_note.sort(key=sorted_func) 

    return multi_note

def polar_angle_sort_cross(multi_note: list[Vector]) -> list[Vector]:
    count = len(multi_note)
    centorid = Vector(0,0)

    for note in multi_note:
        centorid = centorid + note
    centorid = centorid / count

    def sorted_func(note):
        angle = math.atan2(note.y - centorid.y, note.x - centorid.x)
        if angle < 0:
            return angle + 2 * math.pi

        return angle


    same_note = [note for note in multi_note if note == centorid]
    other_note = [note for note in multi_note if note != centorid]

    other_note =  sorted(other_note, key=sorted_func)

    return same_note + other_note

def multi_connect(multi_note: list[Vector]):
    # 多押连接线调用函数
    multi_count = len(multi_note)

    if multi_count < 2:
        # 错误情况，不执行操作
        pass
    
    shape_type = get_shape_type(multi_note)

    if shape_type == Shape.LINE:
        multi_note.sort(key=lambda x: (x.x, x.y))
        return multi_note

    elif shape_type == Shape.POINT:
        multi_note.append(multi_note[0])
        return multi_note

    elif multi_count < 4:
        # 能确定情况的直接按默认顺序连接
        multi_note.append(multi_note[0])
        return multi_note

    else:
        multi_note = polar_angle_sort(multi_note)
        multi_note.append(multi_note[0])
        return multi_note

# ==================== Tkinter 可视化部分 ====================
# 让AI帮我写了下，不是很想自己写（
from operator import truediv
import re
from collections import deque
import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext

TARGET_BLOCK_RE = re.compile(r"Target\s*\{([^}]*)\}\s*;", re.IGNORECASE)


def parse_target_xy_updates(raw: str) -> tuple[dict[int, Vector], list[str]]:
    """
    从文本中解析所有 `Target { ... };` 行，读取大括号内第 2 个数为点序号、
    第 7、8 个数为 X、Y。重复序号时后者覆盖前者，并产生提示信息。
    返回 (序号 -> 坐标, 提示/警告列表)。
    """
    updates_map: dict[int, Vector] = {}
    notes: list[str] = []

    for line_no, line in enumerate(raw.splitlines(), start=1):
        m = TARGET_BLOCK_RE.search(line)
        if not m:
            continue
        tokens = m.group(1).strip().split()
        if len(tokens) < 8:
            notes.append(f"第 {line_no} 行: 大括号内至少需要 8 个参数")
            continue
        try:
            idx = int(float(tokens[1]))
        except ValueError:
            notes.append(f"第 {line_no} 行: 第 2 个参数不是有效的点序号")
            continue
        try:
            x = float(tokens[6])
            y = float(tokens[7])
        except ValueError:
            notes.append(f"第 {line_no} 行: 第 7、8 个参数不是有效数字")
            continue
        if idx in updates_map:
            notes.append(f"第 {line_no} 行: 点序号 {idx} 重复，已采用本行坐标")
        updates_map[idx] = Vector(x, y)

    return updates_map, notes


def parse_points(text: str) -> list[Vector]:
    """将输入字符串解析为Vector列表，格式：x1,y1;x2,y2;..."""
    points = []
    for part in text.split(';'):
        part = part.strip()
        if not part:
            continue
        try:
            x_str, y_str = part.split(',')
            x = float(x_str.strip())
            y = float(y_str.strip())
            points.append(Vector(x, y))
        except ValueError:
            raise ValueError(f"坐标格式错误: '{part}'，应为 x,y")
    return points

class App:
    # 控制点在画布上的半径（像素）
    POINT_RADIUS = 12
    # 点击选中控制点的判定半径（略大于圆，方便拖）
    HIT_RADIUS = 22

    @staticmethod
    def _vertex_label(index: int) -> str:
        if index < 26:
            return chr(ord("A") + index)
        return f"P{index + 1}"

    # 逻辑坐标上视为「同一点」的误差（用于错开名称标注）
    LOGICAL_COINCIDE_EPS = 1e-4
    # 重合时名称在画布上纵向错开的步长（像素）
    LABEL_STACK_STEP = 18

    @classmethod
    def _coincident_label_stack(cls, points: list[Vector]) -> list[int]:
        """第 i 个点与前面若干点逻辑重合时，返回纵向错开档位 0,1,2…（避免字母叠字）。"""
        n = len(points)
        stacks: list[int] = []
        for i in range(n):
            k = 0
            for j in range(i):
                if (
                    abs(points[i].x - points[j].x) <= cls.LOGICAL_COINCIDE_EPS
                    and abs(points[i].y - points[j].y) <= cls.LOGICAL_COINCIDE_EPS
                ):
                    k += 1
            stacks.append(k)
        return stacks

    def __init__(self, root):
        self.root = root
        root.title("多押连接可视化")
        root.geometry("1650x800")
        root.resizable(False, False)

        self._drag_index: int | None = None
        self.logical_points: list[Vector] = []

        # ---------- 左侧画布 1280x720 ----------
        self.canvas = tk.Canvas(root, width=1280, height=720, bg='white')
        self.canvas.place(x=20, y=20)
        self.canvas.bind("<Button-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

        # ---------- 右侧控制面板 ----------
        control_frame = tk.Frame(root, width=600, height=1080, bg='#f0f0f0')
        control_frame.place(x=1320, y=20)

        tk.Label(control_frame, text="输入点 (格式: x1,y1; x2,y2; ...)", 
                 font=('Arial', 12), bg='#f0f0f0').pack(pady=(20, 5), anchor='w')

        self.entry_text = tk.StringVar()
        self.entry = tk.Entry(control_frame, textvariable=self.entry_text,
                              font=('Consolas', 10), width=50)
        self.entry.pack(pady=5, padx=10)
        self.entry.insert(0, "192,576; 192,480; 576,480; 576,576")

        tk.Button(control_frame, text="更新绘制", command=self.update_canvas,
                  font=('Arial', 12, 'bold'), bg='#4CAF50', fg='white',
                  width=12).pack(pady=15)

        tk.Label(
            control_frame,
            text="连接顺序（与画布蓝线、线段旁数字一致）",
            font=("Arial", 11, "bold"),
            bg="#f0f0f0",
        ).pack(pady=(4, 2), padx=10, anchor="w")
        self.order_label = tk.Label(
            control_frame,
            text="",
            font=("Arial", 10),
            bg="#f0f0f0",
            justify="left",
            wraplength=520,
        )
        self.order_label.pack(pady=(0, 8), padx=10, anchor="w")

        tk.Label(
            control_frame,
            text="Target 区（由你编辑，程序不会改写）：\n"
                 "大括号内第 2 个数为点序号（0=A…），第 7、8 个数为 X、Y。\n"
                 "点「从 Target 同步到点」后，坐标会应用到画布与上方输入框。",
            font=("Arial", 10),
            bg="#f0f0f0",
            justify="left",
        ).pack(pady=(10, 4), padx=10, anchor="w")

        self.target_text = scrolledtext.ScrolledText(
            control_frame,
            height=9,
            width=52,
            font=("Consolas", 9),
            wrap=tk.NONE,
        )
        self.target_text.pack(pady=4, padx=10, fill="x")
        sample_targets = (
            "Target { 192 3 1 0 0 0 816.00 528.00 135.00 0.00 500.00 880.00 };\n"
            "Target { 192 2 1 0 0 0 240.00 768.00 -135.00 0.00 500.00 880.00 };\n"
            "Target { 192 1 1 0 0 0 240.00 528.00 45.00 0.00 500.00 880.00 };\n"
            "Target { 192 0 1 0 0 0 240.00 288.00 -45.00 0.00 500.00 880.00 };"
        )
        self.target_text.insert("1.0", sample_targets)

        tk.Button(
            control_frame,
            text="从 Target 第7、8参数同步到点",
            command=self.sync_points_from_target_text,
            font=("Arial", 11, "bold"),
            bg="#2196F3",
            fg="white",
            width=28,
        ).pack(pady=8)

        # 显示缩放信息
        self.info_label = tk.Label(control_frame, text="", bg='#f0f0f0', font=('Arial', 10), justify='left')
        self.info_label.pack(pady=10, padx=10, anchor='w')

        self.update_canvas()

    @classmethod
    def _same_pt(cls, a: Vector, b: Vector) -> bool:
        e = cls.LOGICAL_COINCIDE_EPS
        return abs(a.x - b.x) <= e and abs(a.y - b.y) <= e

    @classmethod
    def _coincidence_index_deques(cls, points: list[Vector]) -> list[deque[int]]:
        """将下标按「逻辑坐标重合」分组，每组内按输入顺序排列，供映射 multi_connect 序列。"""
        classes: list[list[int]] = []
        for i in range(len(points)):
            placed = False
            for grp in classes:
                if any(cls._same_pt(points[i], points[j]) for j in grp):
                    grp.append(i)
                    placed = True
                    break
            if not placed:
                classes.append([i])
        return [deque(sorted(g)) for g in classes]

    @classmethod
    def ordered_vertex_indices(cls, points: list[Vector], ordered: list[Vector]) -> list[int]:
        """
        将 multi_connect 输出的几何点序列还原为原始顶点下标。
        坐标重合时按输入顺序依次「消耗」同位置的顶点，避免 points.index 总命中第一个。
        若序列首尾闭合（末点与首点同坐标），最后一步映射回路径起点下标。
        """
        deques = cls._coincidence_index_deques(points)
        n_o = len(ordered)
        closed = n_o >= 2 and cls._same_pt(ordered[-1], ordered[0])

        def take(p: Vector) -> int:
            for dq in deques:
                if not dq:
                    continue
                j = dq[0]
                if cls._same_pt(p, points[j]):
                    return dq.popleft()
            raise ValueError(
                "无法将连线序列中的坐标匹配到当前顶点（请检查点集是否与算法输出一致）。"
            )

        out: list[int] = []
        if closed:
            for t in range(n_o - 1):
                out.append(take(ordered[t]))
            out.append(out[0])
        else:
            for t in range(n_o):
                out.append(take(ordered[t]))
        return out

    @staticmethod
    def _nearest_vertex_index(points: list[Vector], p: Vector) -> int:
        """当精确匹配失败时，取与 p 欧氏距离最近的顶点下标（避免 points.index 抛错）。"""
        best_i = 0
        best_d = float("inf")
        for i, q in enumerate(points):
            d = (p.x - q.x) ** 2 + (p.y - q.y) ** 2
            if d < best_d:
                best_d = d
                best_i = i
        return best_i

    def _connect_rule_caption(self, points: list[Vector]) -> str:
        """与 multi_connect 分支一致的文字说明。"""
        n = len(points)
        if n < 2:
            return "点数不足 2，无连线规则。"
        shape_type = get_shape_type(points)
        if shape_type == Shape.POINT:
            return (
                "规则：所有点坐标相同（多压重合）。按输入顺序依次经过各顶点，最后回到第一个顶点。\n"
                "说明：同一坐标上的多个顶点在顺序说明里按 A、B、C… 输入顺序依次出现。"
            )
        if shape_type == Shape.LINE:
            return (
                "规则：各点共线且并非全部重合。按 (x,y) 字典序排序后依次连接；"
                "此分支末尾不自动连回首点。"
            )
        if n < 4:
            return "规则：少于 4 个点。按输入顺序连接，并回到第一个顶点。"
        return (
            "规则：4 个及以上且不全部重合。按围绕质心的极角排序后连接，"
            "并回到排序后的第一个顶点。"
        )

    def _connect_order_texts(
        self, points: list[Vector], ordered: list[Vector] | None
    ) -> tuple[str, str]:
        """根据 multi_connect 的结果返回 (顶点字母链, 规则与线段说明)。"""
        if not ordered:
            return "（无）", "点数不足，无法生成连接顺序。"

        try:
            indices = self.ordered_vertex_indices(points, ordered)
        except ValueError as e:
            return "（匹配失败）", str(e)

        chain = " → ".join(self._vertex_label(i) for i in indices)
        rule = self._connect_rule_caption(points)

        seg_detail = "\n线段（与画布上蓝色数字一致）："
        for k in range(len(indices) - 1):
            a = self._vertex_label(indices[k])
            b = self._vertex_label(indices[k + 1])
            seg_detail += f"\n  {k + 1}. {a} → {b}"

        return chain, rule + seg_detail

    def _sync_entry_from_points(self) -> None:
        parts = []
        for p in self.logical_points:
            if abs(p.x - round(p.x)) < 1e-6 and abs(p.y - round(p.y)) < 1e-6:
                parts.append(f"{int(round(p.x))},{int(round(p.y))}")
            else:
                parts.append(f"{p.x:.4g},{p.y:.4g}")
        self.entry_text.set("; ".join(parts))

    def _find_hit(self, mx: float, my: float, canvas_points: list[Vector]) -> int | None:
        best_i: int | None = None
        best_d2 = self.HIT_RADIUS * self.HIT_RADIUS
        for i, cp in enumerate(canvas_points):
            dx, dy = mx - cp.x, my - cp.y
            d2 = dx * dx + dy * dy
            if d2 <= best_d2:
                best_d2 = d2
                best_i = i
        return best_i

    def _on_canvas_press(self, event: tk.Event) -> None:
        if len(self.logical_points) < 2:
            return
        scale, off_x, off_y = self.compute_transform(self.logical_points)
        cps = [Vector(*self.to_canvas(p, scale, off_x, off_y)) for p in self.logical_points]
        self._drag_index = self._find_hit(event.x, event.y, cps)

    def _on_canvas_drag(self, event: tk.Event) -> None:
        if self._drag_index is None:
            return
        scale, off_x, off_y = self.compute_transform(self.logical_points)
        if scale == 0:
            return
        lx = (event.x - off_x) / scale
        ly = (event.y - off_y) / scale
        self.logical_points[self._drag_index] = Vector(lx, ly)
        self._sync_entry_from_points()
        self._draw()

    def _on_canvas_release(self, _event: tk.Event) -> None:
        self._drag_index = None

    def sync_points_from_target_text(self) -> None:
        """读取 Target 文本中每行第 7、8 参数，写回 logical_points（不修改 Target 文本）。"""
        if not self.logical_points:
            messagebox.showwarning("提示", "请先「更新绘制」载入点（至少 2 个），再同步 Target。")
            return

        raw = self.target_text.get("1.0", "end")
        updates, parse_notes = parse_target_xy_updates(raw)
        if not updates:
            messagebox.showinfo(
                "提示",
                "未在 Target 区解析到有效行（需含 `Target { ... };`，且大括号内至少 8 个参数）。",
            )
            return

        n = len(self.logical_points)
        range_errs: list[str] = []
        applied = 0
        for idx, v in updates.items():
            if idx < 0 or idx >= n:
                range_errs.append(f"点序号 {idx} 超出当前点数 {n}（当前为 0…{n - 1}）")
                continue
            self.logical_points[idx] = Vector(v.x, v.y)
            applied += 1

        self._sync_entry_from_points()
        self._draw()

        all_notes = parse_notes + range_errs
        if range_errs or (parse_notes and applied == 0):
            messagebox.showwarning(
                "同步结果",
                f"已写入 {applied} 个点的坐标。\n\n"
                + "\n".join(all_notes[:14])
                + ("\n…" if len(all_notes) > 14 else ""),
            )
        elif parse_notes:
            messagebox.showinfo(
                "同步完成",
                f"已写入 {applied} 个点的坐标。\n\n"
                + "\n".join(parse_notes[:10])
                + ("\n…" if len(parse_notes) > 10 else ""),
            )
        else:
            messagebox.showinfo("同步完成", f"已写入 {applied} 个点的坐标。")

    def compute_transform(self, points):
        """根据点集计算缩放和平移参数，使点适配 1280x720 画布"""
        if not points:
            return 1, 0, 0

        else:
            return 2/3, 0, 0

    def to_canvas(self, point, scale, offset_x, offset_y):
        """将原始点转换为画布坐标"""
        x = point.x * scale + offset_x
        y = point.y * scale + offset_y
        return x, y

    def update_canvas(self):
        """从输入框读取点，再重绘"""
        try:
            points = parse_points(self.entry_text.get())
        except ValueError as e:
            messagebox.showerror("输入错误", str(e))
            return

        if len(points) < 2:
            messagebox.showinfo("提示", "至少需要两个点")
            return

        self.logical_points = list(points)
        self._draw()

    def _draw(self) -> None:
        """按 self.logical_points 重绘画布（供「更新绘制」与鼠标拖动共用）"""
        self.canvas.delete("all")
        points = self.logical_points
        if len(points) < 2:
            self.order_label.config(text="至少需要两个点。")
            return

        scale, off_x, off_y = self.compute_transform(points)
        canvas_points = [Vector(*self.to_canvas(p, scale, off_x, off_y)) for p in points]

        ordered = multi_connect([Vector(p.x, p.y) for p in points])
        ordered_canvas: list[Vector] = []
        if ordered is not None:
            try:
                idx_path = self.ordered_vertex_indices(points, ordered)
                ordered_canvas = [canvas_points[i] for i in idx_path]
            except ValueError:
                for p in ordered:
                    j = self._nearest_vertex_index(points, p)
                    ordered_canvas.append(canvas_points[j])

        chain, rule = self._connect_order_texts(points, ordered)
        self.order_label.config(text=f"顺序：{chain}\n\n{rule}")

        r = self.POINT_RADIUS
        label_stack = self._coincident_label_stack(points)
        step = self.LABEL_STACK_STEP
        for i, cp in enumerate(canvas_points):
            self.canvas.create_oval(
                cp.x - r, cp.y - r, cp.x + r, cp.y + r,
                fill="red", outline="black", width=2,
            )
            lbl = self._vertex_label(i)
            dy = label_stack[i] * step
            self.canvas.create_text(
                cp.x + r + 8,
                cp.y + dy,
                text=lbl,
                anchor="w",
                font=("Arial", 16, "bold"),
                fill="black",
            )

        if ordered_canvas:
            n = len(ordered_canvas)
            for i in range(n - 1):
                p1 = ordered_canvas[i]
                p2 = ordered_canvas[i + 1]
                self.canvas.create_line(p1.x, p1.y, p2.x, p2.y,
                                        fill='blue', width=2)
                mid_x = (p1.x + p2.x) / 2
                mid_y = (p1.y + p2.y) / 2
                offset = 12
                self.canvas.create_text(mid_x + offset, mid_y + offset,
                                        text=str(i + 1),
                                        font=('Arial', 11, 'bold'),
                                        fill='darkblue')

        self.info_label.config(
            text=f"缩放比例: {scale:.4f}\n"
                 f"偏移: ({off_x:.1f}, {off_y:.1f})\n"
                 f"原始点范围: X[{min(p.x for p in points):.1f}, {max(p.x for p in points):.1f}] "
                 f"Y[{min(p.y for p in points):.1f}, {max(p.y for p in points):.1f}]\n"
                 f"提示: 拖动红点可改点（不改 Target）；改 Target 后点「从 Target 同步到点」。"
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

