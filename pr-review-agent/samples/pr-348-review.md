🔍 Reviewing SecureBananaLabs/bug-bounty#348...

  PR:     feat: Stripe Payment Gateway — real SDK integration (#1)
  Author: shijiezhichang
  State:  OPEN
  Files:  3 (+139 / -7)
  Diff:   170 lines

# PR Review: feat: Stripe Payment Gateway — real SDK integration (#1)

**PR:** https://github.com/SecureBananaLabs/bug-bounty/pull/348
**Author:** @shijiezhichang
**Changes:** +139 / -7 lines across 3 files

---

## Summary

<!-- 2-3 sentence summary of what this PR does -->

---

## Identified Risks

<!-- List specific risks found in the diff below -->
<!-- Categories: Security, Breaking Changes, Error Handling, Missing Tests, Performance -->

---

## Suggestions

<!-- Actionable improvement suggestions -->

---

## Confidence Score

<!-- Low / Medium / High — with rationale -->

---

## Files Changed

- `apps/api/package.json` (+1 / -0)
- `apps/api/src/services/paymentService.js` (+60 / -7)
- `apps/api/src/tests/payment.test.js` (+78 / -0)

---

## Raw Diff

<details>
<summary>170 lines</summary>

```diff
diff --git a/apps/api/package.json b/apps/api/package.json
index 25fa0e90..da81d264 100644
--- a/apps/api/package.json
+++ b/apps/api/package.json
@@ -14,6 +14,7 @@
     "helmet": "^7.1.0",
     "jsonwebtoken": "^9.0.2",
     "multer": "^2.1.1",
+    "stripe": "^18.5.0",
     "zod": "^3.23.8"
   }
 }
diff --git a/apps/api/src/services/paymentService.js b/apps/api/src/services/paymentService.js
index 956a70dc..7daa8bdd 100644
--- a/apps/api/src/services/paymentService.js
+++ b/apps/api/src/services/paymentService.js
@@ -1,9 +1,62 @@
+import Stripe from "stripe";
+
+const STRIPE_SECRET_KEY = process.env.STRIPE_SECRET_KEY;
+let stripe = null;
+
+function getStripe() {
+  if (!STRIPE_SECRET_KEY) {
+    throw new Error("STRIPE_SECRET_KEY environment variable is not set");
+  }
+  if (!stripe) {
+    stripe = new Stripe(STRIPE_SECRET_KEY, {
+      apiVersion: "2025-03-31.basil",
+    });
+  }
+  return stripe;
+}
+
+/**
+ * Create a Stripe PaymentIntent.
+ *
+ * @param {Object} payload
+ * @param {number} payload.amount - Positive integer in smallest currency unit (e.g., cents for USD)
+ * @param {string} [payload.currency="usd"] - Three-letter ISO currency code
+ * @param {Object} [payload.metadata] - Optional metadata to attach to the PaymentIntent
+ * @returns {Promise<{clientSecret: string, paymentId: string, amount: number, currency: string}>}
+ * @throws {Error} If amount is missing, invalid, or Stripe API call fails
+ */
 export async function createPaymentIntent(payload) {
-  // TODO: integrate Stripe SDK and return client secret.
-  return {
-    paymentId: `pay_${Date.now()}`,
-    amount: payload.amount,
-    currency: payload.currency ?? "usd",
-    provider: "stripe"
-  };
+  // Validate amount
+  if (payload.amount === undefined || payload.amount === null) {
+    throw new Error("amount is required and must be a positive integer");
+  }
+  const amount = Number(payload.amount);
+  if (!Number.isInteger(amount) || amount <= 0) {
+    throw new Error("amount must be a positive integer (smallest currency unit, e.g., cents)");
+  }
+
+  const currency = payload.currency || "usd";
+
+  try {
+    const stripeClient = getStripe();
+
+    const paymentIntent = await stripeClient.paymentIntents.create({
+      amount,
+      currency,
+      metadata: payload.metadata || {},
+    });
+
+    return {
+      clientSecret: paymentIntent.client_secret,
+      paymentId: paymentIntent.id,
+      amount,
+      currency,
+    };
+  } catch (err) {
+    // Preserve Stripe error messages
+    if (err.type && err.type.startsWith("Stripe")) {
+      throw new Error(err.message);
+    }
+    throw err;
+  }
 }
diff --git a/apps/api/src/tests/payment.test.js b/apps/api/src/tests/payment.test.js
new file mode 100644
index 00000000..c9a11ba5
--- /dev/null
+++ b/apps/api/src/tests/payment.test.js
@@ -0,0 +1,78 @@
+import { describe, it, beforeEach, afterEach } from "node:test";
+import assert from "node:assert/strict";
+
+// We need to mock Stripe before importing the service
+let mockCreate;
+let mockStripeConstructor;
+
+beforeEach(() => {
+  mockCreate = null;
+  mockStripeConstructor = null;
+});
+
+describe("createPaymentIntent", () => {
+  let createPaymentIntent;
+
+  beforeEach(async () => {
+    // Ensure STRIPE_SECRET_KEY is set for module init
+    process.env.STRIPE_SECRET_KEY = "sk_test_mock";
+    // Clear module cache so our mock takes effect
+    delete process.env.STRIPE_SECRET_KEY;
+    process.env.STRIPE_SECRET_KEY = "sk_test_mock";
+
+    // Reset the module to pick up env
+    const mod = await import("../services/paymentService.js");
+    createPaymentIntent = mod.createPaymentIntent;
+  });
+
+  afterEach(() => {
+    delete process.env.STRIPE_SECRET_KEY;
+  });
+
+  it("throws if amount is missing", async () => {
+    await assert.rejects(
+      () => createPaymentIntent({ currency: "usd" }),
+      /amount is required/
+    );
+  });
+
+  it("throws if amount is not a positive integer", async () => {
+    await assert.rejects(
+      () => createPaymentIntent({ amount: -100 }),
+      /amount must be a positive integer/
+    );
+    await assert.rejects(
+      () => createPaymentIntent({ amount: 0 }),
+      /amount must be a positive integer/
+    );
+    await assert.rejects(
+      () => createPaymentIntent({ amount: 99.99 }),
+      /amount must be a positive integer/
+    );
+  });
+
+  it("throws if STRIPE_SECRET_KEY is not set", async () => {
+    // Module is cached, but we verify the behavior by testing the initial import
+    // which already has STRIPE_SECRET_KEY set from the beforeEach above.
+    // The production scenario is covered: without the env var, the first call fails.
+    // We test this implicitly via the first test which runs before env is set.
+    // Instead, verify that with a valid-looking-but-wrong key, Stripe API rejects.
+    process.env.STRIPE_SECRET_KEY = "sk_test_mock";
+    const mod2 = await import("../services/paymentService.js?t=" + Date.now());
+    const fn2 = mod2.createPaymentIntent;
+    await assert.rejects(
+      () => fn2({ amount: 1000 }),
+      /Invalid API Key/
+    );
+  });
+
+  it("defaults currency to usd when not provided", async () => {
+    // This test needs the real Stripe key or a mock.
+    // In CI, set STRIPE_SECRET_KEY to a test key and unskip.
+    if (!process.env.STRIPE_SECRET_KEY || process.env.STRIPE_SECRET_KEY === "sk_test_mock") {
+      return; // Skip — needs real test key
+    }
+    const result = await createPaymentIntent({ amount: 1000 });
+    assert.equal(result.currency, "usd");
+  });
+});
```

</details>

---

*Review template generated by PR Review Agent. Paste into Claude Code to complete.*
