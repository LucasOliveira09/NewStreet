"""Exercise the actual runtime's four unsupported-call boundaries."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / 'private/build/boot/fifa_boot.exe'


class BootDiagnosticsTests(unittest.TestCase):
    def test_generic_trophy_metadata_cannot_report_success_in_game_boot(self):
        for mode, nid in [('trophy-game-info', 0x49d18217), ('trophy-info', 0xfce6d30a),
                          ('trophy-unlock', 0x8ceedd21)]:
            with self.subTest(mode=mode):
                result = subprocess.run([str(BOOT), '--test-missing', mode],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 90, result.stderr)
                event = json.loads(next(line.removeprefix('[fifa-block] ') for line in result.stderr.splitlines()
                                        if line.startswith('[fifa-block] ')))
                self.assertEqual(event['kind'], 'trophy-metadata')
                self.assertEqual(event['value'], nid)
                self.assertEqual(event['guest_lr'], 0x12345678)
                self.assertEqual(event['arguments'][0], 0x1122334455667788)

    def test_first_import_trace_is_opt_in_and_preserves_dispatch_results(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled), tempfile.TemporaryDirectory() as folder:
                env = dict(os.environ, PS3_HDD0_ROOT=folder)
                env.pop('PS3_HLE_FIRST_CALLS', None)
                if enabled:
                    env['PS3_HLE_FIRST_CALLS'] = '1'
                result = subprocess.run([str(BOOT), '--test-fs-free-space', folder],
                                        capture_output=True, text=True, timeout=10, env=env)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                actual = json.loads(result.stdout.splitlines()[-1])
                self.assertEqual(actual['result'], 0)
                self.assertTrue(actual['null_arguments_preserved'])
                traces = [line for line in result.stderr.splitlines() if line.startswith('[hle-first] ')]
                self.assertEqual(len(traces), 1 if enabled else 0)
                if enabled:
                    self.assertIn('nid=0xAA3B4BCD lr=0x00000000', traces[0])
                    self.assertIn('r3=0x10000 r4=0x11000 r5=0x11008', traces[0])
                    self.assertTrue(traces[0].endswith('result=0x0'))

    def test_free_space_matches_the_mounted_host_volume(self):
        with tempfile.TemporaryDirectory() as folder:
            env = dict(os.environ, PS3_HDD0_ROOT=folder)
            result = subprocess.run([str(BOOT), '--test-fs-free-space', folder],
                                    capture_output=True, text=True, timeout=10, env=env)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        actual = json.loads(result.stdout.splitlines()[-1])
        self.assertEqual(actual['result'], 0)
        self.assertTrue(actual['host_queries'])
        self.assertTrue(actual['null_arguments_preserved'])
        self.assertEqual(actual['block'], 4096)
        # Queries bracket the guest call; allow small concurrent host writes.
        guest_bytes = actual['count'] * actual['block']
        self.assertGreaterEqual(guest_bytes, min(actual['before'], actual['after']) - 262144)
        self.assertLessEqual(guest_bytes, max(actual['before'], actual['after']) + 262144)

    def test_free_space_does_not_invent_capacity_for_missing_host_mount(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = str(Path(folder) / 'absent')
            result = subprocess.run([str(BOOT), '--test-fs-free-space', missing],
                                    capture_output=True, text=True, timeout=10,
                                    env=dict(os.environ, PS3_HDD0_ROOT=missing))
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        actual = json.loads(result.stdout.splitlines()[-1])
        self.assertNotEqual(actual['result'], 0)
        self.assertFalse(actual['host_queries'])
        self.assertEqual((actual['block'], actual['count']), (0, 0))

    def test_input_observer_preserves_api_and_observed_state(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                env = dict(os.environ)
                env.pop('FIFA_INPUT_TRACE', None)
                if enabled:
                    env['FIFA_INPUT_TRACE'] = '1'
                result = subprocess.run([str(BOOT), '--test-input-observer'],
                                        capture_output=True, text=True, timeout=10, env=env)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                self.assertEqual(json.loads(result.stdout.splitlines()[-1]),
                                 dict(api_result=True, registers=True, observed_memory=True))
                events = [json.loads(line.split('] ', 1)[1]) for line in result.stderr.splitlines()
                          if line.startswith('[fifa-input] ')]
                self.assertEqual([event['digital_bits'] for event in events], [8, 0, 0, 0] if enabled else [])
                if enabled:
                    self.assertEqual([event['last_packet'] for event in events], [0x80000, 0, 0x40, 0])
                    self.assertEqual([event['cross_pressure'] for event in events], [0, 0, 255, 0])
                    self.assertTrue(all(event['bits_readable'] for event in events))

    def test_pad_modes_match_protocol_lengths_headers_and_partial_writes(self):
        env = dict(os.environ)
        env.pop('PAD_FILE', None)
        result = subprocess.run([str(BOOT), '--test-pad-modes'],
                                capture_output=True, text=True, timeout=10, env=env)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]),
                         dict(modes=4, lengths=True, headers=True, untouched_tail=True))

    def test_pad_empty_report_preserves_previous_button_payload(self):
        env = dict(os.environ)
        env.pop('PAD_ALWAYS_CHANGE', None)
        env.pop('PAD_FILE', None)
        result = subprocess.run([str(BOOT), '--test-pad-empty-payload'],
                                capture_output=True, text=True, timeout=10, env=env)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(empty_payload_preserved=True))

    def test_file_pad_press_survives_reads_without_a_fresh_report(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'pad.txt')
            env = dict(os.environ, PAD_FILE=path, PAD_REPORT_TRACE='1')
            env.pop('PAD_ALWAYS_CHANGE', None)
            result = subprocess.run([str(BOOT), '--test-pad-file', path],
                                    capture_output=True, text=True, timeout=10, env=env)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(held_through_empty_read=True))
        reports = [json.loads(line.split('] ', 1)[1]) for line in result.stderr.splitlines()
                   if line.startswith('[pad-report] ')]
        self.assertTrue(any(report['length'] > 0 and report['digital1'] & 8 for report in reports))

    def test_file_pad_press_releases_with_always_change_diagnostic_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'pad.txt')
            result = subprocess.run([str(BOOT), '--test-pad-file', path],
                                    capture_output=True, text=True, timeout=10,
                                    env=dict(os.environ, PAD_FILE=path, PAD_ALWAYS_CHANGE='1', PAD_REPORT_TRACE='1'))
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(press_released=True))
        reports = [json.loads(line.split('] ', 1)[1]) for line in result.stderr.splitlines()
                   if line.startswith('[pad-report] ')]
        self.assertEqual([report['digital1'] & 8 for report in reports], [8, 0])

    def test_savedata_overlay_uses_void_abi(self):
        result = subprocess.run([str(BOOT), '--test-savedata-overlay'],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]),
                         dict(void_abi=True, preference_cases=7, default_disabled=True))

    def test_spu_entry_trace_records_each_physical_base_once(self):
        result = subprocess.run([str(BOOT), '--test-spu-entry-trace'],
                                capture_output=True, text=True, timeout=10,
                                env=dict(os.environ, FIFA_SPU_ENTRY_TRACE='1'))
        self.assertEqual(result.returncode, 0, result.stderr)
        entries = [json.loads(line.split('] ', 1)[1]) for line in result.stderr.splitlines()
                   if line.startswith('[fifa-spu-entry] ')]
        self.assertEqual([(e['name'], e['ls_base'], e['pc']) for e in entries],
                         [('fixture', 0, 0x30), ('fixture', 0x7800, 0x7830),
                          ('fixture', 0x8480, 0x84b0), ('other', 0x7800, 0x7830)])

    def test_native_pic_instructions_keep_physical_links_and_relative_and_absolute_memory(self):
        result = subprocess.run([str(BOOT), '--test-spu-pic-lowering'],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout), dict(positions=4, event_paths=2, runs=8, relative_memory=True,
            absolute_memory=True, physical_links=True, cross_program_call=True))

    def test_pic_program_keeps_three_physical_positions_and_negative_bias_independent(self):
        result = subprocess.run([str(BOOT), '--test-spu-overlay', 'pic'],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout), dict(positions=3, isolated=True,
                                                       negative_bias=True, split_preserved=True))

    def test_pic_admission_rejects_modified_source_invalid_layout_and_overwritten_code(self):
        for mode, kind in [('pic-source', 'spu-overlay-source'),
                           ('pic-unaligned', 'spu-overlay-layout'),
                           ('pic-boundary', 'spu-overlay-layout'),
                           ('pic-absolute-source', 'spu-overlay-layout'),
                           ('pic-overwrite', 'spu-indirect')]:
            with self.subTest(mode=mode):
                result = subprocess.run([str(BOOT), '--test-spu-overlay', mode],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 90, result.stderr + result.stdout)
                event = json.loads(next(line.removeprefix('[fifa-block] ') for line in result.stderr.splitlines()
                                        if line.startswith('[fifa-block] ')))
                self.assertEqual(event['kind'], kind)

    def test_fifo_host_callback_setter_is_not_registered_as_a_guest_import(self):
        with tempfile.TemporaryDirectory(prefix='fifa HLE ') as folder:
            table = Path(folder) / 'hle.cpp'
            result = subprocess.run([sys.executable, str(ROOT / 'vendor/ps3recomp/tools/gen_hle_nids.py'),
                                     '--out', str(table), 'cellGcmSys'],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            registrations = table.read_text()
            self.assertIn('cellGcmGetControlRegister', registrations)
            self.assertFalse('fifo_set_fault_handler' in registrations,
                             'Host callback setter leaked into the guest NID table')

    def test_rsx_fifo_rejects_unmapped_jumps_and_unknown_words_before_recovery(self):
        for mode, reason in [('invalid-jump', 'unmapped-JUMP'), ('unknown-word', 'unknown-word')]:
            with self.subTest(mode=mode):
                result = subprocess.run([str(BOOT), '--test-rsx-fifo', mode],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 90, result.stderr + result.stdout)
                event = json.loads(next(line.removeprefix('[fifa-block] ') for line in result.stderr.splitlines()
                                        if line.startswith('[fifa-block] ')))
                self.assertEqual(event['kind'], 'rsx-fifo-' + reason)
                self.assertEqual(event['value'], 4) # GET=0, PUT=4, no forced advance.

    def test_rsx_fifo_waits_for_real_producer_updates_without_skipping_commands(self):
        for mode, waiting, end, label in [('park', 0, 0x50, 7), ('acquire', 8, 0x20, 9)]:
            with self.subTest(mode=mode):
                env = os.environ.copy()
                env.pop('GCM_SEMA_ACQUIRE', None)
                env['GCM_SEMA_ACQUIRE_MS'] = '1'
                result = subprocess.run([str(BOOT), '--test-rsx-fifo', mode],
                                        env=env, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                self.assertEqual(json.loads(result.stdout.splitlines()[-1]),
                                 dict(waiting_get=waiting, untouched=True, final_get=end, label=label))

    def test_directory_eof_clears_hdd0_header_and_preserves_hdd1_last_entry(self):
        for disk in ('hdd0', 'hdd1'):
            for populated in (False, True):
                with self.subTest(disk=disk, populated=populated), tempfile.TemporaryDirectory(prefix='fifa dirs ') as folder:
                    root = Path(folder)
                    (root / 'scan').mkdir()
                    if populated:
                        (root / 'scan/item.bin').write_bytes(b'fixture')
                        (root / 'scan/child').mkdir()
                    env = os.environ.copy()
                    env['PS3_' + disk.upper() + '_ROOT'] = folder
                    result = subprocess.run([str(BOOT), '--test-fs-readdir', '/dev_' + disk + '/scan'],
                                            env=env, capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                    observed = json.loads(result.stdout.splitlines()[-1])
                    self.assertEqual(observed, dict(entries=4 if populated else 2,
                                                    eof_bytes=0, first_eof=True, repeated_eof=True))

    def test_account_region_online_provider_absence_stays_explicit(self):
        env = os.environ.copy()
        # These enable the runtime mode check; no connection is initiated by
        # sceNpInit or this account-region query.
        env.update(PS3_NET_ONLINE='1', PSNR_SERVER='unused.invalid')
        result = subprocess.run([str(BOOT), '--test-offline-np'], env=env,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 90, result.stderr)
        event = json.loads(next(line.removeprefix('[fifa-block] ') for line in result.stderr.splitlines()
                                if line.startswith('[fifa-block] ')))
        self.assertEqual(event['kind'], 'np-account-region-online')

    def test_account_region_reports_real_offline_state_without_fabricating_profile(self):
        env = os.environ.copy()
        env.pop('PS3_NET_ONLINE', None)
        env.pop('PSNR_SERVER', None)
        result = subprocess.run([str(BOOT), '--test-offline-np'], env=env,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        event = json.loads(result.stdout.splitlines()[-1])
        self.assertEqual(event, dict(before=0x8002aa01, invalid_country=0x8002aa03,
                                    invalid_language=0x8002aa03, offline=0x8002aa0c,
                                    after=0x8002aa01, untouched=True))

    def test_job_observer_waits_for_tail_transfers_and_preserves_guest_return(self):
        for depth in (0, 2):
            baseline = None
            for enabled in (False, True):
                with self.subTest(depth=depth, enabled=enabled), tempfile.TemporaryDirectory(prefix='fifa jobs ') as folder:
                    env = os.environ.copy()
                    env.pop('FIFA_SPU_JOB_TRACE_DIR', None)
                    if enabled:
                        env['FIFA_SPU_JOB_TRACE_DIR'] = folder
                    result = subprocess.run([str(BOOT), '--test-spu-observer', str(depth)],
                                            env=env, capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    observed = json.loads(result.stdout)
                    self.assertEqual(observed, dict(pc=0x300, depth=depth, result=7, pending=False, output='OUT!'))
                    if enabled:
                        self.assertEqual(observed, baseline)
                        self.assertEqual((Path(folder) / 'zlib-0.input').read_bytes(), b'IN!!')
                        self.assertEqual((Path(folder) / 'zlib-0.output').read_bytes(), b'OUT!\x00')
                        self.assertTrue(json.loads((Path(folder) / 'zlib-0.json').read_text())['captured'])
                    else:
                        baseline = observed
                        self.assertEqual(list(Path(folder).iterdir()), [])

    def test_failure_memory_snapshot_contains_real_guest_opd_bytes(self):
        with tempfile.TemporaryDirectory(prefix='fifa PPU ') as folder:
            env = os.environ.copy()
            env.update(FIFA_PPU_DUMP_DIR=folder, FIFA_PPU_DUMP_RANGES='0x10000:0x8')
            result = subprocess.run([str(BOOT), '--test-missing', 'callback'],
                                    env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 90, result.stderr)
            snapshots = list(Path(folder).glob('*.bin'))
            self.assertEqual(len(snapshots), 1)
            self.assertEqual(snapshots[0].read_bytes(), bytes.fromhex('0012340000006789'))

    def test_fs_context_io_and_generic_rename_share_default_and_overridden_cache_roots(self):
        for override, repeated in ((False, False), (True, False), (False, True), (True, True)):
            with self.subTest(override=override, repeated=repeated), tempfile.TemporaryDirectory(prefix='fifa FS ') as folder:
                disc = Path(folder) / 'disc'; disc.mkdir()
                storage = Path(folder) / 'cache storage' if override else disc
                (storage / 'cache/test').mkdir(parents=True)
                env = os.environ.copy(); env.pop('PS3_HDD1_ROOT', None)
                env.pop('FIFA_TEST_REPEATED_SLASH', None)
                if repeated: env['FIFA_TEST_REPEATED_SLASH'] = '1'
                if override: env['PS3_HDD1_ROOT'] = str(storage)
                result = subprocess.run([str(BOOT), '--test-fs-mounts', str(disc)],
                                        capture_output=True, text=True, env=env, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                self.assertEqual(json.loads(result.stdout.splitlines()[-1]),
                                 dict(renamed=0, bytes=11, missing_source=0x80010006))
                self.assertFalse((storage / 'cache/test/data.tmp').exists())
                self.assertEqual((storage / 'cache/test/data.big').read_bytes(), b'FIFA\x00\xff\x01\x02\x03\x04\x05')

    def test_streamed_spu_code_owns_its_region_across_dma_chunks(self):
        for mode in ('valid', 'data'):
            with self.subTest(mode=mode):
                result = subprocess.run([str(BOOT), '--test-spu-overlay', mode],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), dict(value=7, owner=222))

    def test_seven_spu_modules_keep_independent_resident_code_ownership(self):
        result = subprocess.run([str(BOOT), '--test-spu-overlay', 'many'],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), dict(modules=7, dispatched=7))

    def test_initialized_offline_netctl_reports_disconnected_and_preserves_lifecycle_errors(self):
        env = os.environ.copy()
        env.pop('PS3_NET_ONLINE', None)
        result = subprocess.run([str(BOOT), '--test-offline-netctl'], env=env,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]),
                         dict(before=0x80130101, duplicate=0x80130102,
                              invalid=0x80130107, result=0, state=0,
                              after=0x80130101, untouched=True,
                              invalid_info=0x80130107, offline_info=0x80130108,
                              untouched_info=True))

    def test_same_spu_source_selects_the_static_translation_for_its_ls_base(self):
        result = subprocess.run([str(BOOT), '--test-spu-overlay', 'relocated'],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), dict(value=9, owner=333))

    def test_nested_spu_plugin_preserves_outer_code_and_can_be_reloaded(self):
        result = subprocess.run([str(BOOT), '--test-spu-overlay', 'overlap'],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), dict(nested=9, outer=7, reloaded=7))

    def test_modified_missing_or_evicted_spu_overlay_cannot_run_stale_code(self):
        for mode, kind in [('tamper', 'spu-overlay-source'), ('base', 'spu-overlay-base'), ('overwrite', 'spu-indirect'),
                           ('missing', 'spu-indirect'), ('overlap-unknown', 'spu-indirect')]:
            with self.subTest(mode=mode):
                result = subprocess.run([str(BOOT), '--test-spu-overlay', mode],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 90, result.stderr)
                event = json.loads(next(line.removeprefix('[fifa-block] ') for line in result.stderr.splitlines()
                                        if line.startswith('[fifa-block] ')))
                self.assertEqual(event['kind'], kind)

                if mode == 'overlap-unknown':
                    self.assertEqual(event['value'] & 0xffffffff, 0x1a0)

    def test_spu_failure_preserves_actual_local_store_and_registers_in_private_diagnostics(self):
        with tempfile.TemporaryDirectory(prefix='fifa SPU ') as folder:
            env = os.environ.copy()
            env['FIFA_SPU_DUMP_DIR'] = folder
            result = subprocess.run([str(BOOT), '--test-missing', 'spu-indirect'],
                                    env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 90, result.stderr)
            states = list(Path(folder).glob('*.json'))
            self.assertEqual(len(states), 1)
            state = json.loads(states[0].read_text())
            local_store = states[0].with_suffix('.ls').read_bytes()
            self.assertEqual(len(local_store), 256 * 1024)
            self.assertEqual(local_store[0x300], 0xa5)
            self.assertEqual(state['pc'], 0x3ff00)
            self.assertEqual(state['gpr'][0][0], 0x1234)
            self.assertEqual(state['image'], 987654321)

    def test_raw_spu_exit_stops_nested_execution_before_any_later_side_effect(self):
        result = subprocess.run([str(BOOT), '--test-spu-termination', 'exit'],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout),
                         dict(halted=True, continued=False, stop_code=0x102, mailbox=23))

    def test_raw_spu_zero_branch_and_unsupported_stop_cannot_complete_silently(self):
        for mode, kind in [('zero', 'spu-indirect'), ('fatal', 'spu-stop'), ('fault', 'spu-fault')]:
            with self.subTest(mode=mode):
                result = subprocess.run([str(BOOT), '--test-spu-termination', mode],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 90, result.stderr)
                event = json.loads(next(line.removeprefix('[fifa-block] ') for line in result.stderr.splitlines()
                                        if line.startswith('[fifa-block] ')))
                self.assertEqual(event['kind'], kind)

    def test_native_spu_cannot_select_another_program_by_shared_entry_address(self):
        result = subprocess.run([str(BOOT), '--test-spu-image-mismatch'], capture_output=True,
                                text=True, timeout=10)
        self.assertEqual(result.returncode, 90, result.stderr)
        event = json.loads(next(line.removeprefix('[fifa-block] ') for line in result.stderr.splitlines()
                                if line.startswith('[fifa-block] ')))
        self.assertEqual(event['kind'], 'spu-program')
        self.assertEqual(event['value'], 0x10000)
        self.assertNotIn('RUNNING lifted image', result.stderr)

    def test_spu_groups_keep_sparse_numbers_arguments_and_local_store_isolated(self):
        result = subprocess.run([str(BOOT), '--test-spu-groups'], capture_output=True,
                                text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), dict(groups=3, threads=4,
            isolated=True, copied_arguments=True, invalid_requests_rejected=True))

    def test_hle_callback_enters_guest_code_with_64bit_arguments_and_thread_identity(self):
        result = subprocess.run([str(BOOT), '--test-callback'], capture_output=True,
                                text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        event = json.loads(result.stdout)
        self.assertEqual(event['argument_sum'], 0x100000024)
        self.assertEqual(event['callback_return'], 0x100000024)
        self.assertEqual(event['identity'], 77)
        self.assertEqual(event['toc'], 0x6789)
        self.assertTrue(event['caller_restored'])

    def test_prx_exports_keep_library_nid_kind_and_guest_context(self):
        result = subprocess.run([str(BOOT), '--test-prx'], capture_output=True,
                                text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        event = json.loads(result.stdout)
        self.assertEqual(event['register_result'], 0)
        self.assertEqual(event['function'], 0x12000)
        self.assertEqual(event['variable'], 0x15000)
        self.assertEqual(event['other_library'], 0)
        self.assertEqual(event['call_result'], 42)
        self.assertEqual(event['restored_toc'], 0xABCDE)
        self.assertEqual(event['bad_header_result'], 0x80010002)
        self.assertEqual(event['after_bad_header'], 0x12000)

    def test_native_crash_keeps_exception_diagnostics(self):
        result = subprocess.run([str(BOOT), '--test-native-crash'], capture_output=True,
                                text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        event = json.loads(next(line.removeprefix('[fifa-crash] ') for line in result.stderr.splitlines()
                                if line.startswith('[fifa-crash] ')))
        self.assertEqual(event['exception'], 0xE0464946)
        self.assertGreater(event['host_rip'], 0)

    def test_native_child_receives_exact_arguments_and_propagates_exit_code(self):
        with tempfile.TemporaryDirectory(prefix='fifa child ') as folder:
            script = Path(folder) / 'capture args.py'
            script.write_text('import sys,json\nprint(json.dumps(sys.argv[1:]))\nsys.exit(37)\n')
            env = os.environ.copy()
            env.update(FIFA_NEXT_EXE=sys.executable, FIFA_NEXT_ELF=str(script))
            result = subprocess.run([str(BOOT), '--test-spawn-child'], capture_output=True,
                                    text=True, timeout=10, env=env)
        self.assertEqual(result.returncode, 37, result.stderr)
        self.assertIn('[fifa-native-child]', result.stderr)
        self.assertEqual(json.loads(result.stdout), [
            'C:/disc with spaces/', '--boot-path', '/dev_bdvd/PS3_GAME/USRDIR/fifazf.self',
            '--guest-arg', 'hello world', '--guest-arg', 'quote"slash\\',
            '--guest-arg', 'a;b', '--guest-arg', ''])

    def test_guest_arguments_do_not_depend_on_a_semicolon_separator(self):
        arguments = ['hello world', 'a;b', '', 'quote"slash\\']
        command = [str(BOOT), '--test-argv', 'unused', '--boot-path', '/dev_bdvd/fifazf.self']
        for value in arguments:
            command += ['--guest-arg', value]
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), ['/dev_bdvd/fifazf.self'] + arguments)

    def test_spawn_request_preserves_guest_32bit_pointer_arrays(self):
        result = subprocess.run([str(BOOT), '--test-spawn'], capture_output=True,
                                text=True, timeout=10)
        self.assertEqual(result.returncode, 92, result.stderr)
        event = json.loads(next(line.removeprefix('[fifa-spawn] ') for line in result.stderr.splitlines()
                                if line.startswith('[fifa-spawn] ')))
        self.assertEqual(event['path'], '/dev_bdvd/PS3_GAME/USRDIR/fifazf.self')
        self.assertEqual(event['argv'], ['hello world', 'quote"slash\\'])
        self.assertEqual(event['envp'], ['TEST=1'])
        self.assertEqual(event['priority'], 1001)

    def test_missing_runtime_work_cannot_report_success(self):
        for boundary in ('hle', 'syscall', 'indirect', 'indirect-null', 'unlifted', 'callback', 'callback-ct', 'spu-workload', 'spu-indirect'):
            with self.subTest(boundary=boundary):
                result = subprocess.run([str(BOOT), '--test-missing', boundary],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 90, result.stderr)
                lines = [line for line in result.stderr.splitlines()
                         if line.startswith('[fifa-block] ')]
                self.assertEqual(len(lines), 1, result.stderr)
                event = json.loads(lines[0].removeprefix('[fifa-block] '))
                self.assertEqual(event['kind'], boundary)
                self.assertEqual(event['guest_lr'], 0x12345678)
                self.assertEqual(event['arguments'][0], 0x1122334455667788)
                self.assertNotIn('faking CELL_OK', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
