"""副本评分与星级系统 - 多维度加权评分"""
from dataclasses import dataclass, field

# 评分维度权重：时间40% + 死亡20% + 机制30% + 操作10%
WEIGHT_TIME = 0.40
WEIGHT_DEATH = 0.20
WEIGHT_MECHANIC = 0.30
WEIGHT_OPERATION = 0.10

# 每个BOSS必须正确处理的关键机制
BOSS_KEY_MECHANICS = {
    "boss1": ["m1", "m2"],
    "boss2": ["m3", "m4"],
    "boss3": ["m5", "m6"],
}

# 难度系数：影响时间基准
DIFFICULTY_FACTOR = {"easy": 1.5, "normal": 1.0, "hard": 0.8, "nightmare": 0.6}

# 操作最低要求（按队伍人数缩放）
MIN_INTERRUPTS_PER_PLAYER = 1
MIN_DODGES_PER_PLAYER = 2

# 死亡降星阈值：死亡数超过 队伍人数*2 直接降星
DEATH_STAR_DROP_FACTOR = 2


@dataclass
class RunStats:
    duration: float = 0
    deaths: int = 0
    mechanics_done: list = field(default_factory=list)
    mechanics_total: int = 0
    interrupts: int = 0
    dodges: int = 0
    player_count: int = 5
    difficulty: str = "normal"
    combos: int = 0


class DungeonScore:
    def __init__(self):
        # 5人普通难度基准时间（秒），星级越高要求越快
        self.base_time_thresholds = {1: 600, 2: 480, 3: 360, 4: 240, 5: 120}
        self.base_player_count = 5
        # 奖励倍率按星级分级，五星有额外奖励和稀有掉落
        self.reward_multipliers = {1: 1.0, 2: 1.2, 3: 1.5, 4: 2.0, 5: 3.0}
        self.five_star_bonus = {"extra_loot": True, "rare_drop": True}

    def get_time_threshold(self, player_count: int, difficulty: str) -> float:
        """按队伍人数和难度动态调整的时间基准（3星标准）"""
        base = self.base_time_thresholds[3]
        party_factor = player_count / self.base_player_count
        diff_factor = DIFFICULTY_FACTOR.get(difficulty, 1.0)
        return base * party_factor * diff_factor

    def _time_score(self, stats: RunStats) -> float:
        """时间维度得分 0.0~1.0，按动态阈值评定"""
        threshold3 = self.get_time_threshold(stats.player_count, stats.difficulty)
        scale = threshold3 / self.base_time_thresholds[3]
        for stars, base in sorted(self.base_time_thresholds.items(), reverse=True):
            if stats.duration <= base * scale:
                return stars / 5.0
        return 0.2

    def get_death_penalty(self, deaths: int) -> int:
        """死亡按比例扣分，每次死亡扣5分（满分100）"""
        return deaths * 5

    def _death_score(self, stats: RunStats) -> float:
        """死亡维度得分 0.0~1.0"""
        penalty = self.get_death_penalty(stats.deaths)
        return max(0.0, (100 - penalty) / 100.0)

    def check_mechanics(self, stats: RunStats) -> float:
        """机制完成度：检查每个BOSS的关键机制是否被正确处理"""
        if stats.mechanics_total <= 0:
            return 1.0
        done = set(stats.mechanics_done)
        # 关键机制缺失直接计为未完成
        key_missed = 0
        key_total = 0
        for boss, keys in BOSS_KEY_MECHANICS.items():
            for key in keys:
                key_total += 1
                if key not in done:
                    key_missed += 1
        completed = len(done)
        ratio = min(1.0, completed / stats.mechanics_total)
        if key_total:
            ratio *= (key_total - key_missed) / key_total
        return ratio

    def get_operation_score(self, stats: RunStats) -> int:
        """操作维度得分 0~100：打断/连击/规避，含最低要求"""
        interrupts = stats.interrupts
        dodges = stats.dodges
        combos = stats.combos
        raw = min(100, interrupts * 5 + dodges * 2 + combos * 3)
        # 最低要求：达不到则操作分打折
        min_interrupts = MIN_INTERRUPTS_PER_PLAYER * stats.player_count
        min_dodges = MIN_DODGES_PER_PLAYER * stats.player_count
        if interrupts < min_interrupts or dodges < min_dodges:
            raw //= 2
        return raw

    def calculate_score(self, stats: RunStats) -> int:
        """多维度加权总分 -> 星级(1~5)"""
        total = (
            self._time_score(stats) * WEIGHT_TIME
            + self._death_score(stats) * WEIGHT_DEATH
            + self.check_mechanics(stats) * WEIGHT_MECHANIC
            + (self.get_operation_score(stats) / 100.0) * WEIGHT_OPERATION
        )
        stars = max(1, min(5, round(total * 5)))
        # 死亡数超过阈值直接降星
        if stats.deaths > stats.player_count * DEATH_STAR_DROP_FACTOR:
            stars = max(1, stars - 1)
        return stars

    def get_reward_multiplier(self, stars: int) -> float:
        """奖励按星级分级"""
        return self.reward_multipliers.get(stars, 1.0)

    def get_rewards(self, stars: int) -> dict:
        """完整奖励：五星有额外奖励和稀有掉落"""
        rewards = {"multiplier": self.get_reward_multiplier(stars)}
        if stars >= 5:
            rewards.update(self.five_star_bonus)
        return rewards

    def recalc_on_player_leave(self, stats: RunStats, original_count: int):
        """成员退出后重新计算评分基准，并记录原始队伍构成"""
        stats.original_player_count = original_count
        stats.adjusted = True
        # 时间基准按剩余人数重新计算（评分时读取 stats.player_count 即新基准）
        stats.adjusted_time_threshold = self.get_time_threshold(
            stats.player_count, stats.difficulty
        )
        return stats
