import { Wallet, Provider, ethers } from "ethers";
import { Config } from "./config";
import { GitHubClient } from "./github";
import { BountyClaim } from "./types";

export class Claimer {
  private config: Config;
  private wallet: Wallet;
  private provider: Provider;
  private github: GitHubClient;
  private claimsFile: string;

  constructor(config: Config) {
    this.config = config;
    this.provider = new Provider(config.rpcUrl);
    this.wallet = new Wallet(config.walletPrivateKey, this.provider);
    this.github = new GitHubClient();
    this.claimsFile = process.env.CLAIMS_FILE || "./claims.json";
  }

  private async loadClaims(): Promise<BountyClaim[]> {
    try {
      const fs = require("fs");
      if (fs.existsSync(this.claimsFile)) {
        const data = fs.readFileSync(this.claimsFile, "utf-8");
        return JSON.parse(data);
      }
    } catch (error) {
      console.error("Failed to load claims:", error);
    }
    return [];
  }

  private async saveClaims(claims: BountyClaim[]): Promise<void> {
    try {
      const fs = require("fs");
      fs.writeFileSync(this.claimsFile, JSON.stringify(claims, null, 2));
    } catch (error) {
      console.error("Failed to save claims:", error);
    }
  }

  private async isAlreadyClaimed(issueNumber: number): Promise<boolean> {
    const claims = await this.loadClaims();
    return claims.some((claim) => claim.issueNumber === issueNumber && claim.status === "claimed");
  }

  private async parseClaimRequest(issueBody: string): Promise<{ walletAddress: string } | null> {
    // Parse /claim command with wallet address
    const claimRegex = /\/claim\s+([\dA-Fa-f]{40})/i;
    const match = issueBody.match(claimRegex);
    
    if (match && ethers.isAddress(match[1])) {
      return { walletAddress: match[1].toLowerCase() };
    }
    return null;
  }

  private async validateClaim(issue: any, walletAddress: string): Promise<boolean> {
    // Check if the issue is open
    if (issue.state !== "open") {
      console.log(`Issue #${issue.number} is not open`);
      return false;
    }

    // Check if already claimed
    if (await this.isAlreadyClaimed(issue.number)) {
      console.log(`Issue #${issue.number} already claimed`);
      return false;
    }

    // Verify wallet address matches the issue author
    const issueAuthor = issue.user.login.toLowerCase();
    const walletOwner = await this.getWalletOwner(walletAddress);
    
    if (walletOwner !== issueAuthor) {
      console.log(`Wallet address does not match issue author`);
      return false;
    }

    return true;
  }

  private async getWalletOwner(_walletAddress: string): Promise<string> {
    // In a real implementation, this would resolve ENS or check contract ownership
    // For now, we'll use the issue author as the validator
    return process.env.ISSUE_AUTHOR || "";
  }

  public async processIssue(issueNumber: number): Promise<void> {
    try {
      console.log(`Processing issue #${issueNumber}...`);
      
      const issue = await this.github.getIssue(
        this.config.bountyRepoOwner,
        this.config.bountyRepoName,
        issueNumber
      );

      const claimRequest = await this.parseClaimRequest(issue.body || "");
      if (!claimRequest) {
        console.log(`No valid /claim request found in issue #${issueNumber}`);
        return;
      }

      const isValid = await this.validateClaim(issue, claimRequest.walletAddress);
      if (!isValid) {
        await this.github.createComment(
          this.config.bountyRepoOwner,
          this.config.bountyRepoName,
          issueNumber,
          "❌ Claim validation failed. Please ensure the wallet address matches the issue author."
        );
        return;
      }

      // Execute the claim on-chain
      const txHash = await this.executeClaim(issue.number, claimRequest.walletAddress);
      
      // Save the claim
      await this.saveClaim({
        id: `claim-${issue.number}`,
        repoOwner: this.config.bountyRepoOwner,
        repoName: this.config.bountyRepoName,
        issueNumber,
        claimant: claimRequest.walletAddress,
        claimedAt: Date.now(),
        transactionHash: txHash,
        status: "claimed",
      });

      // Post success comment
      await this.github.createComment(
        this.config.bountyRepoOwner,
        this.config.bountyRepoName,
        issueNumber,
        `✅ **Claim successful!**\n\nTransaction: [${txHash.substring(0, 10)}...${txHash.substring(txHash.length - 8)}](https://basescan.org/tx/${txHash})\n\nYour bounty claim has been processed on-chain.`
      );

      console.log(`Successfully claimed bounty for issue #${issueNumber}`);
    } catch (error) {
      console.error(`Failed to process issue #${issueNumber}:`, error);
      
      await this.github.createComment(
        this.config.bountyRepoOwner,
        this.config.bountyRepoName,
        issueNumber,
        "❌ **Claim failed.** Please try again later or contact the bounty administrators."
      );
    }
  }

  private async executeClaim(issueNumber: number, walletAddress: string): Promise<string> {
    // Contract ABI for the claim function
    const CLAIM_ABI = [
      "function claim(uint256 issueId, address claimant) external",
      "function getClaimStatus(uint256 issueId) external view returns (bool)",
    ];

    const contract = new ethers.Contract(
      this.config.claimContractAddress,
      CLAIM_ABI,
      this.wallet
    );

    try {
      const tx = await contract.claim(issueNumber, walletAddress);
      console.log(`Claim transaction submitted: ${tx.hash}`);
      
      // Wait for confirmation
      const receipt = await tx.wait(this.config.minConfirmationBlocks);
      
      if (!receipt || receipt.status !== 1) {
        throw new Error("Transaction failed");
      }

      return receipt.hash;
    } catch (error) {
      console.error("Claim transaction failed:", error);
      throw error;
    }
  }

  public async runCron(): Promise<void> {
    console.log("Starting bounty claim processor...");
    
    try {
      const issues = await this.github.getRepoIssues(
        this.config.bountyRepoOwner,
        this.config.bountyRepoName,
        "open"
      );

      let processed = 0;
      for (const issue of issues) {
        if (issue.pull_request) continue; // Skip PRs
        
        await this.processIssue(issue.number);
        processed++;
        
        // Rate limiting
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }

      console.log(`Processed ${processed} issues`);
    } catch (error) {
      console.error("Cron job failed:", error);
    }
  }
}
