import type { Item } from '@/lib/queries/items';

interface Props {
  items: Item[];
}

export function ItemList({ items }: Props) {
  if (items.length === 0) return <p>No items yet.</p>;
  return (
    <ul>
      {items.map((item) => (
        <li key={item.id}>{item.title}</li>
      ))}
    </ul>
  );
}
