/**
 * Distributed Deadlock Detector using Wait-For-Graph (WFG) Cycle Analysis.
 * Enterprise-grade deadlock detection for distributed transaction coordinators.
 * Features Tarjan / DFS cycle detection, victim transaction selection based on
 * rollback cost weighting, and automatic dependency graph serialization.
 */

export interface ResourceLockRequest {
    transactionId: string;
    resourceId: string;
    heldByTransactionId?: string; // Transaction currently holding the resource
    transactionCost: number;     // Cost/age metric (e.g. CPU time or write count)
}

export interface DeadlockCycle {
    cycleTransactionIds: string[];
    suggestedVictimId: string;
    victimRollbackCost: number;
}

export interface DeadlockAnalysisResult {
    hasDeadlock: boolean;
    cycles: DeadlockCycle[];
    resolvedWaitGraph: Record<string, string[]>;
}

export class DistributedDeadlockDetector {
    private waitGraph: Map<string, Set<string>> = new Map(); // waiter -> Set of holders
    private transactionCosts: Map<string, number> = new Map();

    /**
     * Registers a transaction and its lock dependency into the wait-for graph.
     */
    public addDependency(request: ResourceLockRequest): this {
        this.transactionCosts.set(request.transactionId, request.transactionCost);

        if (!this.waitGraph.has(request.transactionId)) {
            this.waitGraph.set(request.transactionId, new Set());
        }

        if (request.heldByTransactionId && request.heldByTransactionId !== request.transactionId) {
            this.waitGraph.get(request.transactionId)!.add(request.heldByTransactionId);
            if (!this.transactionCosts.has(request.heldByTransactionId)) {
                this.transactionCosts.set(request.heldByTransactionId, 100);
            }
        }

        return this;
    }

    /**
     * Removes all dependency edges for a completed or aborted transaction.
     */
    public removeTransaction(transactionId: string): void {
        this.waitGraph.delete(transactionId);
        this.transactionCosts.delete(transactionId);

        for (const [_, holders] of this.waitGraph.entries()) {
            holders.delete(transactionId);
        }
    }

    /**
     * Detects cycles in the Wait-For-Graph using DFS and selects lowest-cost victim transactions.
     */
    public detectDeadlocks(): DeadlockAnalysisResult {
        const visited: Set<string> = new Set();
        const recursionStack: Set<string> = new Set();
        const currentPath: string[] = [];
        const cycles: DeadlockCycle[] = [];

        const dfs = (node: string) => {
            visited.add(node);
            recursionStack.add(node);
            currentPath.push(node);

            const neighbors = this.waitGraph.get(node) || new Set();
            for (const neighbor of neighbors) {
                if (!visited.has(neighbor)) {
                    dfs(neighbor);
                } else if (recursionStack.has(neighbor)) {
                    // Cycle detected! Extract cycle path
                    const cycleStartIndex = currentPath.indexOf(neighbor);
                    if (cycleStartIndex !== -1) {
                        const cycleNodes = currentPath.slice(cycleStartIndex);
                        // Pick victim with minimum rollback cost
                        let victimId = cycleNodes[0];
                        let minCost = this.transactionCosts.get(victimId) ?? Infinity;

                        for (const txId of cycleNodes) {
                            const cost = this.transactionCosts.get(txId) ?? 100;
                            if (cost < minCost) {
                                minCost = cost;
                                victimId = txId;
                            }
                        }

                        cycles.push({
                            cycleTransactionIds: [...cycleNodes],
                            suggestedVictimId: victimId,
                            victimRollbackCost: minCost,
                        });
                    }
                }
            }

            recursionStack.delete(node);
            currentPath.pop();
        };

        for (const node of this.waitGraph.keys()) {
            if (!visited.has(node)) {
                dfs(node);
            }
        }

        const serializedGraph: Record<string, string[]> = {};
        for (const [k, v] of this.waitGraph.entries()) {
            serializedGraph[k] = Array.from(v);
        }

        return {
            hasDeadlock: cycles.length > 0,
            cycles,
            resolvedWaitGraph: serializedGraph,
        };
    }
}