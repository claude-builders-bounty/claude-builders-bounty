import { bignumber, BN } from 'keto-bignumber';
import { ethers } from 'ethers';

import type { ClaimOpts, ClaimBountyResult } from '@/common/types/claims';
import { CLAIM_VERSIONS } from '@/common/types/claims';
import { getProvider, verifyClaimSig } from './helpers';
import { getClaimBountyConfig } from '@/data/claims_config';
import { ClaimError } from '@/common/error/ClaimError';
import {
  claimRecordAlreadyExistsError,
  claimSignatureNotFoundError,
  unsupportedClaimVersionError,
  claimNotFoundError,
  insufficientPoolBalanceError,
  invalidRecipientWalletAddressError,
} from '@/common/error/validationErrors';

export async function claim(
  opts: ClaimOpts
): Promise<ClaimBountyResult> {
  const provider = getProvider();
  const version = opts.version ?? CLAIM_VERSIONS.latest;

  if (version === null) {
    throw new ClaimError(unsupportedClaimVersionError);
  }

  const poolAddress = await getClaimBountyConfig();

  // Verify signature before any state changes
  if (!opts.signature) {
    throw new ClaimError(claimSignatureNotFoundError);
  }
  await verifyClaimSig(provider, opts);

  const claimRecordAlreadyExists = await provider.contract.callStatic
    .canClaim(opts.recipient, opts.timestamp, opts.version)
    .catch(() => false);

  if (claimRecordAlreadyExists) {
    throw new ClaimError(claimRecordAlreadyExistsError);
  }

  // Validate recipient wallet address format
  if (!ethers.isAddress(opts.recipient)) {
    throw new ClaimError(invalidRecipientWalletAddressError);
  }

  const recipient = opts.recipient;

  const nonce = await provider.wallet.nonce();
  try {
    const txResponse = await provider.wallet.sendTransaction({
      to: provider.contract.address,
      value: opts.value,
      data: provider.contract.interface.encodeFunctionData('claim', [
        recipient,
        opts.timestamp,
        opts.version,
        opts.signature,
      ]),
      nonce,
    });

    return {
      success: true,
      txHash: txResponse.hash,
      blockNumber: (await txResponse.wait())?.blockNumber,
    };
  } catch (error: unknown) {
    // If the transaction fails due to insufficient pool balance,
    // provide a more informative error.
    const err = error as { data?: string; code?: string };
    const revertData = err?.data;
    if (
      revertData &&
      typeof revertData === 'string' &&
      revertData.startsWith('0x')
    ) {
      // Decode custom error or generic failure
      const selector = revertData.slice(0, 10).toLowerCase();
      const isInsufficientBalance =
        selector === '0x2e1d57f6' || // InsufficientBalance()
        selector === '0x08c379a0' || // Error(string)
        selector === '0x4e487b71' || // Panic(uint256)
        selector === '0x4550d2e3' || // OwnableUnauthorizedAccount(address)
        selector === '0x000001' || // Gas estimation failed (often OOG or revert)
        selector === '0x';
      // We treat any revert from claim() as a possible InsufficientBalance,
      // because that's the most common expected failure during airdrop claims.
      const reasonHex = selector === '0x08c379a0' ? revertData.slice(10) : '';
      if (reasonHex) {
        try {
          const reason = ethers.AbiCoder.defaultAbiCoder().decode(['string'], `0x${reasonHex}`)[0] as string;
          if (reason.toLowerCase().includes('insufficient')) {
            throw new ClaimError(insufficientPoolBalanceError);
          }
        } catch {
          // ignore decode failures
        }
      }
    }
    throw new ClaimError(claimNotFoundError);
  }
}
