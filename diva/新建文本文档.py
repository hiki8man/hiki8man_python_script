#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
几何算法性能基准测试
比较叉乘(懒惰)、叉乘(预计算)、Atan2、凸包算法的性能
"""

import math
import time
import random
from dataclasses import dataclass
from functools import cmp_to_key
from typing import List, Tuple, Callable
from collections import Counter

# ==================== 数据结构 ====================

@dataclass(frozen=True)
class Vector:
    """二维向量"""
    x: float
    y: float

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        return Vector(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x - other.x, self.y - other.y)
        return Vector(self.x - other, self.y - other)

    def __mul__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Vector(self.x * scalar, self.y * scalar)
        return NotImplemented

    def __truediv__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Vector(self.x / scalar, self.y / scalar)
        return NotImplemented

    def cross(self, other: 'Vector') -> float:
        """叉积"""
        return self.x * other.y - self.y * other.x

    def dot(self, other: 'Vector') -> float:
        """点积"""
        return self.x * other.x + self.y * other.y

    def length_squared(self) -> float:
        """长度的平方"""
        return self.x * self.x + self.y * self.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"({self.x:.2f}, {self.y:.2f})"


# ==================== 算法实现 ====================

def polar_sort_cross_lazy(points: List[Vector]) -> List[Vector]:
    """
    算法1: 叉积排序 - 边比较边计算（懒惰版本）
    每次比较都重新计算叉积
    """
    if len(points) <= 1:
        return points.copy()

    # 计算质心
    centroid = Vector(0, 0)
    for p in points:
        centroid = centroid + p
    centroid = centroid / len(points)

    def cmp_cross(a: Vector, b: Vector) -> int:
        va = a - centroid
        vb = b - centroid
        cross = va.cross(vb)

        if cross > 0:
            return -1
        if cross < 0:
            return 1

        # 共线时按距离排序
        dist_a = va.length_squared()
        dist_b = vb.length_squared()
        if dist_a < dist_b:
            return -1
        if dist_a > dist_b:
            return 1
        return 0

    result = points.copy()
    result.sort(key=cmp_to_key(cmp_cross))
    return result


def polar_sort_cross_precomputed(points: List[Vector]) -> List[Vector]:
    """
    算法2: 叉积排序 - 预计算所有值
    注意：为了得到角度，内部仍然使用了atan2
    """
    if len(points) <= 1:
        return points.copy()

    # 计算质心
    centroid = Vector(0, 0)
    for p in points:
        centroid = centroid + p
    centroid = centroid / len(points)

    # 预计算角度和距离
    data = []
    for p in points:
        v = p - centroid
        # 计算角度（这里仍然需要atan2）
        angle = math.atan2(v.y, v.x)
        if angle < 0:
            angle += 2 * math.pi
        dist = v.length_squared()
        data.append((p, angle, dist))

    # 排序
    data.sort(key=lambda x: (x[1], x[2]))
    return [x[0] for x in data]


def polar_sort_atan2(points: List[Vector]) -> List[Vector]:
    """
    算法3: Atan2极角排序（标准版本）
    每个点只计算一次角度
    """
    if len(points) <= 1:
        return points.copy()

    # 计算质心
    centroid = Vector(0, 0)
    for p in points:
        centroid = centroid + p
    centroid = centroid / len(points)

    def key_func(p: Vector) -> Tuple[float, float]:
        dx = p.x - centroid.x
        dy = p.y - centroid.y
        angle = math.atan2(dy, dx)
        if angle < 0:
            angle += 2 * math.pi
        dist = dx * dx + dy * dy
        return (angle, dist)

    result = points.copy()
    result.sort(key=key_func)
    return result


def polar_sort_angle_only(points: List[Vector]) -> List[Vector]:
    """
    算法4: 纯角度排序（最快，但共线点顺序不确定）
    不包含距离排序
    """
    if len(points) <= 1:
        return points.copy()

    centroid = Vector(0, 0)
    for p in points:
        centroid = centroid + p
    centroid = centroid / len(points)

    def key_func(p: Vector) -> float:
        dx = p.x - centroid.x
        dy = p.y - centroid.y
        angle = math.atan2(dy, dx)
        return angle if angle >= 0 else angle + 2 * math.pi

    result = points.copy()
    result.sort(key=key_func)
    return result


def convex_hull(points: List[Vector]) -> List[Vector]:
    """
    算法5: Andrew单调链凸包算法
    返回最小凸包
    """
    if len(points) <= 1:
        return points.copy()

    def cross(o: Vector, a: Vector, b: Vector) -> float:
        return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)

    sorted_points = sorted(points, key=lambda p: (p.x, p.y))

    # 下凸包
    lower = []
    for p in sorted_points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    # 上凸包
    upper = []
    for p in reversed(sorted_points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


# ==================== 数据生成器 ====================

class DataGenerator:
    """测试数据生成器"""

    @staticmethod
    def random_points(count: int, x_range: Tuple[float, float] = (0, 1000),
                      y_range: Tuple[float, float] = (0, 1000)) -> List[Vector]:
        """生成随机点"""
        random.seed(42)
        points = []
        for _ in range(count):
            x = random.uniform(*x_range)
            y = random.uniform(*y_range)
            points.append(Vector(x, y))
        return points

    @staticmethod
    def circle_points(count: int, radius: float = 500,
                      center: Tuple[float, float] = (500, 500)) -> List[Vector]:
        """生成圆形分布的点"""
        points = []
        for i in range(count):
            angle = 2 * math.pi * i / count
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            points.append(Vector(x, y))
        return points

    @staticmethod
    def line_points(count: int, x1: float = 0, y1: float = 0,
                    x2: float = 1000, y2: float = 1000,
                    noise: float = 1.0) -> List[Vector]:
        """生成直线分布的点（带噪声）"""
        random.seed(42)
        points = []
        for i in range(count):
            t = i / (count - 1) if count > 1 else 0
            x = x1 + (x2 - x1) * t + random.uniform(-noise, noise)
            y = y1 + (y2 - y1) * t + random.uniform(-noise, noise)
            points.append(Vector(x, y))
        return points

    @staticmethod
    def grid_points(cols: int, rows: int,
                    spacing: float = 100) -> List[Vector]:
        """生成网格点"""
        points = []
        for i in range(cols):
            for j in range(rows):
                points.append(Vector(i * spacing, j * spacing))
        return points


# ==================== 正确性验证 ====================

def verify_correctness():
    """验证各算法的正确性"""
    print("=" * 60)
    print("正确性验证")
    print("=" * 60)

    test_cases = [
        ("正方形", [Vector(0, 0), Vector(1, 0), Vector(1, 1), Vector(0, 1)]),
        ("三角形", [Vector(0, 0), Vector(1, 0), Vector(0, 1)]),
        ("共线点", [Vector(0, 0), Vector(1, 0), Vector(2, 0), Vector(3, 0)]),
        ("重复点", [Vector(0, 0), Vector(1, 1), Vector(0, 0), Vector(2, 2)]),
    ]

    algorithms = [
        ("叉乘(懒惰)", polar_sort_cross_lazy),
        ("叉乘(预计算)", polar_sort_cross_precomputed),
        ("Atan2", polar_sort_atan2),
        ("纯角度", polar_sort_angle_only),
        ("凸包", convex_hull),
    ]

    for name, points in test_cases:
        print(f"\n测试: {name} - {len(points)}个点")
        print(f"  原始: {points}")

        for algo_name, algo_func in algorithms:
            try:
                result = algo_func(points)
                print(f"  {algo_name:12}: {result}")
            except Exception as e:
                print(f"  {algo_name:12}: ❌ 错误 - {e}")

    print()


# ==================== 性能基准测试 ====================

def run_benchmark():
    """运行性能基准测试"""
    print("=" * 60)
    print("性能基准测试")
    print("=" * 60)

    sizes = [10, 50, 100, 500, 1000, 2000, 5000]

    algorithms = [
        ("叉乘(懒惰)", polar_sort_cross_lazy),
        ("叉乘(预计算)", polar_sort_cross_precomputed),
        ("Atan2", polar_sort_atan2),
        ("纯角度", polar_sort_angle_only),
        ("凸包", convex_hull),
    ]

    # 打印表头
    print(f"\n{'数据量':<8}", end="")
    for name, _ in algorithms:
        print(f"{name:>16}", end="")
    print()
    print("-" * (8 + 16 * len(algorithms)))

    # 运行测试
    for n in sizes:
        points = DataGenerator.random_points(n)
        print(f"{n:<8}", end="")

        for name, algo_func in algorithms:
            # 预热
            for _ in range(3):
                algo_func(points)

            # 正式测试 - 运行10次取平均
            start = time.perf_counter()
            for _ in range(10):
                algo_func(points)
            elapsed = (time.perf_counter() - start) / 10 * 1000  # 转换为毫秒

            print(f"{elapsed:>15.3f}ms", end="")
        print()

    print()


# ==================== 详细性能分析 ====================

def run_detailed_analysis():
    """运行详细性能分析"""
    print("=" * 60)
    print("详细性能分析")
    print("=" * 60)

    n = 1000
    points = DataGenerator.random_points(n)

    algorithms = [
        ("叉乘(懒惰)", polar_sort_cross_lazy),
        ("叉乘(预计算)", polar_sort_cross_precomputed),
        ("Atan2", polar_sort_atan2),
        ("纯角度", polar_sort_angle_only),
        ("凸包", convex_hull),
    ]

    print(f"\n测试数据量: {n} 个点\n")

    # 预热
    for _, algo_func in algorithms:
        algo_func(points)

    # 详细测试
    results = {}
    for name, algo_func in algorithms:
        times = []
        for i in range(20):
            start = time.perf_counter()
            algo_func(points)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg = sum(times) / len(times)
        min_t = min(times)
        max_t = max(times)
        std = math.sqrt(sum((t - avg) ** 2 for t in times) / len(times))

        results[name] = {
            'avg': avg,
            'min': min_t,
            'max': max_t,
            'std': std,
            'times': times
        }

        print(f"{name}:")
        print(f"  平均: {avg:.3f}ms")
        print(f"  最小: {min_t:.3f}ms")
        print(f"  最大: {max_t:.3f}ms")
        print(f"  标准差: {std:.3f}ms")
        print()

    # 相对性能对比
    base_avg = results["叉乘(懒惰)"]['avg']
    print("相对性能（基准: 叉乘懒惰 = 1.0x）:")
    for name, data in results.items():
        ratio = data['avg'] / base_avg
        speedup = base_avg / data['avg']
        print(f"  {name:12}: {ratio:.3f}x  (速度提升 {speedup:.2f}x)")
    print()


# ==================== 算法特性对比 ====================

def compare_algorithm_characteristics():
    """对比算法特性"""
    print("=" * 60)
    print("算法特性对比")
    print("=" * 60)

    # 测试各种特殊数据
    test_configs = [
        ("随机点", DataGenerator.random_points(100)),
        ("圆形", DataGenerator.circle_points(100)),
        ("直线", DataGenerator.line_points(100)),
        ("网格", DataGenerator.grid_points(10, 10)),
    ]

    algorithms = [
        ("叉乘(懒惰)", polar_sort_cross_lazy),
        ("叉乘(预计算)", polar_sort_cross_precomputed),
        ("Atan2", polar_sort_atan2),
        ("纯角度", polar_sort_angle_only),
        ("凸包", convex_hull),
    ]

    print("\n各算法在不同数据类型下的表现 (100个点, 毫秒):")
    print(f"{'数据类型':<12}", end="")
    for name, _ in algorithms:
        print(f"{name:>14}", end="")
    print()
    print("-" * (12 + 14 * len(algorithms)))

    for data_name, points in test_configs:
        print(f"{data_name:<12}", end="")

        for algo_name, algo_func in algorithms:
            start = time.perf_counter()
            for _ in range(100):  # 运行100次取平均
                algo_func(points)
            elapsed = (time.perf_counter() - start) / 100 * 1000
            print(f"{elapsed:>13.3f}ms", end="")
        print()

    print()


# ==================== 主程序 ====================

def main():
    """主程序入口"""
    print("\n" + "=" * 60)
    print("几何算法性能基准测试套件")
    print("=" * 60 + "\n")

    # 1. 正确性验证
    verify_correctness()

    # 2. 性能基准测试
    run_benchmark()

    # 3. 详细性能分析
    run_detailed_analysis()

    # 4. 算法特性对比
    compare_algorithm_characteristics()

    print("=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()