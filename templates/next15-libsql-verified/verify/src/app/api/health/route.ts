import { db } from '@/server/db/client';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  const result = await db.execute('SELECT 1 AS ready');
  return Response.json({ ready: result.rows[0].ready === 1 });
}
