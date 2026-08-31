/**
 * User-space Read-Copy-Update (RCU) Synchronization Primitive.
 * High-concurrency lock-free read data structure synchronization featuring:
 * - Lockless Readers: Zero locking overhead on reads (`readLock` / `readUnlock`).
 * - Copy-on-Write Updates: Atomic pointer swaps for reader safety.
 * - Epoch-based Grace Period Tracking (`synchronizeRcu`): Waits until all pre-existing readers complete before freeing old memory.
 * - Deferred Callback Reclamation (`callRcu`).
 */

export class ReadCopyUpdateContainer<T> {
    private currentPointer: T;
    private activeReaders: Map<string, number> = new Map(); // readerId -> readerEpoch
    private globalEpoch = 1;
    private retirementQueue: Array<{ oldData: T; retiredAtEpoch: number; callback?: (data: T) => void }> = [];

    constructor(initialData: T) {
        this.currentPointer = initialData;
    }

    /**
     * Reader enters critical section (lock-free).
     */
    public rcuReadLock(readerId: string): T {
        this.activeReaders.set(readerId, this.globalEpoch);
        return this.currentPointer;
    }

    /**
     * Reader exits critical section.
     */
    public rcuReadUnlock(readerId: string): void {
        this.activeReaders.delete(readerId);
        this.reclaimDeferred();
    }

    /**
     * Replaces the shared data pointer with an updated copy atomically.
     */
    public update(updater: (current: T) => T, onReclaim?: (old: T) => void): void {
        const oldData = this.currentPointer;
        const newData = updater(oldData);

        // Atomic publication of new pointer
        this.currentPointer = newData;
        const retiredEpoch = this.globalEpoch;
        this.globalEpoch += 1;

        this.retirementQueue.push({
            oldData,
            retiredAtEpoch: retiredEpoch,
            callback: onReclaim,
        });

        this.reclaimDeferred();
    }

    /**
     * Returns true if all readers that were active during the retired epoch have finished.
     */
    private isGracePeriodComplete(retiredEpoch: number): boolean {
        for (const readerEpoch of this.activeReaders.values()) {
            if (readerEpoch <= retiredEpoch) {
                return false; // Still an active reader from that epoch
            }
        }
        return true;
    }

    /**
     * Purges retired memory items whose grace periods have completed.
     */
    public reclaimDeferred(): number {
        let reclaimed = 0;
        const remaining: typeof this.retirementQueue = [];

        for (const entry of this.retirementQueue) {
            if (this.isGracePeriodComplete(entry.retiredAtEpoch)) {
                if (entry.callback) {
                    entry.callback(entry.oldData);
                }
                reclaimed++;
            } else {
                remaining.push(entry);
            }
        }

        this.retirementQueue = remaining;
        return reclaimed;
    }

    /**
     * Synchronously waits until all readers of the retired data exit.
     */
    public async synchronizeRcu(pollIntervalMs = 5): Promise<void> {
        const currentEpoch = this.globalEpoch;
        while (!this.isGracePeriodComplete(currentEpoch)) {
            await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
        }
        this.reclaimDeferred();
    }

    public get(): T {
        return this.currentPointer;
    }
}