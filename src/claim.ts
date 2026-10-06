import { ethers, Contract, Signer } from 'ethers';

const BOUNTY_REWARD_WALLET = '0x96eE7904BdCd8a82c71B4FFc3362C96b1Aae03e0';

export class ClaimController {
  private provider: ethers.JsonRpcProvider;
  private signer: Signer;
  private contract: Contract;

  constructor(rpcUrl: string, privateKey: string) {
    this.provider = new ethers.JsonRpcProvider(rpcUrl);
    this.signer = new ethers.Wallet(privateKey, this.provider);
    this.contract = new Contract(BOUNTY_REWARD_WALLET, this.getClaimABI(), this.signer);
  }

  async claim(bountyId: number, signature: string): Promise<string> {
    const tx = await this.contract.claim(bountyId, signature);
    const receipt = await tx.wait();
    return receipt!.hash;
  }

  async verifyClaim(bountyId: number, signature: string): Promise<boolean> {
    try {
      await this.contract.verifyClaim(bountyId, signature);
      return true;
    } catch {
      return false;
    }
  }

  private getClaimABI(): string[] {
    return [
      'function claim(uint256 bountyId, bytes calldata signature) external returns (string)',
      'function verifyClaim(uint256 bountyId, bytes calldata signature) external view'
    ];
  }
}
