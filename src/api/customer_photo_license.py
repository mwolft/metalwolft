"""Versioned draft of the commercial photo license shown before acceptance."""

PHOTO_LICENSE_VERSION = "photo-license-v3-draft"
PHOTO_LICENSE_TEXT = (
    "Autorizo a MetalWolft a utilizar comercialmente las fotografías que envío mediante "
    "una licencia no exclusiva, de ámbito mundial y durante cinco años desde mi aceptación. "
    "Conservo la titularidad y los derechos sobre mis fotografías. La licencia permite "
    "reproducirlas y publicarlas en la web y fichas de producto de MetalWolft, redes sociales, "
    "publicidad, catálogos y materiales promocionales digitales o impresos. Autorizo recortes, "
    "ajustes de iluminación y color, cambios de tamaño y adaptaciones de formato, sin alterar "
    "engañosamente las características del producto. Los proveedores técnicos o publicitarios "
    "podrán trabajar con las fotografías exclusivamente para prestar servicios a MetalWolft, "
    "sin explotación comercial independiente. Dispongo de los derechos necesarios sobre las "
    "imágenes que envío. Entiendo que esta licencia es necesaria para participar en la promoción "
    "de 20 €, que es distinta del tratamiento de datos personales y que mantengo mis derechos "
    "reconocidos por el RGPD."
)

# Frozen version previously offered to customers. Never broaden its agreed scope.
PHOTO_LICENSE_TEXT_BY_VERSION = {
    "photo-license-v2-draft": (
        "Conservo la titularidad de mis fotografías y concedo a MetalWolft una licencia "
        "no exclusiva, de ámbito mundial y por cinco años desde mi aceptación, para "
        "reproducirlas y utilizarlas en su web y fichas de producto, redes sociales, "
        "publicidad online, catálogos y materiales promocionales. Autorizo recortes, "
        "ajustes de iluminación y color, y cambios de tamaño y formato, sin alterar "
        "engañosamente el producto. MetalWolft podrá facilitar las fotografías a "
        "proveedores técnicos o publicitarios que trabajen para ella, sin permitirles "
        "una explotación comercial independiente. Esta licencia no sustituye el "
        "tratamiento de datos personales ni implica renuncia a mis derechos de protección de datos."
    ),
    PHOTO_LICENSE_VERSION: PHOTO_LICENSE_TEXT,
}
