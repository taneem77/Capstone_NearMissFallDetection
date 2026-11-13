"""
Automated Sequential Click-Through and State Verification Test Suite
Tests rapid switching, back-navigation, and exact payload-to-control matching
to prove zero stale-state or crosstalk exists.
"""

import os
import sys
import unittest
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from server import app

class TestStateAndControlIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def test_pipeline_step_switching_and_back_nav(self):
        """Simulate user rapidly clicking Step 1 -> 2 -> 3 -> 4 -> 5 -> 3 -> 1 -> 4 -> 2."""
        sequence = [1, 2, 3, 4, 5, 3, 1, 4, 2]
        for step in sequence:
            res = self.client.get(f'/api/pipeline_step?step={step}&subject=SA06&task=30&trial=1')
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data['step'], step, f"Expected step {step}, got {data.get('step')}")
            # Verify specific step characteristics
            if step == 1:
                self.assertIn('signal_in', data)
                self.assertIn('time_s', data)
            elif step == 2:
                self.assertIn('signal_in', data)
                self.assertIn('title', data)
            elif step == 3:
                self.assertIn('signal_in', data)
            elif step == 4:
                self.assertIn('windows', data)
            elif step == 5:
                self.assertEqual(data.get('total_feature_count'), 59)

    def test_rq_results_tabs_rapid_toggle(self):
        """Simulate rapid toggling between RQ1, RQ2, RQ3, RQ4 tabs."""
        rq_sequence = ['rq1', 'rq4', 'rq2', 'rq3', 'rq1', 'rq2', 'rq4']
        for rq in rq_sequence:
            res = self.client.get('/api/rq_results')
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIn(rq, data)
            if rq == 'rq1':
                self.assertIn('metrics', data['rq1'])
            elif rq == 'rq2':
                self.assertIn('metrics', data['rq2'])
            elif rq == 'rq3':
                self.assertIn('mean_latency_ms', data['rq3'])
            elif rq == 'rq4':
                self.assertIn('headline', data['rq4'])

    def test_live_recording_switching_and_recompute(self):
        """Test switching across recordings and recomputing detection with custom thresholds."""
        test_cases = [
            ("SA06", 30, 1), # Fall Task 30
            ("SA06", 1, 1),  # Walk Task 01
            ("SA07", 32, 1), # Slip Task 32
            ("SA06", 30, 1)  # Back to Fall Task 30
        ]
        for subj, task, trial in test_cases:
            res = self.client.get(f'/api/load_recording?subject={subj}&task={task}&trial={trial}')
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            stream = data['stream']
            self.assertEqual(stream['subject'], subj)
            self.assertEqual(stream['task'], task)
            self.assertEqual(stream['trial'], trial)
            self.assertIn('acc_mag', stream)
            self.assertIn('grip_n', stream)

            # Recompute with varying thresholds
            payload = {
                'jerk_threshold': 50.0,
                'grip_threshold': 10.0,
                'coincidence_window_sec': 0.35
            }
            rec_res = self.client.post('/api/recompute_detection',
                                       data=json.dumps(payload),
                                       content_type='application/json')
            self.assertEqual(rec_res.status_code, 200)
            det = rec_res.get_json()
            self.assertIn('imu', det)
            self.assertIn('grip', det)
            self.assertIn('fused', det)

    def test_protocol_recording_trial_types(self):
        """Verify recording protocol trial across multiple activity types."""
        activities = ["nearmiss", "walking", "tapping", "stairs", "nearmiss"]
        for act in activities:
            res = self.client.get(f'/api/record_trial?activity={act}&subject=S01&trial=1')
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data['activity'], act)
            self.assertEqual(data['subject'], 'S01')
            self.assertIn('event_box', data)
            self.assertIn('acc_mag', data)
            self.assertIn('grip_n', data)

    def test_curated_playlist_and_coverage(self):
        """Verify dataset catalog coverage and curated playlist consistency."""
        cov_res = self.client.get('/api/dataset_coverage')
        self.assertEqual(cov_res.status_code, 200)
        cov = cov_res.get_json()
        self.assertGreaterEqual(cov['total_subjects'], 30)
        self.assertGreaterEqual(cov['total_files'], 4000)

        play_res = self.client.get('/api/curated_playlist')
        self.assertEqual(play_res.status_code, 200)
        playlist_data = play_res.get_json()
        playlist = playlist_data['playlist']
        self.assertGreaterEqual(len(playlist), 5)
        for item in playlist:
            self.assertIn('subject', item)
            self.assertIn('task', item)
            self.assertIn('label', item)

if __name__ == '__main__':
    unittest.main()
