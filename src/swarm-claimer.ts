import { ethers } from 'ethers';
import { ClaimController } from './claim';

export class SwarmClaimer {
  private controller: ClaimController;
  private privateKey: string;
  private rpcUrl: string;

  constructor(rpcUrl: string, privateKey: string) {
    this.rpcUrl = rpcUrl;
    this.privateKey = privateKey;
    this.controller = new ClaimController(rpcUrl, privateKey);
  }

  async performClaim(bountyId: number, digest: string): Promise<string> {
    const signature = await this.signMessage(digest);
    const txHash = await this.controller.claim(bountyId, signature);
    return txHash;
  }

  async autoSwarmClaim(): Promise<void> {
    const pendingClaims = await this.fetchPendingClaims();
    
    for (const claim of pendingClaims) {
      try {
        console.log(`Claiming bounty ${claim.bountyId}...`);
        const txHash = await this.performClaim(claim.bountyId, claim.digest);
        console.log(`Successfully claimed ${claim.bountyId}: ${txHash}`);
      } catch (error) {
        console.error(`Failed to claim ${claim.bountyId}: ${error}`);
      }
    }
  }

  private async signMessage(digest: string): Promise<string> {
    const wallet = new ethers.Wallet(this.privateKey, new ethers.JsonRpcProvider(this.rpcUrl));
    return await wallet.signMessage(digest);
  }

  private async fetchPendingClaims(): Promise<Array<{ bountyId: number; digest: string }>> {
    // Implementation would query the bounty contract for pending claims
    return [];
  }
}
