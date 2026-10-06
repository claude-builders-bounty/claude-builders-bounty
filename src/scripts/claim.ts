import { ethers } from "hardhat";
import { SwarmClaim } from "../typechain-types";
import { Wallet, TypedDataEncoder } from "ethers";

const CLAIM_TYPE = {
  Claim: [
    { name: "claimant", type: "address" },
    { name: "sequenceId", type: "uint256" },
    { name: "amount", type: "uint256" },
    { name: "deadline", type: "uint256" },
  ],
};

interface ClaimParams {
  claimant: string;
  sequenceId: bigint;
  amount: bigint;
  deadline: bigint;
}

/**
 * Sign a claim request using EIP-712
 */
export async function signClaim(
  wallet: Wallet,
  contractAddress: string,
  params: ClaimParams,
  chainId: number
): Promise<string> {
  const domain = {
    name: "SwarmClaim",
    version: "1",
    chainId,
    verifyingContract: contractAddress,
  };

  const message = {
    claimant: params.claimant,
    sequenceId: params.sequenceId,
    amount: params.amount,
    deadline: params.deadline,
  };

  const signature = await wallet.signTypedData(domain, { Claim: CLAIM_TYPE }, message);
  return signature;
}

/**
 * Process a single claim
 */
export async function processClaim(
  claimContract: SwarmClaim,
  wallet: Wallet,
  params: ClaimParams
): Promise<ReturnType<SwarmClaim["claim"]>> {
  const chainId = (await wallet.provider.getNetwork()).chainId;
  const signature = await signClaim(wallet.target, await claimContract.getAddress(), params, Number(chainId));
  
  const deadline = await claimContract.deadline || params.deadline;
  
  return claimContract.claim(
    params.claimant,
    params.sequenceId,
    params.amount,
    params.deadline,
    signature
  );
}

/**
 * Process batch claims
 */
export async function processBatchClaim(
  claimContract: SwarmClaim,
  wallets: Wallet[],
  paramsList: ClaimParams[]
): Promise<ReturnType<SwarmClaim["batchClaim"]>> {
  const chainId = (await wallets[0].provider.getNetwork()).chainId;
  const contractAddress = await claimContract.getAddress();
  
  const signatures = await Promise.all(
    wallets.map(async (wallet, i) => 
      signClaim(wallet.target, contractAddress, paramsList[i], Number(chainId))
    )
  );
  
  const claimants = paramsList.map(p => p.claimant);
  const sequenceIds = paramsList.map(p => p.sequenceId);
  const amounts = paramsList.map(p => p.amount);
  const deadlines = paramsList.map(p => p.deadline);
  
  return claimContract.batchClaim(claimants, sequenceIds, amounts, deadlines, signatures);
}

async function main() {
  const CONTRACT_ADDRESS = process.env.CONTRACT_ADDRESS;
  const PRIVATE_KEY = process.env.PRIVATE_KEY;
  const SEQUENCE_ID = process.env.SEQUENCE_ID;
  const AMOUNT = process.env.AMOUNT;
  
  if (!CONTRACT_ADDRESS || !PRIVATE_KEY || !SEQUENCE_ID || !AMOUNT) {
    throw new Error("Required environment variables: CONTRACT_ADDRESS, PRIVATE_KEY, SEQUENCE_ID, AMOUNT");
  }
  
  const provider = ethers.getDefaultProvider();
  const wallet = new Wallet(PRIVATE_KEY, provider);
  
  const SwarmClaim = await ethers.getContractFactory("SwarmClaim");
  const claimContract = SwarmClaim.attach(CONTRACT_ADDRESS) as SwarmClaim;
  
  console.log(`Processing claim for ${wallet.address}`);
  
  const params: ClaimParams = {
    claimant: wallet.address,
    sequenceId: BigInt(SEQUENCE_ID),
    amount: BigInt(AMOUNT),
    deadline: BigInt(Math.floor(Date.now() / 1000) + 3600), // 1 hour from now
  };
  
  const tx = await claimContract.claim(
    params.claimant,
    params.sequenceId,
    params.amount,
    params.deadline,
    await signClaim(wallet, CONTRACT_ADDRESS, params, (await wallet.provider.getNetwork()).chainId)
  );
  
  console.log(`Claim transaction: ${tx.hash}`);
  await tx.wait();
  console.log("Claim processed successfully!");
}

if (require.main === module) {
  main()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}
