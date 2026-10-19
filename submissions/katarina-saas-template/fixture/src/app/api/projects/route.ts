import { requireMembership } from '../../../server/auth';
import { listProjects } from '../../../server/db';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const membership = await requireMembership();
    return Response.json({ data: listProjects(membership.organizationId) });
  } catch (error) {
    if (error instanceof Error && error.message === 'UNAUTHENTICATED') {
      return Response.json({ error: 'unauthorized' }, { status: 401 });
    }
    return Response.json({ error: 'internal_error' }, { status: 500 });
  }
}
