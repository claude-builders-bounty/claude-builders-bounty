import { ItemList } from '@/components/item-list';
import { listItems } from '@/lib/queries/items';

// A page that reads the database is always dynamic.
export const dynamic = 'force-dynamic';

export default function Page() {
  const items = listItems();
  return (
    <main>
      <h1>Items</h1>
      <ItemList items={items} />
    </main>
  );
}
