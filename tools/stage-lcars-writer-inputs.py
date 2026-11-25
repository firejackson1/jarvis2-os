#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare LCARS writer inputs from a verified preflight and a pinned review."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'writer_preflight', ROOT / 'tools/prepare-lcars-install.py')
PREFLIGHT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PREFLIGHT)
PACK = PREFLIGHT.PACK
WRITER = PREFLIGHT.load_tool('writer_contract', ROOT / 'tools/install-candidate.py')


def pinned_json(path, expected):
    PACK.sha256_value(expected)
    with PACK.regular(path).open('rb') as stream:
        data = stream.read(1048577)
    if len(data) > 1048576 or hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('Review or preflight digest differs from its pin')
    result = json.loads(data, object_pairs_hook=PACK.unique_object)
    if not isinstance(result, dict):
        raise ValueError('Review and preflight must be JSON objects')
    return result


def stage(preflight, preflight_pin, capture, approval, approval_pin, lpdump, output):
    output = Path(os.path.abspath(output))
    if (output.exists() or any(path.is_symlink() for path in (output, *output.parents)) or
        any(output.is_relative_to(path.resolve()) for path in (ROOT, preflight, capture))):
        raise ValueError('Choose a fresh output directory outside the input and source trees')

    receipt = pinned_json(preflight / 'verification.json', preflight_pin)
    reviewed = pinned_json(approval, approval_pin)
    profile_path = ROOT / PREFLIGHT.PROFILE
    if (type(receipt.get('format')) is not int or receipt['format'] != 1 or
        any(receipt.get(field) is not True for field in ('avb_chain_verified', 'stock_reference_bytes_verified')) or
        any(receipt.get(field) is not False for field in ('rehearsal_only', 'device_contacted', 'installation_authorized')) or
        receipt.get('stock_profile_sha256') != PACK.digest(profile_path)):
        raise ValueError('A verified production LCARS preflight with the pinned stock profile is required')
    for name in ('archive_sha256', 'root_public_key_sha256'):
        PACK.sha256_value(receipt.get(name))
    fit = receipt.get('saved_capture_fit')
    if (not isinstance(fit, dict) or fit.get('target_slot') not in ('a', 'b') or
        fit.get('restore_images_verified') != 7 or fit.get('candidate_images_fit') != 7):
        raise ValueError('A saved fit for all seven image and restore files is required')
    slot = fit['target_slot']
    capture_pin = fit.get('capture_sha256')
    PACK.sha256_value(capture_pin)
    expected_review = {'format': 1, 'kind': 'jarvis2-reviewed-lcars-transition',
                       'target_slot': slot, 'preflight_sha256': preflight_pin, 'capture_sha256': capture_pin}
    if type(reviewed.get('format')) is not int or reviewed != expected_review:
        raise ValueError('The review must bind the exact preflight receipt, capture and target slot')

    five_names = PACK.IMAGE_NAMES
    transition_names = ('init_boot.img', 'vendor_boot.img')
    parts = {'images': five_names, 'transition-images': transition_names}
    records = receipt.get('files')
    if not isinstance(records, dict) or set(records) != {
        f'{folder}/{name}' for folder, names in parts.items() for name in names
    }:
        raise ValueError('Expected the exact seven preflight records')
    groups = {folder: {name: records[f'{folder}/{name}'] for name in names}
              for folder, names in parts.items()}
    for folder, files in groups.items():
        WRITER.image_files(preflight / folder, files)

    profile = json.loads(profile_path.read_bytes())
    actual_fit = PREFLIGHT.verify_saved_fit(records, profile, slot=slot, inputs=capture,
        capture_sha256=capture_pin, lpdump=lpdump, lpdump_sha256=fit.get('lpdump_sha256'))
    if actual_fit != fit:
        raise ValueError('Recomputed saved fit differs from the reviewed preflight')

    shared = {'passed': True, 'foundation_compatible': True, 'target_slot': slot,
              'capture_sha256': capture_pin, 'preflight_sha256': preflight_pin,
              'transition_review_sha256': approval_pin}
    candidate = {**shared, 'avb_offline_verified': True, 'files': groups['images']}
    with TemporaryDirectory(prefix='jarvis2-writer-inputs-', dir=output.parent) as scratch:
        bundle = Path(scratch) / 'inputs'
        bundle.mkdir(mode=0o700)
        candidate_path = bundle / 'candidate-proof.json'
        candidate_path.write_text(json.dumps(candidate, indent=2) + '\n')
        candidate_pin = PACK.digest(candidate_path)
        transition = {**shared, 'recovery_transition_reviewed': True,
                      'candidate_proof_sha256': candidate_pin, 'files': groups['transition-images']}
        transition_path = bundle / 'transition-proof.json'
        transition_path.write_text(json.dumps(transition, indent=2) + '\n')
        result = {'format': 1, 'target_slot': slot, 'archive_sha256': receipt['archive_sha256'],
                  'capture_sha256': capture_pin, 'preflight_sha256': preflight_pin,
                  'transition_review_sha256': approval_pin, 'candidate_proof_sha256': candidate_pin,
                  'transition_proof_sha256': PACK.digest(transition_path),
                  'device_contacted': False, 'installation_authorized': False}
        (bundle / 'writer-inputs.json').write_text(json.dumps(result, indent=2) + '\n')
        if output.exists() or output.is_symlink():
            raise ValueError('Writer input output appeared during preparation')
        bundle.rename(output)
    return result


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('preflight', 'capture', 'review', 'lpdump', 'output'):
        parser.add_argument('--' + flag, type=Path, required=True)
    for flag in ('preflight-sha256', 'review-sha256'):
        parser.add_argument('--' + flag, required=True)
    args = parser.parse_args()
    try:
        result = stage(args.preflight, args.preflight_sha256, args.capture, args.review,
                       args.review_sha256, args.lpdump, args.output)
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'LCARS writer input staging failed: {error}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
