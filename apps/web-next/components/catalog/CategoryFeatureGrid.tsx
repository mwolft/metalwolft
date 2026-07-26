export type CategoryFeatureItem = {
  title: string;
  description: string;
};

type CategoryFeatureGridProps = {
  title: string;
  introduction: string;
  items: readonly CategoryFeatureItem[];
  id?: string;
};

export function CategoryFeatureGrid({
  title,
  introduction,
  items,
  id = "category-features"
}: CategoryFeatureGridProps) {
  if (items.length === 0) {
    return null;
  }

  const headingId = `${id}-heading`;

  return (
    <section className="mw-section mw-category-features" aria-labelledby={headingId} id={id}>
      <h2 id={headingId}>{title}</h2>
      <p className="mw-category-features__introduction">{introduction}</p>
      <ul className="mw-category-feature-grid">
        {items.map((item) => (
          <li className="mw-category-feature-grid__item" key={item.title}>
            <h3>{item.title}</h3>
            <p>{item.description}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
