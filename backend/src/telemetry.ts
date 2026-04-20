import { NodeSDK } from '@opentelemetry/sdk-node';
import { PrometheusExporter } from '@opentelemetry/exporter-prometheus';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';

let sdk: NodeSDK | null = null;

export function setupTelemetry(): void {
  if (sdk) return; // idempotent

  const prometheusExporter = new PrometheusExporter({ port: 9464 });
  prometheusExporter.startServer();
  console.log('Prometheus scrape endpoint: http://0.0.0.0:9464/metrics');

  sdk = new NodeSDK({
    metricReader: prometheusExporter,
    instrumentations: [
      getNodeAutoInstrumentations({
        '@opentelemetry/instrumentation-fs': { enabled: false } as any, // too noisy
      }),
    ],
  });

  sdk.start();

  process.on('SIGTERM', () => {
    sdk!.shutdown().finally(() => process.exit(0));
  });

  process.on('SIGINT', () => {
    sdk!.shutdown().finally(() => process.exit(0));
  });
}
