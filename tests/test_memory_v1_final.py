from pathlib import Path
import sys,unittest,tempfile,shutil,subprocess,json,hashlib,io,tarfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from memorylib.frontmatter import parse_frontmatter
from memorylib.registry import Registry
from memorylib.validate import validate
from memorylib.dashboard import render_all
from memorylib.context import build_context
from memorylib.acceptance import tree_fingerprint
from memorylib.changeset import apply

class T(unittest.TestCase):
    def test_01_parse_scalar(self):
        self.assertEqual(parse_frontmatter('---\nid: X\ntype: component\nstatus: active\n---\n')[0]['id'],'X')
    def test_02_parse_list(self):
        self.assertEqual(parse_frontmatter('---\na:\n  - X\n---\n')[0]['a'],['X'])
    def test_03_nested_mapping_rejected(self):
        with self.assertRaises(ValueError):
            parse_frontmatter('---\na:\n  b: c\n---\n')
    def test_04_registry_ids(self):
        self.assertGreaterEqual(len(Registry(ROOT).scan().by_id),80)
    def test_05_validator_green(self):
        render_all(ROOT)
        r=validate(ROOT,'v1')
        self.assertEqual((r.errors,r.warnings),(0,0))
    def test_06_one_current_state(self):
        self.assertEqual(len([o for o in Registry(ROOT).scan().objects if o.object_type=='project-state' and o.status=='current']),1)
    def test_07_one_approved_task_active(self):
        active=[o for o in Registry(ROOT).scan().objects if o.object_type=='task' and o.status in {'approved','active'}]
        self.assertEqual(len(active),1)
        self.assertEqual(active[0].object_id,'TASK-P0B-002')
    def test_08_current_task_shows_approved(self):
        render_all(ROOT)
        self.assertIn('TASK-P0B-002',(ROOT/'CURRENT_TASK.md').read_text())
    def test_09_p0a_closed(self):
        self.assertIn('status: closed',(ROOT/'workstreams/P0-A.md').read_text())
    def test_10_p0a_findings_resolved(self):
        r=Registry(ROOT).scan()
        self.assertTrue(all(r.by_id[f'FND-20260814-{i:03d}'].status=='resolved_production' for i in range(1,5)))
    def test_11_open_view_excludes_p0a(self):
        render_all(ROOT)
        self.assertNotIn('FND-20260814-001',(ROOT/'findings/OPEN.md').read_text())
    def test_12_resolved_view_includes_p0a(self):
        render_all(ROOT)
        self.assertIn('FND-20260814-001',(ROOT/'findings/RESOLVED.md').read_text())
    def test_13_home_generated(self):
        render_all(ROOT)
        self.assertIn('SportsBrain Home',(ROOT/'00_HOME.md').read_text())
    def test_14_mocs_generated(self):
        render_all(ROOT)
        self.assertGreaterEqual(len(list((ROOT/'mocs').glob('*.md'))),15)
    def test_15_source_map_generated(self):
        render_all(ROOT)
        self.assertIn('src/monitoring/health_writer.py',(ROOT/'views/SOURCE_MAP.md').read_text())
    def test_16_tasks_view(self):
        render_all(ROOT)
        self.assertIn('TASK-P0B-001',(ROOT/'views/TASKS.md').read_text())
    def test_17_approved_task_context_executable(self):
        c=build_context(ROOT,'TASK-P0B-002')
        self.assertIsNotNone(c)
        self.assertGreater(c.estimated_tokens,0)
    def test_18_approved_task_fits_budget(self):
        c=build_context(ROOT,'TASK-P0B-002')
        self.assertLess(c.estimated_tokens,8000)
    def test_19_all_drafts_preview_fit(self):
        r=Registry(ROOT).scan()
        for o in [x for x in r.objects if x.object_type=='task' and x.status=='draft']:
            c=build_context(ROOT,o.object_id,allow_draft=True)
            self.assertLessEqual(c.estimated_tokens,c.hard_limit)
    def test_20_provenance_separate(self):
        s=Registry(ROOT).scan().by_id['STATE-20260816-001']
        self.assertNotEqual(s.meta['source_release_sha'],s.meta['runtime_data_head'])
    def test_21_writer_classes(self):
        self.assertEqual(len([o for o in Registry(ROOT).scan().objects if o.object_type=='writer-class']),5)
    def test_22_jobs(self):
        self.assertGreaterEqual(len([o for o in Registry(ROOT).scan().objects if o.object_type=='job']),12)
    def test_23_generated_idempotent(self):
        render_all(ROOT)
        a=tree_fingerprint(ROOT)
        render_all(ROOT)
        b=tree_fingerprint(ROOT)
        self.assertEqual(a,b)
    def test_24_changeset_path_traversal(self):
        with self.assertRaises(ValueError):
            apply(ROOT,{'operations':[{'op':'create','path':'../evil','content':'x'}]},dry_run=True)
    def test_25_no_hardcoded_159(self):
        self.assertNotIn('expected 159',(ROOT/'tools/memorylib/validate.py').read_text())
    def test_26_backup_dir_excluded_from_fingerprint(self):
        before=tree_fingerprint(ROOT)
        p=ROOT/'.memory-backups'/'fingerprint-test'/'shadow.md'
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text('backup-only\n',encoding='utf-8')
        try:
            self.assertEqual(tree_fingerprint(ROOT),before)
        finally:
            p.unlink(missing_ok=True)
            try: p.parent.rmdir()
            except OSError: pass

    def test_27_installer_package_manifest_semantics(self):
        """Package manifest integrity is verified against the immutable install-time git snapshot.

        The live repo evolves after installation; the manifest records the immutable
        install-time content. This test pins verification to the git commit that installed
        the manifest rather than the evolving live tree, preserving fail-closed semantics
        without requiring perpetual live/manifest equality.
        """
        manifest_path=ROOT/'_meta'/'PACKAGE_MANIFEST.json'
        manifest=json.loads(manifest_path.read_text())
        self.assertIn('content_fingerprint',manifest)
        self.assertIn('files',manifest)
        self.assertIsInstance(manifest['files'],list)
        self.assertEqual(manifest['file_count'],len(manifest['files']))

        r=subprocess.run(
            ['git','-C',str(ROOT),'log','-1','--format=%H','--','_meta/PACKAGE_MANIFEST.json'],
            capture_output=True,text=True)
        install_sha=r.stdout.strip()
        self.assertTrue(install_sha,'could not determine manifest install commit via git log')

        td=Path(tempfile.mkdtemp(prefix='sbmem-pkg-snap-'))
        try:
            r2=subprocess.run(
                ['git','-C',str(ROOT),'archive',install_sha,'--format=tar'],
                capture_output=True)
            self.assertEqual(r2.returncode,0,'git archive of install snapshot failed')
            with tarfile.open(fileobj=io.BytesIO(r2.stdout)) as tf:
                tf.extractall(td)
            expected={x['path']:x for x in manifest['files'] if isinstance(x,dict) and x.get('path')}
            for rel,meta in expected.items():
                p=td/rel
                self.assertTrue(p.exists(),f'package file missing in snapshot: {rel}')
                actual_sha=hashlib.sha256(p.read_bytes()).hexdigest()
                self.assertEqual(actual_sha,meta['sha256'],f'sha256 mismatch: {rel}')
                self.assertEqual(p.stat().st_size,meta['bytes'],f'size mismatch: {rel}')
            h=hashlib.sha256()
            excl={'.memory-build','__pycache__','.git','.memory-backups','.claude','.obsidian'}
            meta_excl={'_meta/ACCEPTANCE_REPORT.json','_meta/PACKAGE_MANIFEST.json','.DS_Store'}
            for p in sorted(td.rglob('*')):
                rel_p=p.relative_to(td)
                if (not p.is_file() or any(x in excl for x in rel_p.parts)
                        or p.suffix=='.pyc' or rel_p.as_posix() in meta_excl):
                    continue
                h.update(rel_p.as_posix().encode()); h.update(b'\0')
                h.update(p.read_bytes()); h.update(b'\0')
            self.assertEqual(h.hexdigest(),manifest['content_fingerprint'])
        finally:
            shutil.rmtree(td,ignore_errors=True)

    def test_28_local_claude_and_obsidian_state_are_unmanaged(self):
        before=tree_fingerprint(ROOT)
        created=[]
        try:
            for rel,content in [
                ('.claude/settings.local.json','{"local":true}\n'),
                ('.obsidian/workspace.json','{}\n'),
                ('.DS_Store','local-ui-state\n'),
            ]:
                q=ROOT/rel
                if not q.exists():
                    q.parent.mkdir(parents=True,exist_ok=True)
                    q.write_text(content,encoding='utf-8')
                    created.append(q)
            self.assertEqual(tree_fingerprint(ROOT),before)
        finally:
            for q in reversed(created):
                q.unlink(missing_ok=True)
                parent=q.parent
                while parent!=ROOT:
                    try: parent.rmdir()
                    except OSError: break
                    parent=parent.parent

    def test_29_late_p0a_findings_are_production_resolved(self):
        r=Registry(ROOT).scan()
        for fid in ('FND-20260814-030','FND-20260814-031'):
            self.assertIn(fid,r.by_id)
            self.assertEqual(r.by_id[fid].status,'resolved_production')

    def test_30_idle_state_zero_active_valid(self):
        td=Path(tempfile.mkdtemp(prefix='sbmem-idle-'))
        try:
            shutil.copytree(ROOT,td,dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('.git','__pycache__','.memory-backups','.memory-build','*.pyc'))
            t=(td/'tasks/records/TASK-P0B-002.md')
            t.write_text(t.read_text().replace('status: approved','status: draft'))
            result=render_all(td)
            self.assertEqual(result['active_tasks'],0)
            self.assertIn('**NONE**',(td/'CURRENT_TASK.md').read_text())
        finally:
            shutil.rmtree(td,ignore_errors=True)

    def test_31_two_active_tasks_rejected(self):
        td=Path(tempfile.mkdtemp(prefix='sbmem-twotask-'))
        try:
            shutil.copytree(ROOT,td,dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('.git','__pycache__','.memory-backups','.memory-build','*.pyc'))
            t3=(td/'tasks/records/TASK-P0B-003.md')
            t3.write_text(t3.read_text().replace('status: draft','status: approved'))
            with self.assertRaises(RuntimeError):
                render_all(td)
        finally:
            shutil.rmtree(td,ignore_errors=True)

    def test_32_current_task_matches_approved(self):
        render_all(ROOT)
        reg=Registry(ROOT).scan()
        active=[o for o in reg.objects if o.object_type=='task' and o.status in {'approved','active'}]
        self.assertEqual(len(active),1)
        self.assertIn(active[0].object_id,(ROOT/'CURRENT_TASK.md').read_text())

    def test_33_draft_task_still_blocked(self):
        with self.assertRaises(RuntimeError):
            build_context(ROOT,'TASK-P0B-003')

    def test_34_task_mem_v1_accept_completed(self):
        r=Registry(ROOT).scan()
        self.assertEqual(r.by_id['TASK-MEM-V1-ACCEPT'].status,'completed')

    def test_35_ws_p0b_active(self):
        r=Registry(ROOT).scan()
        self.assertEqual(r.by_id['WS-P0-B'].status,'active')

    def test_36_current_priorities_no_memory_install(self):
        render_all(ROOT)
        text=(ROOT/'CURRENT_PRIORITIES.md').read_text()
        self.assertNotIn('Accept/install SportsBrainMemory V1',text)
        self.assertIn('TASK-P0B-002',text)

    def test_38_p0b1_completed(self):
        r=Registry(ROOT).scan()
        self.assertEqual(r.by_id['TASK-P0B-001'].status,'completed')

    def test_39_p0b2_approved(self):
        r=Registry(ROOT).scan()
        self.assertEqual(r.by_id['TASK-P0B-002'].status,'approved')

    def test_40_fnd_005_resolved_production(self):
        r=Registry(ROOT).scan()
        self.assertEqual(r.by_id['FND-20260814-005'].status,'resolved_production')

    def test_41_evd_p0b1_prod_exists(self):
        r=Registry(ROOT).scan()
        self.assertIn('EVD-P0B-001-PROD-001',r.by_id)
        self.assertEqual(r.by_id['EVD-P0B-001-PROD-001'].status,'current')

    def test_42_ver_p0b1_prod_exists(self):
        r=Registry(ROOT).scan()
        self.assertIn('VER-P0B-001-PROD-001',r.by_id)
        self.assertEqual(r.by_id['VER-P0B-001-PROD-001'].meta.get('verification_status'),'verified')

    def test_43_p0b1_source_release_sha(self):
        r=Registry(ROOT).scan()
        st=r.by_id['STATE-20260816-001']
        self.assertEqual(st.meta.get('source_release_sha'),'5dc8ff7dd7434420ad856187fdde74d98dc04dbc')

    def test_44_priority_order_p0c_before_model_integrity(self):
        render_all(ROOT)
        text=(ROOT/'CURRENT_PRIORITIES.md').read_text()
        self.assertIn('P0-C',text)
        self.assertIn('P0-D',text)
        self.assertIn('MODEL-INTEGRITY',text)
        idx_p0c=text.index('P0-C')
        idx_p0d=text.index('P0-D')
        idx_model=text.index('MODEL-INTEGRITY')
        self.assertLess(idx_p0c,idx_model,'P0-C must appear before MODEL-INTEGRITY in priorities')
        self.assertLess(idx_p0d,idx_model,'P0-D must appear before MODEL-INTEGRITY in priorities')

    def test_37_current_state_no_fixed_generated_timestamp(self):
        render_all(ROOT)
        text=(ROOT/'CURRENT_STATE.md').read_text()
        self.assertNotIn('last_updated: 2026-08-16T13:04:00+02:00',text)

if __name__=='__main__':
    unittest.main()
