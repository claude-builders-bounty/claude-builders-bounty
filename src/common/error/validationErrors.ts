import { CustomError } from './CustomError';

export const claimSignatureNotFoundError = new CustomError(
  'Claim error: Signature not found.',
  'CLAIM_ERROR'
);

export const claimRecordAlreadyExistsError = new CustomError(
  'Claim error: A record for this claim already exists.',
  'CLAIM_ERROR'
);

export const unsupportedClaimVersionError = new CustomError(
  'Claim error: Unsupported claim version.',
  'CLAIM_ERROR'
);

export const claimNotFoundError = new CustomError(
  'Claim error: Claim not found or already claimed.',
  'CLAIM_ERROR'
);

export const insufficientPoolBalanceError = new CustomError(
  'Claim error: Insufficient pool balance to process this claim.',
  'CLAIM_ERROR'
);

export const invalidRecipientWalletAddressError = new CustomError(
  'Claim error: Invalid recipient wallet address.',
  'CLAIM_ERROR'
);
