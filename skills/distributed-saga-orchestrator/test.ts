import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedSagaOrchestrator } from "./index.js";

describe("DistributedSagaOrchestrator Resilient Transactions", () => {
    it("executes all steps sequentially upon complete success", async () => {
        interface OrderContext {
            orderId: string;
            inventoryReserved: boolean;
            paymentProcessed: boolean;
            shipmentCreated: boolean;
        }

        const saga = new DistributedSagaOrchestrator<OrderContext>()
            .addStep({
                name: "ReserveInventory",
                action: (ctx) => { ctx.inventoryReserved = true; },
                compensate: (ctx) => { ctx.inventoryReserved = false; },
            })
            .addStep({
                name: "ProcessPayment",
                action: (ctx) => { ctx.paymentProcessed = true; },
                compensate: (ctx) => { ctx.paymentProcessed = false; },
            })
            .addStep({
                name: "CreateShipment",
                action: (ctx) => { ctx.shipmentCreated = true; },
                compensate: (ctx) => { ctx.shipmentCreated = false; },
            });

        const ctx: OrderContext = {
            orderId: "ord_100",
            inventoryReserved: false,
            paymentProcessed: false,
            shipmentCreated: false,
        };

        const result = await saga.execute("saga_01", ctx);

        assert.equal(result.status, "COMPLETED");
        assert.equal(ctx.inventoryReserved, true);
        assert.equal(ctx.paymentProcessed, true);
        assert.equal(ctx.shipmentCreated, true);
        assert.equal(result.journal.length, 3);
    });

    it("triggers backward compensation in reverse order when a step fails", async () => {
        interface PaymentContext {
            fundsDeducted: boolean;
            bonusPointsAwarded: boolean;
            externalApiSynced: boolean;
        }

        const saga = new DistributedSagaOrchestrator<PaymentContext>()
            .addStep({
                name: "DeductFunds",
                action: (ctx) => { ctx.fundsDeducted = true; },
                compensate: (ctx) => { ctx.fundsDeducted = false; },
            })
            .addStep({
                name: "AwardBonusPoints",
                action: (ctx) => { ctx.bonusPointsAwarded = true; },
                compensate: (ctx) => { ctx.bonusPointsAwarded = false; },
            })
            .addStep({
                name: "SyncExternalGateway",
                action: () => { throw new Error("Gateway timeout"); },
                compensate: () => {},
            });

        const ctx: PaymentContext = {
            fundsDeducted: false,
            bonusPointsAwarded: false,
            externalApiSynced: false,
        };

        const result = await saga.execute("saga_fail_02", ctx);

        assert.equal(result.status, "COMPENSATED");
        assert.equal(ctx.fundsDeducted, false);       // Rolled back
        assert.equal(ctx.bonusPointsAwarded, false); // Rolled back
        assert.ok(result.error?.includes("Gateway timeout"));
    });
});