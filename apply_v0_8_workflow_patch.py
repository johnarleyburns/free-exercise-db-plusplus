from pathlib import Path
p=Path(".github/workflows/build-db.yml"); s=p.read_text()
for marker in ['      - "tests/**"\n','      - "verify_reproducible_build.py"\n','      - "METHODOLOGY.md"\n','      - "VERSIONING.md"\n']:
    if marker not in s:
        s=s.replace('      - "free-exercise-db-plusplus.schema.json"\n','      - "free-exercise-db-plusplus.schema.json"\n'+marker)
steps='''      - name: Verify reproducible build
        run: python verify_reproducible_build.py exercises.json --schema free-exercise-db-plusplus.schema.json
      - name: Verify release contract
        run: python tests/test_release_contract.py free-exercise-db-plusplus.json
'''
anchor='      - name: Generate review reports\n'
if steps not in s: s=s.replace(anchor,steps+anchor)
p.write_text(s)
print("patched",p)
