import { CustomError } from './CustomError';

export class ClaimError extends CustomError {
  constructor(message: CustomError | string) {
    super(message instanceof CustomError ? message : new CustomError(message, 'CLAIM_ERROR'));
  }
}
