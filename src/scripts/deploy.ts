import { ethers } from "hardhat";

async function main() {
  const CLAIM_TOKEN_ADDRESS = process.env.CLAIM_TOKEN_ADDRESS;
  
  if (!CLAIM_TOKEN_ADDRESS) {
    throw new Error("CLAIM_TOKEN_ADDRESS environment variable is required");
  }
  
  console.log(`Deploying SwarmClaim with token: ${CLAIM_TOKEN_ADDRESS}`);
  
  const SwarmClaim = await ethers.getContractFactory("SwarmClaim");
  const swarmClaim = await SwarmClaim.deploy(CLAIM_TOKEN_ADDRESS);
  
  await swarmClaim.waitForDeployment();
  
  const address = await swarmClaim.getAddress();
  console.log(`SwarmClaim deployed to: ${address}`);
  
  // Save deployment info
  const fs = require("fs");
  const deploymentInfo = {
    network: process.env.HARDHAT_NETWORK || "localhost",
    contract: "SwarmClaim",
    address: address,
    token: CLAIM_TOKEN_ADDRESS,
    deployedAt: new Date().toISOString(),
  };
  
  fs.writeFileSync(
    `deployments/${process.env.HARDHAT_NETWORK || "localhost"}/swarmClaim.json`,
    JSON.stringify(deploymentInfo, null, 2)
  );
  
  console.log("Deployment info saved");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
