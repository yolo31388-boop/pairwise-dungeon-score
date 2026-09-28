"""副本评分与星级系统 - 含7个bug"""
from dataclasses import dataclass, field

@dataclass
class RunStats:
    duration: float = 0
    deaths: int = 0
    mechanics_done: list = field(default_factory=list)
    mechanics_total: int = 0
    interrupts: int = 0
    dodges: int = 0
    player_count: int = 5

class DungeonScore:
    def __init__(self):
        self.time_thresholds = {1: 600, 2: 480, 3: 360, 4: 240, 5: 120}

    def calculate_score(self, stats: RunStats) -> int:
        # bug1: 只看时间
        for stars, threshold in sorted(self.time_thresholds.items(), reverse=True):
            if stats.duration <= threshold:
                return stars
        return 1

    def get_death_penalty(self, deaths: int) -> int:
        # bug2: 死亡不扣分
        return 0

    def check_mechanics(self, stats: RunStats) -> float:
        # bug3: 不检查机制
        return 1.0

    def get_time_threshold(self, player_count: int, difficulty: str) -> float:
        # bug4: 固定阈值
        return 300.0

    def get_operation_score(self, stats: RunStats) -> int:
        # bug5: 操作不纳入评分
        return 0

    def get_reward_multiplier(self, stars: int) -> float:
        # bug6: 奖励不随星级变化
        return 1.0

    def recalc_on_player_leave(self, stats: RunStats, original_count: int):
        # bug7: 有人退出不调整标准
        pass
