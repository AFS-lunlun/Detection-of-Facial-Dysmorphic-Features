# Public release contents

Upload only this prepared directory: code, README files, method/schema docs,
requirements/build configuration, license, synthetic examples, tests, scanner,
validation record and CI workflow. No repository has been created or uploaded.
No account, repository URL or personal author information is preconfigured.

Do not include private inputs or outputs, identity maps, original filenames,
photos, heatmaps, weights, clinical tables, correspondence, manuscript drafts,
credentials or unrelated research files. Pseudonymous manifests remain private.
The two synthetic examples are the only public CSVs allowed by the scanner.

```bash
python -m unittest discover -s tests -v
python tools/check_public_files.py
```

After staging in your own repository, review `git diff --cached --name-only` and
`git diff --cached`. Upload the contents of this directory, not the surrounding
research workspace. Ignore rules do not remove already tracked files and do not
protect files manually dragged into a web upload form.

The scan flags common absolute home paths, credentials, contact details and
unexpected/binary artifacts. It cannot certify anonymity or replace manual review.
MIT covers this code only, not third-party data or weights.
