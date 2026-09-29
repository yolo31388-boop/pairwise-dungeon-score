"""副本评分与星级系统 - 多维度加权评分"""
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
    difficulty: str = "normal"
    combos: int = 0
    original_player_count: int = 0
    adjusted: bool = False

class DungeonScore:
    # 多维加权: 时间40% + 死亡20% + 机制30% + 操作10%
    WEIGHT_TIME = 0.4
    WEIGHT_DEATH = 0.2
    WEIGHT_MECHANICS = 0.3
    WEIGHT_OPERATION = 0.1

    STAR_THRESHOLDS = [(90, 5), (75, 4), (60, 3), (40, 2), (0, 1)]

    # 时间基准: 每人60秒, 按难度缩放
    BASE_TIME_PER_PLAYER = 60.0
    DIFFICULTY_MULTIPLIERS = {
        "easy": 1.5,
        "normal": 1.0,
        "hard": 0.8,
        "heroic": 0.6,
    }

    # 死亡: 每次死亡扣10分, 死亡人数超过队伍人数直接降星
    DEATH_PENALTY_PER_DEATH = 10

    # 操作最低要求: 低于该分数最高只能3星
    MIN_OPERATION_SCORE = 20
    MIN_OPERATION_STARS_CAP = 3

    # 奖励按星级分级, 五星有额外奖励和稀有掉落
    REWARD_MULTIPLIERS = {1: 1.0, 2: 1.2, 3: 1.5, 4: 2.0, 5: 3.0}
    FIVE_STAR_BONUS = 0.5

    def __init__(self):
        self.time_thresholds = {1: 600, 2: 480, 3: 360, 4: 240, 5: 120}

    def calculate_score(self, stats: RunStats) -> int:
        time_score = self.get_time_score(stats)
        death_score = 100 - self.get_death_penalty(stats.deaths)
        mechanics_score = self.check_mechanics(stats) * 100
        operation_score = self.get_operation_score(stats)

        total = (
            time_score * self.WEIGHT_TIME
            + death_score * self.WEIGHT_DEATH
            + mechanics_score * self.WEIGHT_MECHANICS
            + operation_score * self.WEIGHT_OPERATION
        )

        stars = 1
        for threshold, star in self.STAR_THRESHOLDS:
            if total >= threshold:
                stars = star
                break

        # 死亡人数超过队伍人数, 直接降星
        if stats.deaths > stats.player_count:
            stars = min(stars, 2)

        # 操作数据有最低要求
        if operation_score < self.MIN_OPERATION_SCORE:
            stars = min(stars, self.MIN_OPERATION_STARS_CAP)

        return stars

    def get_time_score(self, stats: RunStats) -> float:
        threshold = self.get_time_threshold(stats.player_count, stats.difficulty)
        if stats.duration <= 0:
            return 100.0
        return max(0.0, min(100.0, 100.0 * threshold / stats.duration))

    def get_death_penalty(self, deaths: int) -> int:
        return min(100, max(0, deaths) * self.DEATH_PENALTY_PER_DEATH)

    def check_mechanics(self, stats: RunStats) -> float:
        if stats.mechanics_total <= 0:
            return 1.0
        done = min(len(stats.mechanics_done), stats.mechanics_total)
        return done / stats.mechanics_total

    def get_time_threshold(self, player_count: int, difficulty: str) -> float:
        base = self.BASE_TIME_PER_PLAYER * max(1, player_count)
        multiplier = self.DIFFICULTY_MULTIPLIERS.get(difficulty, 1.0)
        return base * multiplier

    def get_operation_score(self, stats: RunStats) -> int:
        players = max(1, stats.player_count)
        expected_interrupts = players * 2
        expected_dodges = players * 4
        expected_combos = players * 3
        score = (
            40 * min(1.0, stats.interrupts / expected_interrupts)
            + 40 * min(1.0, stats.dodges / expected_dodges)
            + 20 * min(1.0, stats.combos / expected_combos)
        )
        return int(score)

    def get_reward_multiplier(self, stars: int) -> float:
        return self.REWARD_MULTIPLIERS.get(stars, 1.0)

    def get_rewards(self, stars: int) -> dict:
        rewards = {
            "multiplier": self.get_reward_multiplier(stars),
            "bonus": 0.0,
            "rare_drop": False,
        }
        if stars >= 5:
            rewards["bonus"] = self.FIVE_STAR_BONUS
            rewards["rare_drop"] = True
        return rewards

    def recalc_on_player_leave(self, stats: RunStats, original_count: int):
        # 记录原始队伍构成, 评分基准按当前人数动态重算
        stats.original_player_count = original_count
        stats.adjusted = True
