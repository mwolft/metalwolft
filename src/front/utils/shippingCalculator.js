export const calcularEnvio = (cart, threshold = 150) => {
    let subtotal = 0;
    let tipoEnvioFinal = "normal";
    let costeFinal = 0;

    const processedCart = cart.map(product => {
        const alto = parseFloat(product.alto) || 0;
        const ancho = parseFloat(product.ancho) || 0;
        const largo = Math.max(alto, ancho);
        const profundidad = 4; // fijo
        const peso = 10; // estimado en kg
        const sumaDimensiones = largo + Math.min(alto, ancho) + profundidad;

        let tipo = "normal";
        let coste = 0;

        // ----------- NORMA B (99 €) -----------
        if (
            peso > 60 ||
            largo > 300 ||
            sumaDimensiones > 500
        ) {
            tipo = "B";
            coste = 99;
        }

        // ----------- NORMA A (49 €) -----------
        else if (
            peso > 40 ||
            largo > 175 ||
            sumaDimensiones > 300 ||
            largo >= 315
        ) {
            tipo = "A";
            coste = 49;
        }

        subtotal += parseFloat(product.precio_total || 0) * (product.quantity || 1);

        if (tipo === "B") {
            tipoEnvioFinal = "B";
            costeFinal = Math.max(costeFinal, 99);
        } else if (tipo === "A" && tipoEnvioFinal !== "B") {
            tipoEnvioFinal = "A";
            costeFinal = Math.max(costeFinal, 49);
        }

        return {
            ...product,
            shipping_type: tipo,
            shipping_cost: coste
        };
    });

    let totalShipping = 0;
    if (tipoEnvioFinal === "normal" && subtotal >= threshold) {
        totalShipping = 0;
    } else if (tipoEnvioFinal !== "normal") {
        totalShipping = costeFinal;
    } else {
        totalShipping = 17;
    }

    return {
        products: processedCart,
        totalShipping,
        subtotal,
        finalTotal: subtotal + totalShipping
    };
};
