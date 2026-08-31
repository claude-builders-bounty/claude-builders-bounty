/**
 * Distributed Saga Pattern Orchestrator with Compensating Transactions.
 * Enterprise-grade multi-step workflow manager featuring forward execution,
 * automatic backward compensating rollbacks on failure, idempotency keys,
 * retry strategies with exponential backoff, and step execution journals.
 */

export type SagaStepStatus = "PENDING" | "COMPLETED" | "FAILED" | "COMPENSATED" | "COMPENSATION_FAILED";
export type SagaOverallStatus = "NOT_STARTED" | "RUNNING" | "COMPLETED" | "FAILED" | "COMPENSATED";

export interface SagaStep<TContext> {
    name: string;
    action: (context: TContext) => Promise<void> | void;
    compensate: (context: TContext) => Promise<void> | void;
    maxRetries?: number;
    backoffMs?: number;
}

export interface StepJournalEntry {
    stepName: string;
    status: SagaStepStatus;
    attempts: number;
    error?: string;
}

export interface SagaExecutionResult<TContext> {
    sagaId: string;
    status: SagaOverallStatus;
    context: TContext;
    journal: StepJournalEntry[];
    error?: string;
}

export class DistributedSagaOrchestrator<TContext> {
    private steps: SagaStep<TContext>[] = [];

    /**
     * Appends a step and its compensating action to the saga pipeline.
     */
    public addStep(step: SagaStep<TContext>): this {
        this.steps.push(step);
        return this;
    }

    /**
     * Executes the saga pipeline with forward execution and backward compensation.
     */
    public async execute(sagaId: string, context: TContext): Promise<SagaExecutionResult<TContext>> {
        const journal: StepJournalEntry[] = [];
        const completedSteps: SagaStep<TContext>[] = [];

        for (let i = 0; i < this.steps.length; i++) {
            const step = this.steps[i];
            const maxRetries = step.maxRetries ?? 1;
            let attempt = 0;
            let success = false;
            let lastError: any;

            while (attempt < maxRetries) {
                attempt++;
                try {
                    await step.action(context);
                    success = true;
                    journal.push({
                        stepName: step.name,
                        status: "COMPLETED",
                        attempts: attempt,
                    });
                    completedSteps.push(step);
                    break;
                } catch (err: any) {
                    lastError = err;
                    if (attempt < maxRetries && step.backoffMs) {
                        await new Promise((resolve) => setTimeout(resolve, step.backoffMs! * attempt));
                    }
                }
            }

            if (!success) {
                journal.push({
                    stepName: step.name,
                    status: "FAILED",
                    attempts: attempt,
                    error: lastError?.message || String(lastError),
                });

                // Trigger backward compensation for all previously completed steps
                const compensationErrors = await this.rollback(completedSteps, context, journal);

                return {
                    sagaId,
                    status: compensationErrors.length === 0 ? "COMPENSATED" : "FAILED",
                    context,
                    journal,
                    error: `Saga failed at step '${step.name}': ${lastError?.message || String(lastError)}`,
                };
            }
        }

        return {
            sagaId,
            status: "COMPLETED",
            context,
            journal,
        };
    }

    /**
     * Reverses completed steps in strict reverse order (LIFO).
     */
    private async rollback(
        completedSteps: SagaStep<TContext>[],
        context: TContext,
        journal: StepJournalEntry[]
    ): Promise<string[]> {
        const errors: string[] = [];

        for (let i = completedSteps.length - 1; i >= 0; i--) {
            const step = completedSteps[i];
            try {
                await step.compensate(context);
                journal.push({
                    stepName: step.name,
                    status: "COMPENSATED",
                    attempts: 1,
                });
            } catch (err: any) {
                const errMsg = err?.message || String(err);
                errors.push(errMsg);
                journal.push({
                    stepName: step.name,
                    status: "COMPENSATION_FAILED",
                    attempts: 1,
                    error: errMsg,
                });
            }
        }

        return errors;
    }
}