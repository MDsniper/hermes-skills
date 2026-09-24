#!/usr/bin/env python3
"""Offline, bounded configuration review. Independently written; no upstream code.

Apache-2.0. See references/provenance.md. Does not prove effective permissions.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import stat

MAX_BYTES = 1024 * 1024
MAX_FILES = 32


class InputError(ValueError):
    """Safe error codes only: never echo input content or parser messages."""


def read_scoped(root, name):
    rel = Path(name)
    if rel.is_absolute() or not rel.parts or '..' in rel.parts:
        raise InputError('path_outside_scope')
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise InputError('symlink_refused')
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    fd = os.open(current, flags)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise InputError('regular_file_required')
        if info.st_size > MAX_BYTES:
            raise InputError('file_too_large')
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise InputError('file_too_large')
    return data


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError('duplicate_json_key')
        result[key] = value
    return result


def reject_nonfinite(_value):
    raise InputError('nonfinite_json_number')


def finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise InputError('json_number_out_of_range')
    return number


def strings(value):
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, list) and value and all(isinstance(x, str) and x for x in value):
        return value
    raise InputError('invalid_string_or_list')


def finding(rule_id, severity, location, predicate, csf, attack=None, d3fend=None):
    return {'rule_id': rule_id, 'severity': severity,
            'confidence': 'configuration_candidate', 'requires_context_review': True,
            'evidence': {'location': location, 'predicate': predicate},
            'mapping': {'type': 'analyst_alignment_not_certification', 'nist_csf': csf,
                        'mitre_attack': attack or [], 'd3fend': d3fend or []}}


def audit_iam(doc):
    if not isinstance(doc, dict) or 'Statement' not in doc:
        raise InputError('iam_document_required')
    statements = doc['Statement']
    if isinstance(statements, dict):
        statements = [statements]
    if not isinstance(statements, list) or not statements:
        raise InputError('iam_statements_required')
    findings = []
    omissions = ['effective_permissions', 'trust_and_resource_policies',
                 'boundaries_scps_and_other_denies', 'service_action_semantics']
    for i, statement in enumerate(statements):
        if not isinstance(statement, dict) or statement.get('Effect') not in ('Allow', 'Deny'):
            raise InputError('invalid_iam_statement')
        for positive, negative in [('Action', 'NotAction'), ('Resource', 'NotResource')]:
            if (positive in statement) == (negative in statement):
                raise InputError('iam_exclusive_field_required')
            strings(statement.get(positive, statement.get(negative)))
        if 'Condition' in statement:
            if not isinstance(statement['Condition'], dict):
                raise InputError('invalid_iam_condition')
            omissions.append('conditions_not_evaluated')
        if 'NotAction' in statement or 'NotResource' in statement:
            omissions.append('notaction_notresource_not_evaluated')
            continue
        if 'Principal' in statement or 'NotPrincipal' in statement:
            omissions.append('principal_not_evaluated')
        actions = strings(statement['Action'])
        resources = strings(statement['Resource'])
        if statement['Effect'] == 'Allow' and '*' in resources and any('*' in a or '?' in a for a in actions):
            findings.append(finding('IAM001', 'high',
                {'statement_index': i, 'fields': ['Action', 'Resource']},
                'Allow with wildcard action pattern and literal global Resource; conditions and denies unresolved',
                ['PR.AA-05'], ['T1078.004']))
    return findings, sorted(set(omissions))


def audit_compose(doc):
    if not isinstance(doc, dict) or not isinstance(doc.get('services'), dict) or not doc['services']:
        raise InputError('compose_services_required')
    findings = []
    omissions = ['image_and_runtime_state', 'environment_interpolation_and_merges',
                 'unlisted_settings', 'network_reachability', 'effective_user_namespaces']
    for i, service in enumerate(doc['services'].values()):
        if not isinstance(service, dict):
            raise InputError('invalid_compose_service')
        for field in ['privileged', 'read_only']:
            if field in service and not isinstance(service[field], bool):
                raise InputError('compose_boolean_required')
        if 'network_mode' in service and not isinstance(service['network_mode'], str):
            raise InputError('compose_network_mode_string_required')
        caps = service.get('cap_add', [])
        if not isinstance(caps, list) or not all(isinstance(c, str) for c in caps):
            raise InputError('compose_capability_list_required')
        user = service.get('user')
        if 'user' in service and (isinstance(user, bool) or not isinstance(user, (str, int))):
            raise InputError('compose_user_string_or_integer_required')
        for field in ['user', 'read_only', 'privileged']:
            if field not in service:
                omissions.append('service_' + str(i) + '_missing_' + field)
        cases = [
            ('CMP001', 'high', 'privileged', service.get('privileged') is True,
             'privileged explicitly enabled', ['PR.PS-01'], ['T1611'], ['D3-EI']),
            ('CMP002', 'medium', 'network_mode', service.get('network_mode') == 'host',
             'host network namespace requested', ['PR.IR-01'], [], ['D3-EI']),
            ('CMP003', 'high', 'cap_add', any(c.upper().removeprefix('CAP_') in ('ALL', 'SYS_ADMIN') for c in caps),
             'ALL or SYS_ADMIN capability requested', ['PR.PS-01'], ['T1611'], ['D3-EI']),
            ('CMP006', 'medium', 'read_only', service.get('read_only') is False,
             'root filesystem explicitly writable', ['PR.PS-01'], [], [])]
        first = str(user).split(':', 1)[0].strip() if user is not None else ''
        is_root = first == 'root' or (first.isascii() and first.isdecimal() and int(first) == 0)
        cases.append(('CMP005', 'medium', 'user', is_root,
                      'container user explicitly root or UID zero; host mapping unresolved',
                      ['PR.AA-05'], [], []))
        for rule, severity, field, matched, predicate, csf, attack, d3 in cases:
            if matched:
                findings.append(finding(rule, severity, {'service_index': i, 'field': field},
                                        predicate, csf, attack, d3))
        volumes = service.get('volumes', [])
        if not isinstance(volumes, list):
            raise InputError('compose_volume_list_required')
        for j, volume in enumerate(volumes):
            if isinstance(volume, str):
                source = volume.split(':', 1)[0] if ':' in volume else ''
            elif isinstance(volume, dict):
                if volume.get('type') not in ('bind', 'volume', 'tmpfs', 'image', 'npipe', 'cluster'):
                    raise InputError('unsupported_compose_mount_type')
                source = volume.get('source', '') if volume['type'] == 'bind' else ''
                if not isinstance(source, str):
                    raise InputError('compose_mount_source_string_required')
            else:
                raise InputError('invalid_compose_volume')
            if source == '/' or (source.startswith('/') and source.endswith('/docker.sock')):
                findings.append(finding('CMP004', 'high',
                    {'service_index': i, 'field': 'volumes', 'volume_index': j},
                    'host root or potential Docker management socket bind; read-only does not establish safe API access',
                    ['PR.PS-01'], ['T1611'], ['D3-EI']))
    return findings, sorted(set(omissions))


def main():
    parser = argparse.ArgumentParser(description='Offline JSON checks on explicitly allowed local files; not a compliance audit.')
    parser.add_argument('--root', required=True, help='Trusted local directory containing sanitized copies')
    parser.add_argument('--kind', required=True, choices=['iam', 'compose'])
    parser.add_argument('files', nargs='+', help='Exact relative JSON filenames; no recursion')
    args = parser.parse_args()
    root = Path(args.root).absolute()
    report = {'schema_version': 1, 'kind': args.kind, 'files': [],
              'limitations': 'Static subset only. No finding is not proof of security or compliance.'}
    if len(args.files) > MAX_FILES or len(set(args.files)) != len(args.files):
        print(json.dumps({**report, 'status': 'input_error', 'error': 'invalid_file_count_or_duplicates'}))
        return 2
    for name in args.files:
        entry = {'source': name, 'findings': [], 'not_evaluated': []}
        try:
            if root.is_symlink() or not root.is_dir():
                raise InputError('invalid_review_root')
            raw = read_scoped(root, name)
            entry['sha256'] = hashlib.sha256(raw).hexdigest()
            doc = json.loads(raw, object_pairs_hook=unique_object,
                             parse_constant=reject_nonfinite, parse_float=finite_float)
            checker = audit_iam if args.kind == 'iam' else audit_compose
            findings, omissions = checker(doc)
            entry.update(status='checked', findings=findings, not_evaluated=omissions)
        except InputError as error:
            entry.update(status='input_error', error=str(error))
        except (OSError, UnicodeError, ValueError, RecursionError):
            entry.update(status='input_error', error='unreadable_or_invalid_json')
        report['files'].append(entry)
    summary = {'files_requested': len(args.files),
               'files_read': sum('sha256' in f for f in report['files']),
               'findings': sum(len(f['findings']) for f in report['files']),
               'input_errors': sum(f['status'] == 'input_error' for f in report['files'])}
    report['summary'] = summary
    report['status'] = ('incomplete' if summary['input_errors'] else
                        'findings' if summary['findings'] else 'no_findings_in_supported_checks')
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2 if summary['input_errors'] else 1 if summary['findings'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
