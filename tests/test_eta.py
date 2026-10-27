"""Pure-stdlib ETA boundary checks; no pytest runner, torch, simulation or GPU."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from monitoring.eta import estimate


class TrainingEtaTests(unittest.TestCase):
    def calculate(self, **overrides):
        arguments = dict(samples=[(900+i,i/2) for i in range(0,501,10)],
            args={"iterations":2000,"wm_only_iters":500},
            status={"status":"running","stage":"policy_bptt","started_at":1000},
            launch={"max_seconds":6600},log_mtime=1598,now=1600)
        arguments.update(overrides)
        return estimate(**arguments)

    def test_recent_window_iteration_goal_first(self):
        p = self.calculate()
        self.assertEqual(p["window_iterations"],500)
        self.assertEqual(p["recent_iterations_per_minute"],120)
        self.assertEqual(p["predicted_stop"],"iterations")
        self.assertEqual(p["eta_seconds"],298)
        self.assertEqual(p["estimated_finish_at"],1898)
        self.assertEqual(p["iteration_percent"],70)

    def test_time_budget_first(self):
        p = self.calculate(launch={"max_seconds":700})
        self.assertEqual(p["predicted_stop"],"time_limit")
        self.assertEqual(p["eta_seconds"],100)
        self.assertEqual(p["estimated_finish_at"],1700)

    def test_postprocessing_does_not_extend_training_time(self):
        p = self.calculate(now=3000,status={"status":"running","stage":"evaluation","started_at":1000},
            summary={"started_at":1000,"finished_at":1601,"completed":True})
        self.assertEqual(p["training_elapsed_seconds"],601)
        self.assertEqual(p["actual_finished_at"],1601)
        self.assertIsNone(p["eta_seconds"])

    def test_historical_controller_elapsed_precedes_pipeline_completion(self):
        p = self.calculate(now=5000,status={"status":"completed","stage":"finished","started_at":1000,"updated_at":4900},
                           result={"elapsed_s":600,"returncode":0,"reason":None})
        self.assertEqual(p["actual_finished_at"],1600)
        self.assertEqual(p["training_elapsed_seconds"],600)

    def test_warmup_and_bptt_not_mixed(self):
        p = self.calculate(samples=[(i,i/4) for i in range(0,701,10)])
        self.assertEqual(p["window_iterations"],200)
        self.assertIsNone(p["recent_iterations_per_second"])
        self.assertIsNone(p["estimated_finish_at"])

    def test_stale_log_does_not_predict_completion(self):
        p = self.calculate(log_mtime=1500)
        self.assertIsNone(p["estimated_finish_at"])
        self.assertIn("暂未更新",p["note"])

    def test_insufficient_history_no_invented_speed(self):
        p = self.calculate(samples=[(1000,0),(1100,40)])
        self.assertIsNone(p["recent_iterations_per_minute"])
        self.assertIsNone(p["eta_seconds"])


if __name__ == "__main__":
    unittest.main()
