from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from memorylib.frontmatter import parse_frontmatter
from memorylib.registry import Registry
from memorylib.validate import validate
from memorylib.dashboard import render_all
from memorylib.context import build_context
from memorylib.acceptance import tree_fingerprint
from memorylib.changeset import apply
from importlib.util import spec_from_file_location, module_from_spec

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
    def test_07_zero_active_task_valid(self):
        self.assertEqual(len([o for o in Registry(ROOT).scan().objects if o.object_type=='task' and o.status in {'approved','active'}]),0)
    def test_08_current_task_none(self):
        render_all(ROOT)
        self.assertIn('**NONE**',(ROOT/'CURRENT_TASK.md').read_text())
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
    def test_17_draft_context_blocked(self):
        with self.assertRaises(RuntimeError):
            build_context(ROOT,'TASK-P0B-001')
    def test_18_draft_preview_fits(self):
        self.assertLess(build_context(ROOT,'TASK-P0B-001',allow_draft=True).estimated_tokens,8000)
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
    def test_27_installer_manifest_integrity(self):
        spec=spec_from_file_location('install_v1',ROOT/'tools/install_v1.py')
        mod=module_from_spec(spec); spec.loader.exec_module(mod)
        manifest=mod.verify_package_manifest()
        self.assertEqual(manifest['content_fingerprint'],tree_fingerprint(ROOT))

    def test_28_local_claude_and_obsidian_state_are_unmanaged(self):
        spec=spec_from_file_location('install_v1_local_state',ROOT/'tools/install_v1.py')
        mod=module_from_spec(spec); spec.loader.exec_module(mod)
        before=tree_fingerprint(ROOT)
        created=[]
        try:
            for rel,content in [
                ('.claude/settings.local.json','{\"local\":true}\n'),
                ('.obsidian/workspace.json','{}\n'),
                ('.DS_Store','local-ui-state\n'),
            ]:
                q=ROOT/rel
                if not q.exists():
                    q.parent.mkdir(parents=True,exist_ok=True)
                    q.write_text(content,encoding='utf-8')
                    created.append(q)
            manifest=mod.verify_package_manifest()
            self.assertEqual(manifest['content_fingerprint'],before)
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

if __name__=='__main__':
    unittest.main()
