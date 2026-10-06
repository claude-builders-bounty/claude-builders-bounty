import { expect } from "chai";
import { ethers } from "hardhat";
import { SwarmClaim } from "../typechain-types";
import { Wallet } from "ethers";

const CLAIM_TYPE = {
  Claim: [
    { name: "claimant", type: "address" },
    { name: "sequenceId", type: "uint256" },
    { name: "amount", type: "uint256" },
    { name: "deadline", type: "uint256" },
  ],
};

describe("SwarmClaim", function () {
  let swarmClaim: SwarmClaim;
  let owner: Wallet;
  let claimant1: Wallet;
  let claimant2: Wallet;
  let mockToken: any;
  
  const DOMAIN = {
    name: "SwarmClaim",
    version: "1",
    chainId: 1,
    verifyingContract: "" as string,
  };

  async function signClaim(
    wallet: Wallet,
    contractAddress: string,
    sequenceId: bigint,
    amount: bigint,
    deadline: bigint
  ): Promise<string> {
    const message = {
      claimant: wallet.address,
      sequenceId,
      amount,
      deadline,
    };
    
    return wallet.signTypedData(
      { ...DOMAIN, verifyingContract: contractAddress },
      { Claim: CLAIM_TYPE },
      message
    );
  }

  beforeEach(async () => {
    [owner, claimant1, claimant2] = await ethers.getSigners();
    
    // Deploy mock ERC20 token
    const MockToken = await ethers.getContractFactory("MockERC20");
    mockToken = await MockToken.deploy("Mock Token", "MTK", 1000000n * 10n ** 18n);
    
    // Deploy SwarmClaim
    const SwarmClaimFactory = await ethers.getContractFactory("SwarmClaim");
    swarmClaim = await SwarmClaimFactory.deploy(await mockToken.getAddress());
    
    // Fund the contract with tokens
    await mockToken.transfer(await swarmClaim.getAddress(), 10000n * 10n ** 18n);
  });

  describe("Deployment", function () {
    it("Should set the correct token address", async function () {
      expect(await swarmClaim.claimToken()).to.equal(await mockToken.getAddress());
    });

    it("Should have zero total claimed initially", async function () {
      expect(await swarmClaim.totalClaimed()).to.equal(0);
    });

    it("Should have correct fast path threshold", async function () {
      expect(await swarmClaim.FAST_PATH_THRESHOLD()).to.equal(10);
    });
  });

  describe("Claim", function () {
    it("Should allow a valid claim", async function () {
      const amount = 100n * 10n ** 18n;
      const sequenceId = 1n;
      const deadline = BigInt(Math.floor(Date.now() / 1000)) + 3600n;
      
      const signature = await signClaim(
        claimant1,
        await swarmClaim.getAddress(),
        sequenceId,
        amount,
        deadline
      );
      
      const balanceBefore = await mockToken.balanceOf(claimant1.address);
      const tx = await swarmClaim.claim(
        claimant1.address,
        sequenceId,
        amount,
        deadline,
        signature
      );
      
      await tx.wait();
      
      const balanceAfter = await mockToken.balanceOf(claimant1.address);
      expect(balanceAfter - balanceBefore).to.equal(amount);
      expect(await swarmClaim.totalClaimed()).to.equal(amount);
      expect(await swarmClaim.isClaimed(claimant1.address, sequenceId)).to.be.true;
    });

    it("Should reject already claimed sequences", async function () {
      const amount = 100n * 10n ** 18n;
      const sequenceId = 1n;
      const deadline = BigInt(Math.floor(Date.now() / 1000)) + 3600n;
      
      const signature = await signClaim(
        claimant1,
        await swarmClaim.getAddress(),
        sequenceId,
        amount,
        deadline
      );
      
      await swarmClaim.claim(claimant1.address, sequenceId, amount, deadline, signature);
      
      await expect(
        swarmClaim.claim(claimant1.address, sequenceId, amount, deadline, signature)
      ).to.be.revertedWith("SwarmClaim: already claimed");
    });

    it("Should reject expired signatures", async function () {
      const amount = 100n * 10n ** 18n;
      const sequenceId = 1n;
      const deadline = BigInt(Math.floor(Date.now() / 1000)) - 1n;
      
      const signature = await signClaim(
        claimant1,
        await swarmClaim.getAddress(),
        sequenceId,
        amount,
        deadline
      );
      
      await expect(
        swarmClaim.claim(claimant1.address, sequenceId, amount, deadline, signature)
      ).to.be.revertedWith("SwarmClaim: signature expired");
    });

    it("Should reject zero amounts", async function () {
      const sequenceId = 1n;
      const deadline = BigInt(Math.floor(Date.now() / 1000)) + 3600n;
      
      const signature = await signClaim(
        claimant1,
        await swarmClaim.getAddress(),
        sequenceId,
        0n,
        deadline
      );
      
      await expect(
        swarmClaim.claim(claimant1.address, sequenceId, 0n, deadline, signature)
      ).to.be.revertedWith("SwarmClaim: zero amount");
    });

    it("Should reject invalid signatures", async function () {
      const amount = 100n * 10n ** 18n;
      const sequenceId = 1n;
      const deadline = BigInt(Math.floor(Date.now() / 1000)) + 3600n;
      
      // Sign with wrong wallet
      const signature = await signClaim(
        claimant2,
        await swarmClaim.getAddress(),
        sequenceId,
        amount,
        deadline
      );
      
      await expect(
        swarmClaim.claim(claimant1.address, sequenceId, amount, deadline, signature)
      ).to.be.revertedWith("SwarmClaim: invalid signature");
    });
  });

  describe("Batch Claim", function () {
    it("Should process multiple claims in batch", async function () {
      const amounts = [100n * 10n ** 18n, 200n * 10n ** 18n];
      const sequenceIds = [1n, 2n];
      const deadline = BigInt(Math.floor(Date.now() / 1000)) + 3600n;
      
      const signatures = await Promise.all([
        signClaim(claimant1, await swarmClaim.getAddress(), sequenceIds[0], amounts[0], deadline),
        signClaim(claimant2, await swarmClaim.getAddress(), sequenceIds[1], amounts[1], deadline),
      ]);
      
      const tx = await swarmClaim.batchClaim(
        [claimant1.address, claimant2.address],
        sequenceIds,
        amounts,
        [deadline, deadline],
        signatures
      );
      
      await tx.wait();
      
      expect(await swarmClaim.totalClaimed()).to.equal(amounts[0] + amounts[1]);
      expect(await swarmClaim.isClaimed(claimant1.address, sequenceIds[0])).to.be.true;
      expect(await swarmClaim.isClaimed(claimant2.address, sequenceIds[1])).to.be.true;
    });

    it("Should reject batch with mismatched array lengths", async function () {
      await expect(
        swarmClaim.batchClaim(
          [claimant1.address],
          [1n, 2n],
          [100n * 10n ** 18n],
          [BigInt(Math.floor(Date.now() / 1000)) + 3600n],
          ["0x"]
        )
      ).to.be.revertedWith("SwarmClaim: array length mismatch");
    });
  });

  describe("Fast Path", function () {
    it("Should track claim counts", async function () {
      const amount = 100n * 10n ** 18n;
      const deadline = BigInt(Math.floor(Date.now() / 1000)) + 3600n;
      
      for (let i = 1; i <= 11; i++) {
        const signature = await signClaim(
          claimant1,
          await swarmClaim.getAddress(),
          BigInt(i),
          amount,
          deadline
        );
        await swarmClaim.claim(claimant1.address, BigInt(i), amount, deadline, signature);
      }
      
      expect(await swarmClaim.getClaimCount(claimant1.address)).to.equal(11);
    });
  });

  describe("Admin Functions", function () {
    it("Should allow owner to withdraw tokens", async function () {
      const amount = 100n * 10n ** 18n;
      const ownerBalanceBefore = await mockToken.balanceOf(owner.address);
      
      await swarmClaim.withdrawTokens(await mockToken.getAddress(), amount);
      
      expect(await mockToken.balanceOf(owner.address)).to.equal(ownerBalanceBefore + amount);
    });

    it("Should not allow non-owner to withdraw tokens", async function () {
      await expect(
        swarmClaim.connect(claimant1).withdrawTokens(await mockToken.getAddress(), 1n)
      ).to.be.reverted;
    });
  });
});
