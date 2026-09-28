# Free Exercise DB++ C health bridge

This is the portable C ABI for the full-health-data sidecar contract. It keeps
the canonical DB++ ACTUAL JSON byte-for-byte intact and lets a host application
attach it to a native record.

The C package intentionally does not vendor Garmin’s FIT SDK or pretend that
HealthKit/Health Connect are C APIs. Use Garmin’s official `fit-c-sdk` for FIT
binary messages; use an Objective-C/Swift host for HealthKit and an Android/JNI
host for Health Connect. Those hosts call this ABI to retain the exact DB++
document while using the platform projection.

Build and test:

```sh
cmake -S packages/c -B /tmp/fedbpp-c-build -DBUILD_TESTING=ON
cmake --build /tmp/fedbpp-c-build
ctest --test-dir /tmp/fedbpp-c-build --output-on-failure
```
