export const contactDetails = {
  phoneDisplay: "+34 634 11 26 04",
  phoneRaw: "34634112604",
  email: "admin@metalwolft.com",
  whatsappMessage: "Hola, necesito ayuda con unas rejas para ventanas a medida.",
  supportArea: "España"
} as const;

export const contactLinks = {
  phone: `tel:+${contactDetails.phoneRaw}`,
  whatsapp: `https://wa.me/${contactDetails.phoneRaw}?text=${encodeURIComponent(contactDetails.whatsappMessage)}`,
  email: `mailto:${contactDetails.email}?subject=${encodeURIComponent("Consulta sobre rejas para ventanas")}`,
  quote: "/rejas-para-ventanas"
} as const;
