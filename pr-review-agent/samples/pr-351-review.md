🔍 Reviewing SecureBananaLabs/bug-bounty#351...

  PR:     feat: implement Stripe payment gateway — #1
  Author: shijiezhichang
  State:  OPEN
  Files:  6 (+203 / -10)
  Diff:   285 lines

# PR Review: feat: implement Stripe payment gateway — #1

**PR:** https://github.com/SecureBananaLabs/bug-bounty/pull/351
**Author:** @shijiezhichang
**Changes:** +203 / -10 lines across 6 files

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
- `apps/api/src/controllers/paymentController.js` (+3 / -1)
- `apps/api/src/services/paymentService.js` (+45 / -7)
- `apps/api/src/tests/payment.test.js` (+128 / -0)
- `apps/api/src/validators/payment.js` (+6 / -0)
- `package-lock.json` (+20 / -2)

---

## Raw Diff

<details>
<summary>285 lines</summary>

```diff
diff --git a/apps/api/package.json b/apps/api/package.json
index 25fa0e90..fed0bdc0 100644
--- a/apps/api/package.json
+++ b/apps/api/package.json
@@ -14,6 +14,7 @@
     "helmet": "^7.1.0",
     "jsonwebtoken": "^9.0.2",
     "multer": "^2.1.1",
+    "stripe": "^22.1.1",
     "zod": "^3.23.8"
   }
 }
diff --git a/apps/api/src/controllers/paymentController.js b/apps/api/src/controllers/paymentController.js
index 138f909e..57b981b8 100644
--- a/apps/api/src/controllers/paymentController.js
+++ b/apps/api/src/controllers/paymentController.js
@@ -1,6 +1,8 @@
 import { ok } from "../utils/response.js";
+import { createPaymentSchema } from "../validators/payment.js";
 import { createPaymentIntent } from "../services/paymentService.js";
 
 export async function createPayment(req, res) {
-  return ok(res, await createPaymentIntent(req.body), 201);
+  const payload = createPaymentSchema.parse(req.body);
+  return ok(res, await createPaymentIntent(payload), 201);
 }
diff --git a/apps/api/src/services/paymentService.js b/apps/api/src/services/paymentService.js
index 956a70dc..9ca34e8b 100644
--- a/apps/api/src/services/paymentService.js
+++ b/apps/api/src/services/paymentService.js
@@ -1,9 +1,47 @@
+let _stripe = null;
+
+/**
+ * Inject a Stripe client instance for testing.
+ * In production, the client is lazily created from STRIPE_SECRET_KEY.
+ */
+export function setStripeClient(client) {
+  _stripe = client;
+}
+
+async function getStripe() {
+  if (!_stripe) {
+    if (!process.env.STRIPE_SECRET_KEY) {
+      throw new Error("STRIPE_SECRET_KEY environment variable is not set");
+    }
+    const Stripe = (await import("stripe")).default;
+    _stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
+  }
+  return _stripe;
+}
+
 export async function createPaymentIntent(payload) {
-  // TODO: integrate Stripe SDK and return client secret.
-  return {
-    paymentId: `pay_${Date.now()}`,
-    amount: payload.amount,
-    currency: payload.currency ?? "usd",
-    provider: "stripe"
-  };
+  if (!payload.amount || typeof payload.amount !== "number" || !Number.isInteger(payload.amount) || payload.amount <= 0) {
+    throw new Error("amount must be a positive integer (smallest currency unit, e.g. cents)");
+  }
+
+  const currency = payload.currency ?? "usd";
+
+  try {
+    const stripe = await getStripe();
+    const paymentIntent = await stripe.paymentIntents.create({
+      amount: payload.amount,
+      currency,
+    });
+
+    return {
+      clientSecret: paymentIntent.client_secret,
+      paymentId: paymentIntent.id,
+    };
+  } catch (err) {
+    const StripeModule = await import("stripe");
+    if (err instanceof StripeModule.default.errors.StripeError) {
+      throw new Error(err.message);
+    }
+    throw err;
+  }
 }
diff --git a/apps/api/src/tests/payment.test.js b/apps/api/src/tests/payment.test.js
new file mode 100644
index 00000000..dc289356
--- /dev/null
+++ b/apps/api/src/tests/payment.test.js
@@ -0,0 +1,128 @@
+import test from "node:test";
+import assert from "node:assert/strict";
+import { createPaymentIntent, setStripeClient } from "../services/paymentService.js";
+
+// Reset between tests
+function resetClient() {
+  delete process.env.STRIPE_SECRET_KEY;
+  setStripeClient(null);
+}
+
+// --- Unit tests: input validation ---
+
+test("validates amount — rejects zero", async () => {
+  resetClient();
+  await assert.rejects(
+    () => createPaymentIntent({ amount: 0, currency: "usd" }),
+    { message: "amount must be a positive integer (smallest currency unit, e.g. cents)" },
+  );
+});
+
+test("validates amount — rejects negative", async () => {
+  resetClient();
+  await assert.rejects(
+    () => createPaymentIntent({ amount: -100, currency: "usd" }),
+    { message: "amount must be a positive integer (smallest currency unit, e.g. cents)" },
+  );
+});
+
+test("validates amount — rejects float", async () => {
+  resetClient();
+  await assert.rejects(
+    () => createPaymentIntent({ amount: 99.5, currency: "usd" }),
+    { message: "amount must be a positive integer (smallest currency unit, e.g. cents)" },
+  );
+});
+
+test("validates amount — rejects missing", async () => {
+  resetClient();
+  await assert.rejects(
+    () => createPaymentIntent({ currency: "usd" }),
+    { message: "amount must be a positive integer (smallest currency unit, e.g. cents)" },
+  );
+});
+
+test("validates amount — rejects NaN", async () => {
+  resetClient();
+  await assert.rejects(
+    () => createPaymentIntent({ amount: NaN, currency: "usd" }),
+    { message: "amount must be a positive integer (smallest currency unit, e.g. cents)" },
+  );
+});
+
+// --- Unit test: Stripe SDK mocked via dependency injection ---
+
+test("calls stripe.paymentIntents.create() with correct arguments", async (t) => {
+  const mockCreate = t.mock.fn(async ({ amount, currency }) => ({
+    id: "pi_mock_123",
+    client_secret: "pi_mock_123_secret_mock",
+  }));
+
+  setStripeClient({
+    paymentIntents: { create: mockCreate },
+  });
+
+  const result = await createPaymentIntent({ amount: 2500, currency: "eur" });
+
+  assert.equal(result.paymentId, "pi_mock_123");
+  assert.equal(result.clientSecret, "pi_mock_123_secret_mock");
+  assert.equal(mockCreate.mock.calls.length, 1, "create should be called once");
+  assert.deepEqual(mockCreate.mock.calls[0].arguments[0], { amount: 2500, currency: "eur" });
+
+  resetClient();
+});
+
+// --- Unit test: Stripe error handling ---
+
+test("re-throws Stripe errors with original message", async (t) => {
+  class StripeCardError extends Error {
+    constructor(opts) {
+      super(opts.message);
+      this.name = "StripeCardError";
+    }
+    get type() {
+      return "StripeCardError";
+    }
+  }
+
+  setStripeClient({
+    paymentIntents: {
+      create: t.mock.fn(async () => {
+        throw new StripeCardError({ message: "Your card was declined." });
+      }),
+    },
+  });
+
+  // The error won't be instanceof Stripe.errors.StripeError since we're not using Stripe import,
+  // but it will be caught by the generic catch and re-thrown.
+  await assert.rejects(
+    () => createPaymentIntent({ amount: 1000 }),
+    { message: "Your card was declined." },
+  );
+
+  resetClient();
+});
+
+// --- Unit test: Stripe key not set ---
+
+test("throws when STRIPE_SECRET_KEY not set", async () => {
+  resetClient();
+  await assert.rejects(
+    () => createPaymentIntent({ amount: 1000 }),
+    { message: "STRIPE_SECRET_KEY environment variable is not set" },
+  );
+});
+
+// --- Integration test (gated) ---
+
+test("integration: creates a real PaymentIntent in Stripe test mode", { skip: !process.env.RUN_STRIPE_INTEGRATION_TESTS }, async () => {
+  const key = process.env.STRIPE_SECRET_KEY;
+  if (!key || !key.startsWith("sk_test_")) {
+    assert.fail("STRIPE_SECRET_KEY must be a test mode key (sk_test_*) for integration tests");
+  }
+
+  const result = await createPaymentIntent({ amount: 1000, currency: "usd" });
+
+  assert.ok(result.paymentId.startsWith("pi_"), "paymentId should start with pi_");
+  assert.ok(result.clientSecret.startsWith("pi_"), "clientSecret should start with pi_");
+});
diff --git a/apps/api/src/validators/payment.js b/apps/api/src/validators/payment.js
new file mode 100644
index 00000000..9859cdc1
--- /dev/null
+++ b/apps/api/src/validators/payment.js
@@ -0,0 +1,6 @@
+import { z } from "zod";
+
+export const createPaymentSchema = z.object({
+  amount: z.number().int().positive("amount must be a positive integer (cents)"),
+  currency: z.string().length(3).default("usd"),
+});
diff --git a/package-lock.json b/package-lock.json
index a19a9928..6cfdfb71 100644
--- a/package-lock.json
+++ b/package-lock.json
@@ -19,6 +19,7 @@
         "helmet": "^7.1.0",
         "jsonwebtoken": "^9.0.2",
         "multer": "^2.1.1",
+        "stripe": "^22.1.1",
         "zod": "^3.23.8"
       }
     },
@@ -742,7 +743,7 @@
       "version": "22.15.19",
       "resolved": "https://registry.npmjs.org/@types/node/-/node-22.15.19.tgz",
       "integrity": "sha512-3vMNr4TzNQyjHcRZadojpRaD9Ofr6LsonZAoQ+HMUa/9ORTPoxVIw0e0mpqWpdjj8xybyCM+oKOUH2vwFu/oEw==",
-      "dev": true,
+      "devOptional": true,
       "license": "MIT",
       "dependencies": {
         "undici-types": "~6.21.0"
@@ -2053,6 +2054,23 @@
         "safe-buffer": "~5.2.0"
       }
     },
+    "node_modules/stripe": {
+      "version": "22.1.1",
+      "resolved": "https://registry.npmjs.org/stripe/-/stripe-22.1.1.tgz",
+      "integrity": "sha512-cmodIYP27tBkJ8G7DuGgWw0PFuemlFZbuF3Wwr1TrjFjUa3T7NIgCe6TVwX8BO2ynu+xtTuDGfHafNDCPt9lXA==",
+      "license": "MIT",
+      "engines": {
+        "node": ">=18"
+      },
+      "peerDependencies": {
+        "@types/node": ">=18"
+      },
+      "peerDependenciesMeta": {
+        "@types/node": {
+          "optional": true
+        }
+      }
+    },
     "node_modules/styled-jsx": {
       "version": "5.1.6",
       "resolved": "https://registry.npmjs.org/styled-jsx/-/styled-jsx-5.1.6.tgz",
@@ -2128,7 +2146,7 @@
       "version": "6.21.0",
       "resolved": "https://registry.npmjs.org/undici-types/-/undici-types-6.21.0.tgz",
       "integrity": "sha512-iwDZqg0QAGrg9Rav5H4n0M64c3mkR59cJ6wQp+7C4nI0gsmExaedaYLNO44eT4AtBBwjbTiGPMlt2Md0T9H9JQ==",
-      "dev": true,
+      "devOptional": true,
       "license": "MIT"
     },
     "node_modules/unpipe": {
```

</details>

---

*Review template generated by PR Review Agent. Paste into Claude Code to complete.*
