# Interop CLI examples

From the repository root:

```bash
python3 -m pip install ./packages/python
fedbpp import fhir examples/interop/python/fhir-input.json --output /tmp/actual.json --report /tmp/report.json
fedbpp export fhir /tmp/actual.json --output /tmp/fhir-output.json --allow-lossy
```
