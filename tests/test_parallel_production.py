"""Concurrent preparation must preserve bulletin order and fail on missing work."""
import threading
import unittest
from unittest.mock import patch

from scripts import generate


class ParallelProductionTests(unittest.TestCase):
    def test_tasks_overlap_and_results_remain_in_input_order(self):
        barrier = threading.Barrier(2, timeout=5)
        second_finished = threading.Event()
        def work(index):
            barrier.wait()
            if index == 0:
                self.assertTrue(second_finished.wait(5))
            else:
                second_finished.set()
            return index
        with patch.object(generate, 'CONFIG', {'production': {'parallel_workers': 2}}):
            self.assertEqual(generate.parallel_map(work, [0, 1], 'test'), [0, 1])

    def test_worker_limit_is_respected(self):
        barrier = threading.Barrier(2, timeout=5)
        lock = threading.Lock()
        active = peak = 0
        def work(index):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            barrier.wait()
            barrier.wait()
            with lock:
                active -= 1
            return index
        with patch.object(generate, 'CONFIG', {'production': {'parallel_workers': 2}}):
            self.assertEqual(generate.parallel_map(work, range(6), 'test'), list(range(6)))
        self.assertEqual(peak, 2)

    def test_single_worker_runs_on_calling_thread(self):
        caller = threading.get_ident()
        with patch.object(generate, 'CONFIG', {'production': {'parallel_workers': 1}}):
            self.assertEqual(generate.parallel_map(lambda _: threading.get_ident(), range(3), 'test'), [caller] * 3)

    def test_missing_config_enables_two_workers(self):
        barrier = threading.Barrier(2, timeout=5)
        with patch.object(generate, 'CONFIG', {}):
            self.assertEqual(sorted(generate.parallel_map(lambda _: barrier.wait(), range(2), 'test')), [0, 1])

    def test_worker_failure_propagates(self):
        def fail(_):
            raise RuntimeError('Speech unavailable')
        with patch.object(generate, 'CONFIG', {}):
            with self.assertRaisesRegex(RuntimeError, 'Speech unavailable'):
                generate.parallel_map(fail, range(4), 'Speech')

    def test_empty_stage(self):
        self.assertEqual(generate.parallel_map(lambda _: self.fail('Unexpected task'), [], 'test'), [])


if __name__ == '__main__':
    unittest.main()
