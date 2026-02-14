# Name collision notes

Distribution name: `axiomfusion-lang` (pip install name)  
Import package: `axiomfusion`

If you need to rename the import package too:
1) rename `src/axiomfusion/` to `src/<newname>/`
2) update imports + CLI entrypoint in `pyproject.toml`
