import 'server-only';

export type Membership = { userId: string; organizationId: string };

// Deliberately fail closed until a verified session provider is integrated.
export async function requireMembership(): Promise<Membership> {
  throw new Error('UNAUTHENTICATED');
}
