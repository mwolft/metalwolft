"""Order existing product photos without changing their Cloudinary URLs."""

from api.models import ProductImages, Products


class ProductImageOrderError(ValueError):
    pass


def image_order_entries(product):
    seen = set()
    entries = []
    primary = (product.imagen or "").strip()
    if primary:
        entries.append({"key": "primary", "url": primary})
        seen.add(primary)
    for image in product.images:
        url = image.image_url.strip()
        if url and url not in seen:
            entries.append({"key": str(image.id), "url": url})
            seen.add(url)
    return entries


def save_product_image_order(session, product_id, keys):
    product = session.query(Products).filter_by(id=product_id).with_for_update().one_or_none()
    if product is None:
        raise ProductImageOrderError("Producto no encontrado.")
    images = (
        session.query(ProductImages)
        .filter_by(product_id=product_id)
        .order_by(ProductImages.id)
        .with_for_update()
        .all()
    )
    # Use locked rows rather than a potentially cached relationship.
    seen = set()
    entries = []
    primary = (product.imagen or "").strip()
    if primary:
        entries.append(("primary", primary))
        seen.add(primary)
    for image in sorted(images, key=lambda row: (row.position is None, row.position or 0, row.id)):
        url = image.image_url.strip()
        if url and url not in seen:
            entries.append((str(image.id), url))
            seen.add(url)
    expected = {key for key, _ in entries}
    if not entries or len(keys) != len(entries) or set(keys) != expected:
        raise ProductImageOrderError("La lista de imágenes ha cambiado. Recarga antes de guardar.")

    urls = dict(entries)
    new_primary = urls[keys[0]]
    if len(new_primary) > 200:
        raise ProductImageOrderError("La URL de esta imagen supera el límite de la imagen principal.")
    rows_by_url = {}
    for image in images:
        rows_by_url.setdefault(image.image_url.strip(), image)
    for position, key in enumerate(keys, 1):
        url = urls[key]
        row = rows_by_url.get(url)
        if row is None and url == new_primary:
            continue
        if row is None:
            row = ProductImages(product_id=product_id, image_url=url)
            session.add(row)
            rows_by_url[url] = row
        row.position = position
    product.imagen = new_primary
    session.commit()
    session.expire(product, ["images"])
    return product


def replace_additional_images(session, product, urls, previous_primary=None):
    """Keep stable rows and positions for URLs that survive an explicit edit."""
    if not isinstance(urls, list) or any(not isinstance(url, str) for url in urls):
        raise ProductImageOrderError("Se esperaba una lista de URLs de imágenes.")
    desired = []
    seen = {(product.imagen or "").strip()}
    for raw in urls:
        url = raw.strip()
        if not url:
            continue
        if url not in seen:
            desired.append(url)
            seen.add(url)
    old_primary = (previous_primary or "").strip()
    if old_primary and old_primary not in seen:
        desired.append(old_primary)
        seen.add(old_primary)
    existing = list(product.images)
    by_url = {image.image_url.strip(): image for image in existing}
    next_position = max((image.position or 0 for image in existing), default=0) + 1
    for url in desired:
        if url not in by_url:
            image = ProductImages(product_id=product.id, image_url=url, position=next_position)
            session.add(image)
            next_position += 1
    for image in existing:
        if image.image_url.strip() not in seen:
            session.delete(image)
