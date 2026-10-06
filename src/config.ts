export interface Config {
  rpcUrl: string;
  walletPrivateKey: string;
  claimContractAddress: string;
  bountyRepoOwner: string;
  bountyRepoName: string;
  minConfirmationBlocks: number;
}

export function loadConfig(): Config {
  const rpcUrl = process.env.RPC_URL || "https://mainnet.base.org";
  const walletPrivateKey = process.env.WALLET_PRIVATE_KEY || "";
  const claimContractAddress = process.env.CLAIM_CONTRACT_ADDRESS || "";
  const bountyRepoOwner = process.env.BOUNTY_REPO_OWNER || "claude-builders-bounty";
  const bountyRepoName = process.env.BOUNTY_REPO_NAME || "claude-builders-bounty";
  const minConfirmationBlocks = parseInt(process.env.MIN_CONFIRMATION_BLOCKS || "1", 10);

  if (!walletPrivateKey) {
    throw new Error("WALLET_PRIVATE_KEY environment variable is required");
  }
  if (!claimContractAddress) {
    throw new Error("CLAIM_CONTRACT_ADDRESS environment variable is required");
  }

  return {
    rpcUrl,
    walletPrivateKey,
    claimContractAddress,
    bountyRepoOwner,
    bountyRepoName,
    minConfirmationBlocks,
  };
}
