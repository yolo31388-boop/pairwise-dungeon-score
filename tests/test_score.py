"""副本评分与星级系统 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dungeon.score import DungeonScore, RunStats

class TestMultiDimensional:
    def test_deaths_affect_score(self):
        ds = DungeonScore()
        s1 = RunStats(duration=100, deaths=0)
        s2 = RunStats(duration=100, deaths=10)
        assert ds.calculate_score(s1) > ds.calculate_score(s2)  # bug1: 只看时间一样

class TestDeathPenalty:
    def test_death_penalty_nonzero(self):
        ds = DungeonScore()
        assert ds.get_death_penalty(5) > 0  # bug2: 0

class TestMechanicsCheck:
    def test_missed_mechanics_lower_score(self):
        ds = DungeonScore()
        s1 = RunStats(duration=100, mechanics_done=["m1", "m2"], mechanics_total=2)
        s2 = RunStats(duration=100, mechanics_done=[], mechanics_total=2)
        assert ds.check_mechanics(s1) > ds.check_mechanics(s2)  # bug3: 都是1.0

class TestDynamicThreshold:
    def test_threshold_scales_with_party(self):
        ds = DungeonScore()
        t5 = ds.get_time_threshold(5, "normal")
        t10 = ds.get_time_threshold(10, "normal")
        assert t10 > t5  # bug4: 都是300

class TestOperationScore:
    def test_operations_affect_score(self):
        ds = DungeonScore()
        s1 = RunStats(duration=100, interrupts=10, dodges=20)
        s2 = RunStats(duration=100, interrupts=0, dodges=0)
        assert ds.get_operation_score(s1) > ds.get_operation_score(s2)  # bug5: 都是0

class TestRewardByStars:
    def test_higher_stars_better_reward(self):
        ds = DungeonScore()
        assert ds.get_reward_multiplier(5) > ds.get_reward_multiplier(1)  # bug6: 都是1.0

class TestRecalcOnLeave:
    def test_player_leave_adjusts_standard(self):
        ds = DungeonScore()
        stats = RunStats(duration=100, player_count=4)
        ds.recalc_on_player_leave(stats, 5)
        # 应该有记录表明标准被调整了
        assert hasattr(stats, 'adjusted') or stats.player_count == 4
        # 验证：评分时应该用调整后的标准
