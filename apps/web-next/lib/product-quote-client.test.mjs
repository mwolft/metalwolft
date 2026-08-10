import assert from "node:assert/strict";
import {
  ProductQuoteClientError,
  isTemporaryQuoteNetworkError,
  requestProductQuote
} from "./product-quote-client.ts";


const validQuote = {
  product_id: 7,
  quantity: 1,
  alto: 100,
  ancho: 120,
  anclaje: "Sin obra: con pletinas",
  color: "satinado_blanco",
  screw_option: "long_150",
  screw_length_mm: 150,
  currency: "EUR",
  base_unit_price: 120,
  anchorage_supplement: 24.95,
  screw_supplement: 8.95,
  unit_price: 153.9,
  subtotal: 153.9
};

const request = {
  productId: 7,
  alto: 100,
  ancho: 120,
  anclaje: "Sin obra: con pletinas",
  color: "satinado_blanco",
  screw_option: "long_150"
};

{
  let capturedUrl = "";
  let capturedInit;
  const controller = new AbortController();
  const quote = await requestProductQuote(request, {
    apiBaseUrl: "https://api.example.test/",
    signal: controller.signal,
    fetcher: async (url, init) => {
      capturedUrl = String(url);
      capturedInit = init;
      return Response.json(validQuote);
    }
  });

  assert.deepEqual(quote, validQuote);
  assert.equal(capturedUrl, "https://api.example.test/api/products/7/quote");
  assert.equal(capturedInit.method, "POST");
  assert.equal(capturedInit.signal, controller.signal);
  assert.deepEqual(JSON.parse(capturedInit.body), {
    alto: 100,
    ancho: 120,
    anclaje: "Sin obra: con pletinas",
    color: "satinado_blanco",
    screw_option: "long_150",
    quantity: 1
  });
}

{
  const clawsQuote = await requestProductQuote(
    {
      ...request,
      anclaje: "Con obra: con garras metálicas",
      screw_option: "not_applicable"
    },
    {
      apiBaseUrl: "https://api.example.test",
      fetcher: async () =>
        Response.json({
          ...validQuote,
          anclaje: "Con obra: con garras metálicas",
          screw_option: "not_applicable",
          screw_length_mm: null,
          anchorage_supplement: 49.95,
          screw_supplement: 0,
          unit_price: 169.95,
          subtotal: 169.95
        })
    }
  );

  assert.equal(clawsQuote.screw_length_mm, null);
  assert.equal(clawsQuote.screw_option, "not_applicable");
}

{
  await assert.rejects(
    requestProductQuote(request, {
      apiBaseUrl: "https://api.example.test",
      fetcher: async () => Response.json({ message: "Dimensiones fuera de rango" }, { status: 400 })
    }),
    (error) =>
      error instanceof ProductQuoteClientError &&
      error.kind === "http" &&
      error.status === 400 &&
      error.message === "Dimensiones fuera de rango" &&
      !isTemporaryQuoteNetworkError(error)
  );
}

{
  await assert.rejects(
    requestProductQuote(request, {
      apiBaseUrl: "https://api.example.test",
      fetcher: async () => {
        throw new TypeError("network unavailable");
      }
    }),
    (error) => isTemporaryQuoteNetworkError(error)
  );
}

for (const status of [400, 404, 429, 500, 503]) {
  await assert.rejects(
    requestProductQuote(request, {
      apiBaseUrl: "https://api.example.test",
      fetcher: async () => Response.json({ message: "Internal server error" }, { status })
    }),
    (error) =>
      error instanceof ProductQuoteClientError &&
      error.kind === "http" &&
      error.status === status &&
      !isTemporaryQuoteNetworkError(error)
  );
}

{
  await assert.rejects(
    requestProductQuote(request, {
      apiBaseUrl: "https://api.example.test",
      fetcher: async () => Response.json({ ...validQuote, product_id: 99 })
    }),
    (error) => error instanceof ProductQuoteClientError && error.kind === "contract"
  );
}

{
  const abortError = new DOMException("Aborted", "AbortError");
  await assert.rejects(
    requestProductQuote(request, {
      apiBaseUrl: "https://api.example.test",
      fetcher: async () => {
        throw abortError;
      }
    }),
    (error) => error === abortError && !isTemporaryQuoteNetworkError(error)
  );
}

console.log("10 product quote client tests passed");
