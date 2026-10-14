import { NextResponse } from 'next/server';
import { ItemInputSchema } from '@/lib/validation/items';
import { createItem, listItems } from '@/lib/queries/items';

export async function GET() {
  return NextResponse.json({ items: listItems() });
}

export async function POST(request: Request) {
  const body: unknown = await request.json();
  const parsed = ItemInputSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  return NextResponse.json({ item: createItem(parsed.data.title) }, { status: 201 });
}
