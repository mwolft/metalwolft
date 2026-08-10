import assert from "node:assert/strict";
import {
  ProductConfigurationClientError,
  isTemporaryConfigurationNetworkError,
  requestProductConfiguration
} from "./product-configuration-client.ts";

const validConfiguration = {
  schema_version: 2,
  product_id: 7,
  dimensions: {
    alto: { min_cm: 30, max_cm: 250 },
    ancho: { min_cm: 30, max_cm: 250 },
    max_sum_cm: 400
  },
  anchorages: [
    {
      value: "Sin obra: con agujeros interiores",
      name: "Agujeros interiores",
      label: "Sin obra: con agujeros interiores",
      description: "Instalación sin obra mediante agujeros interiores.",
      supplement: 0,
      enabled: true,
      screw_required: true
    },
    {
      value: "Sin obra: con pletinas",
      name: "Pletinas",
      label: "Sin obra: con pletinas",
      description: "Instalación sin obra mediante pletinas.",
      supplement: 24.95,
      enabled: true,
      screw_required: true
    }
  ],
  colors: [
    {
      value: "satinado_blanco",
      name: "Blanco",
      label: "Blanco liso",
      finish: "liso",
      finish_label: "Satinado liso",
      enabled: true
    }
  ],
  screw_options: {
    "Sin obra: con agujeros interiores": [
      {
        value: "standard",
        label: "Estándar incluida",
        description: "Incluida en el pedido",
        length_mm: 80,
        supplement: 0,
        enabled: true
      },
      {
        value: "long_150",
        label: "Tornillos largos",
        description: "Para huecos que necesitan mayor profundidad de fijación",
        length_mm: 150,
        supplement: 8.95,
        enabled: true
      }
    ],
    "Sin obra: con pletinas": [
      {
        value: "standard",
        label: "Estándar incluida",
        description: "Incluida en el pedido",
        length_mm: 70,
        supplement: 0,
        enabled: true
      }
    ]
  },
  defaults: {
    anchorage: "Sin obra: con agujeros interiores",
    color: "satinado_blanco",
    screw_option: "standard"
  }
};

{
  const configuration = await requestProductConfiguration(7, {
    apiBaseUrl: "https://api.example.test",
    fetcher: async () =>
      Response.json({
        ...validConfiguration,
        anchorages: [
          ...validConfiguration.anchorages,
          {
            value: "Con obra: con garras metálicas",
            name: "Garras metálicas",
            label: "Con obra: con garras metálicas",
            description: "Instalación con obra mediante garras metálicas.",
            supplement: 49.95,
            enabled: true,
            screw_required: false
          }
        ],
        screw_options: {
          ...validConfiguration.screw_options,
          "Con obra: con garras metálicas": []
        }
      })
  });

  assert.equal(configuration.anchorages[2].screw_required, false);
}

{
  let capturedUrl = "";
  const controller = new AbortController();
  const configuration = await requestProductConfiguration(7, {
    apiBaseUrl: "https://api.example.test/",
    signal: controller.signal,
    fetcher: async (url, init) => {
      capturedUrl = String(url);
      assert.equal(init?.signal, controller.signal);
      return Response.json(validConfiguration);
    }
  });

  assert.deepEqual(configuration, validConfiguration);
  assert.equal(capturedUrl, "https://api.example.test/api/products/7/configuration");
}

{
  await assert.rejects(
    requestProductConfiguration(7, {
      apiBaseUrl: "https://api.example.test",
      fetcher: async () =>
        Response.json({
          ...validConfiguration,
          screw_options: {
            ...validConfiguration.screw_options,
            "Sin obra: con agujeros interiores": []
          }
        })
    }),
    (error) => error instanceof ProductConfigurationClientError && error.kind === "contract"
  );
}

{
  await assert.rejects(
    requestProductConfiguration(7, {
      apiBaseUrl: "https://api.example.test",
      fetcher: async () => {
        throw new TypeError("network unavailable");
      }
    }),
    (error) => isTemporaryConfigurationNetworkError(error)
  );
}

for (const status of [400, 404, 429, 500, 503]) {
  await assert.rejects(
    requestProductConfiguration(7, {
      apiBaseUrl: "https://api.example.test",
      fetcher: async () => Response.json({ message: "Internal error" }, { status })
    }),
    (error) =>
      error instanceof ProductConfigurationClientError &&
      error.kind === "http" &&
      error.status === status &&
      !isTemporaryConfigurationNetworkError(error)
  );
}

{
  await assert.rejects(
    requestProductConfiguration(7, {
      apiBaseUrl: "https://api.example.test",
      fetcher: async () =>
        Response.json({
          ...validConfiguration,
          defaults: { ...validConfiguration.defaults, color: "color_inexistente" }
        })
    }),
    (error) => error instanceof ProductConfigurationClientError && error.kind === "contract"
  );
}

{
  await assert.rejects(
    requestProductConfiguration(7, {
      apiBaseUrl: "https://api.example.test",
      fetcher: async () => Response.json({ ...validConfiguration, product_id: 9 })
    }),
    (error) => error instanceof ProductConfigurationClientError && error.kind === "contract"
  );
}

{
  await assert.rejects(
    requestProductConfiguration(7, {
      apiBaseUrl: "https://api.example.test",
      fetcher: async () =>
        Response.json({
          ...validConfiguration,
          colors: validConfiguration.colors.map(({ label, ...color }) => color)
        })
    }),
    (error) => error instanceof ProductConfigurationClientError && error.kind === "contract"
  );
}

{
  const abortError = new DOMException("Aborted", "AbortError");
  await assert.rejects(
    requestProductConfiguration(7, {
      apiBaseUrl: "https://api.example.test",
      fetcher: async () => {
        throw abortError;
      }
    }),
    (error) => error === abortError && !isTemporaryConfigurationNetworkError(error)
  );
}

console.log("12 product configuration client tests passed");
