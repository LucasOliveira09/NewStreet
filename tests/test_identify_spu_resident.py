import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import identify_spu_resident as subject


def image(size=0x100, base=0x80, pic=False):
    # Authored metadata, with four valid ILA instructions; no game bytes.
    words = [0x42000002 | (i << 7) for i in range(4)]
    words += [0x30 if pic else base + 0x30,
              size if pic else base + size + 0x50, 0x20,
              0x80000000 if pic else base,
              size if pic else base + size, 0, int(pic), 0x55011055]
    return struct.pack('>12I', *words) + bytes(size - 48)


def label(name=b'owned.elf\0'):
    return b'BuiltElfName' + bytes(20) + name


class IdentifyResidentTests(unittest.TestCase):
    def identify(self, source, loaded, base=0x80, broken_metadata=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'private').mkdir()
            (root / 'private/FIFAZF.elf').write_bytes(source)
            (root / 'spu_overlays.json').write_text(json.dumps({
                'elf_sha256': hashlib.sha256(source).hexdigest()}))
            run = root / 'run'
            (run / 'spu').mkdir(parents=True)
            (run / 'spu/state.json').write_text(json.dumps({'pc': base + 0x30}))
            ls = bytearray(0x40000)
            ls[base:base + len(loaded)] = loaded
            (run / 'spu/state.ls').write_bytes(ls)
            if broken_metadata is not None:
                (run / 'spu/000-truncated.json').write_bytes(broken_metadata)
            elf = SimpleNamespace(load=lambda: None,
                                  program_headers=[SimpleNamespace(p_type=subject.PT_LOAD,
                                                                  p_vaddr=0x100000)],
                                  get_segment_data=lambda index: source)
            with patch.object(subject, 'ROOT', root), patch.object(subject, 'ELFFile', return_value=elf):
                return subject.identify(run)

    def test_incomplete_metadata_is_reported_without_losing_valid_snapshots(self):
        for broken in [b'{"pc":', b'\xff']:
            with self.subTest(broken=broken):
                damaged, valid = self.identify(image() + label(), image(), broken_metadata=broken)
                self.assertIn('metadata_error', damaged)
                self.assertFalse(damaged['automatically_admitted'])
                self.assertNotIn('source_ea', damaged)
                self.assertEqual(valid['label'], 'owned.elf')
                self.assertEqual(valid['snapshot_byte_differences'], 0)

    def test_distant_label_is_not_assigned_to_current_image(self):
        loaded = image(size=0x4f30)
        source = loaded + bytes(0x362c0 - len(loaded)) + label(b'Replay_deltacompress.elf\0')
        result, = self.identify(source, loaded)
        self.assertNotIn('label', result)
        self.assertEqual(result['source_sha256'], hashlib.sha256(loaded).hexdigest())
        self.assertEqual(result['snapshot_byte_differences'], 0)

    def test_labels_at_declared_fixed_and_pic_boundaries(self):
        for pic, base in [(False, 0x80), (True, 0x3780), (True, 0x7800)]:
            with self.subTest(pic=pic, base=base):
                loaded = image(base=base, pic=pic)
                result, = self.identify(loaded + label(), loaded, base)
                self.assertEqual(result['label'], 'owned.elf')
                self.assertEqual(result['image_size'], hex(len(loaded)))
                self.assertEqual(result['image_end'], hex(base + len(loaded)))
                self.assertEqual(result['source_sha256'], hashlib.sha256(loaded).hexdigest())

    def test_pic_size_is_relative_even_when_loaded_above_it(self):
        loaded = image(pic=True, base=0x3780)
        result, = self.identify(loaded + label(), loaded, 0x3780)
        self.assertEqual(result['image_bounds_basis'], 'pic_relative_size')
        self.assertEqual(result['label_size_hint'], '0x100')

    def test_missing_name_preserves_differences_within_initialized_image(self):
        source = image() + bytes(0x100)
        loaded = bytearray(image())
        loaded[0x60] = 1
        result, = self.identify(source, loaded)
        self.assertNotIn('label', result)
        self.assertEqual(result['snapshot_byte_differences'], 1)
        self.assertEqual(result['first_differences'], ['0xe0'])
        self.assertEqual(result['source_sha256'], hashlib.sha256(image()).hexdigest())

    def test_nearby_and_internal_markers_are_not_image_boundaries(self):
        for offset in [0x60, 0xff, 0x101, 0x150]:
            with self.subTest(offset=offset):
                source = bytearray(image() + bytes(0x100))
                source[offset:offset + len(label())] = label()
                result, = self.identify(bytes(source), image())
                self.assertNotIn('label', result)

    def test_rejects_truncated_empty_non_ascii_and_unterminated_names(self):
        for trailer in [b'BuiltElfName', label(b''), label(b'\0'),
                        label(b'broken.elf'), label(b'bad\xff.elf\0'),
                        label(b'bad\n.elf\0'), label(b'a' * 512 + b'\0')]:
            with self.subTest(trailer=trailer[:50]):
                result, = self.identify(image() + trailer, image())
                self.assertNotIn('label', result)
                self.assertIn('source_sha256', result)

    def test_long_name_is_returned_complete(self):
        name = b'c:/' + b'a' * 100 + b'/owned.elf'
        result, = self.identify(image() + label(name + b'\0'), image())
        self.assertEqual(result['label'], name.decode('ascii'))

    def test_trailer_may_follow_last_local_store_byte(self):
        loaded = image(size=0x40000 - 0x80)
        result, = self.identify(loaded + label(), loaded)
        self.assertEqual(result['label'], 'owned.elf')
        self.assertEqual(result['image_end'], '0x40000')

    def test_duplicate_source_headers_are_ambiguous(self):
        source = image() + label() + image() + label(b'other.elf\0')
        result, = self.identify(source, image())
        self.assertEqual(result['source_header_matches'], 2)
        self.assertNotIn('label', result)
        self.assertNotIn('source_ea', result)

    def test_invalid_or_truncated_bounds_do_not_claim_image_hash(self):
        for offset, value in [(28, 0x90), (32, 0x40004), (32, 0xa0),
                              (32, 0x181), (16, 0x1000)]:
            with self.subTest(offset=offset, value=value):
                loaded = bytearray(image())
                struct.pack_into('>I', loaded, offset, value)
                result, = self.identify(bytes(loaded) + label(), loaded)
                self.assertIn('image_bounds_error', result)
                self.assertNotIn('source_sha256', result)
                self.assertNotIn('label', result)
        result, = self.identify(image()[:0x80], image())
        self.assertIn('image_bounds_error', result)


if __name__ == '__main__':
    unittest.main()
