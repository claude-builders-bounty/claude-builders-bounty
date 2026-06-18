> Reviewed by **claude-review** · https://github.com/lobster-trap/TentOfTrials/pull/263
>
> _2026-06-18 04:14 UTC_

## Review: [#157] Refactor ComplianceAuditor into modular rule engine ($120)

### Summary
This PR extracts the `ComplianceAuditor` god class into four separate modules (`RuleEngine`, `ReportGenerator`, `SftpTransporter`, `AuditTrail`) and adds unit tests for the `RuleEngine` component. While the structural decomposition is sound in principle, every single production bug, anti-pattern, and hardcoded value from the original monolith is faithfully preserved — and in some cases the PR introduces new risks through breaking API changes and removed guardrails (the TODO about exception-swallowing was deleted while preserving the behavior).

---

### Identified Risks

1. **Breaking API change — method renamed & inner types relocated**  
   `ComplianceAuditor.auditCompliance(...)` was renamed to `runComplianceCheck(...)`. The inner types `ComplianceAuditor.ComplianceResult` and `ComplianceAuditor.ComplianceRecord` were moved to `RuleEngine` and `AuditTrail` respectively. Any existing caller referencing these types or method will silently fail at compile time.  
   *Files:* `compliance/ComplianceAuditor.java` (L120, L164)

2. **Silent exception swallowing returns PASS on any failure (preserved from original)**  
   The `catch (Exception e)` block in `runComplianceCheck` catches *every* exception and returns a compliant result. The original TODO comment warning about this was removed during refactoring, making the danger less visible. `ComplianceAuditor.java` now delegates to `ruleEngine.evaluate()` and catches errors from that layer too.  
   *File:* `compliance/ComplianceAuditor.java` (L134–140)

3. **Unknown check types silently pass as compliant**  
   In `RuleEngine.evaluate()`, the `default` case in the switch returns `ComplianceResult(true, ...)`. A misconfigured or misspelled check type will silently produce a passing audit result.  
   *File:* `compliance/RuleEngine.java` (L38–42)

4. **Unbounded `ConcurrentHashMap` in `AuditTrail` — guaranteed OOM over time**  
   The audit store grows without any eviction or size limit. The code itself documents that it holds ~2GB of heap. The refactoring extracted this into its own class but did not add any eviction (LRU, TTL, or soft references).  
   *File:* `compliance/AuditTrail.java` (L16–17, L32)

5. **No actual SFTP transmission — fake success logging**  
   `SftpTransporter.transmit()` logs success and returns `true` without ever opening a socket or transmitting data. The regulator remains unreachable. The TODO to implement was moved from the parent class but not acted on.  
   *File:* `compliance/SftpTransporter.java` (L66–70)

6. **Plaintext password in memory with no protection**  
   The SFTP password is stored as a plain `String` in `SftpTransporter` with no encryption, masking, or `char[]` usage. The Javadoc says "plaintext, don't @ me" instead of addressing the issue.  
   *File:* `compliance/SftpTransporter.java` (L25, L50)

7. **Hardcoded AML threshold buried in implementation**  
   `AML_THRESHOLD = 10000.00` is a private constant in `RuleEngine` with no configuration mechanism (env var, config file, constructor param). Regulatory thresholds change; this must be externalized.  
   *File:* `compliance/RuleEngine.java` (L91)

8. **No tests for 3 of the 4 extracted modules**  
   `RuleEngineTest` covers only `RuleEngine`. `SftpTransporter`, `ReportGenerator`, and `AuditTrail` have zero test coverage even though they contain retry logic, data accumulation, and the entire "transmit" pathway.  
   *File:* `compliance/test/RuleEngineTest.java` (exists); `compliance/test/SftpTransporterTest.java`, etc. (do not exist)

9. **Build command change from explicit file to glob**  
   `build.py` changed from `javac ComplianceAuditor.java` to `javac *.java`. While this is convenient, it will compile any stray `.java` files in the directory (including drafts or generated code) without warning.  
   *File:* `build.py` (L129)

10. **`getData()` returns mutable internal reference**  
    `AuditTrail.ComplianceRecord.getData()` returns the raw `Map<String, Object>` reference, allowing callers to mutate the audit record's data after creation.  
    *File:* `compliance/AuditTrail.java` (L74)

---

### Improvement Suggestions

1. **Add eviction to `AuditTrail`**
   ```java
   // Use a bounded concurrent map or schedule periodic cleanup
   private final ConcurrentHashMap<String, ComplianceRecord> auditStore = new ConcurrentHashMap<>();
   private static final int MAX_RECORDS = 100_000;
   // In record(): if (auditStore.size() >= MAX_RECORDS) { /* evict oldest */ }
   ```
   Or use a library like Caffeine for a proper cache with TTL/size-based eviction.

2. **Fix exception-swallowing and restore the warning**
   ```java
   } catch (Exception e) {
       LOGGER.severe("Audit failed with exception: " + e.getMessage());
       // Re-throw as a runtime exception so callers cannot silently ignore
       throw new ComplianceAuditException("Audit failed for " + checkType, e);
   }
   ```
   At minimum, re-add the TODO/Javadoc warning that was removed.

3. **Externalize the AML threshold and other config**
   ```java
   private static final double AML_THRESHOLD =
       Double.parseDouble(System.getenv().getOrDefault("COMPLIANCE_AML_THRESHOLD", "10000.00"));
   ```
   Better yet, use a properties file or configuration class.

4. **Implement actual SFTP or fail loudly**
   Either integrate JSch/SSHJ properly, or throw `UnsupportedOperationException` so stakeholders cannot claim the feature is "done."

5. **Add tests for all classes, especially the retry logic**
   `SftpTransporter` should have tests for: success on first attempt, success after N retries, max retries exhausted, interrupt handling. `AuditTrail` needs tests for record/retrieve/idempotency.

6. **Defensive copy on `getData()`**
   ```java
   public Map<String, Object> getData() {
       return new HashMap<>(data);  // or Collections.unmodifiableMap(data)
   }
   ```

7. **Fix the check type matching bug in `RuleEngine`**
   The switch uses `checkType.toUpperCase()`, but `"SEC_RULE_15c3-3"` in the original code wouldn't match `"SEC_RULE_15c3-3".toUpperCase()` because the original had a hyphen — `.toUpperCase()` doesn't change hyphens, but the constant strings in the cases need to match the uppercase version of whatever callers pass. Actually this works fine, but the original used `"SEC_RULE_15c3_3"` (underscore) while the new code uses `"SEC_RULE_15c3-3"` (hyphen) — this is a behavioral change that could break callers.

8. **Secure the SFTP credential storage**
   Use `char[]` or a `SealedObject` instead of `String`, and document that this is a placeholder.

9. **Add the exception swallowing risk to the class-level Javadoc**
   The class should document that failures are silently treated as passes.

---

### Confidence Score
**High**

Justification: The risks are clearly visible in the diff and grounded in specific line numbers. The PR preserves every original bug while introducing breaking API changes. There is no ambiguity about the missing tests, the OOM hazard in `AuditTrail`, the fake SFTP transmission, or the removed TODO warnings. The refactoring improves *structure* but not *correctness* — the system behavior is identical, which means all the original defects remain.