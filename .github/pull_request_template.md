## Summary

- what changed
- why it changed

## Validation

- [ ] `python3 docs/validate_docs.py`
- [ ] `python3 -m unittest discover -s tests -p 'test_*.py'`
- [ ] `python3 smoke_test.py` if backend workflow behavior changed
- [ ] `python3 real_world_functional_test.py` if biology workflow behavior changed
- [ ] `npm run test:e2e` if UI behavior changed

## Docs And Tutorial Impact

- [ ] docs updated if user-facing behavior changed
- [ ] tutorial regenerated if tutorial content changed
- [ ] screenshots refreshed if visible UI changed

## Notes

- known limitations
- follow-up work
