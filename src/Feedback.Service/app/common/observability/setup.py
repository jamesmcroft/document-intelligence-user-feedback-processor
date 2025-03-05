from opentelemetry.sdk.resources import Resource
from opentelemetry import trace as otel_trace
from opentelemetry import _logs as otel_logs
from opentelemetry import metrics as otel_metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import ConsoleLogExporter, SimpleLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter, AzureMonitorLogExporter, AzureMonitorMetricExporter
from app.common.app_settings import app_settings

def setup_observability():
    # Configure observability
    resource = Resource.create({"service.name": app_settings.app_name})

    otel_trace.set_tracer_provider(TracerProvider(resource=resource))
    trace_provider = otel_trace.get_tracer_provider()

    otel_logs.set_logger_provider(LoggerProvider(resource=resource))
    logger_provider = otel_logs.get_logger_provider()

    otel_metric_readers = []

    # Configure console exporter
    console_trace_exporter = ConsoleSpanExporter()
    console_span_processor = SimpleSpanProcessor(console_trace_exporter)
    trace_provider.add_span_processor(console_span_processor)

    console_log_exporter = ConsoleLogExporter()
    console_log_processor = SimpleLogRecordProcessor(console_log_exporter)
    logger_provider.add_log_record_processor(console_log_processor)

    console_metric_exporter = ConsoleMetricExporter()
    otel_metric_readers.append(PeriodicExportingMetricReader(
        exporter=console_metric_exporter,
        export_interval_millis=app_settings.otel_exporter_export_interval
    ))

    # Configure generic OTLP exporters
    if app_settings.otel_exporter_otlp_endpoint:
        otel_trace_exporter = OTLPSpanExporter(
            endpoint=app_settings.otel_exporter_otlp_endpoint
        )
        otel_span_processor = BatchSpanProcessor(otel_trace_exporter)
        trace_provider.add_span_processor(otel_span_processor)

        otel_log_exporter = OTLPLogExporter(
            endpoint=app_settings.otel_exporter_otlp_endpoint
        )
        otel_log_processor = BatchLogRecordProcessor(otel_log_exporter)
        logger_provider.add_log_record_processor(otel_log_processor)

        otel_metric_exporter = OTLPMetricExporter(
            endpoint=app_settings.otel_exporter_otlp_endpoint
        )
        otel_metric_reader = PeriodicExportingMetricReader(
            exporter=otel_metric_exporter,
            export_interval_millis=app_settings.otel_exporter_export_interval
        )
        otel_metric_readers.append(otel_metric_reader)

    # Configure Azure Monitor exporters
    if app_settings.applicationinsights_connection_string:
        azure_trace_exporter = AzureMonitorTraceExporter(
            connection_string=app_settings.applicationinsights_connection_string
        )
        azure_span_processor = BatchSpanProcessor(azure_trace_exporter)
        trace_provider.add_span_processor(azure_span_processor)

        azure_log_exporter = AzureMonitorLogExporter(
            connection_string=app_settings.applicationinsights_connection_string
        )
        azure_log_processor = BatchLogRecordProcessor(azure_log_exporter)
        logger_provider.add_log_record_processor(azure_log_processor)

        azure_metric_exporter = AzureMonitorMetricExporter(
            connection_string=app_settings.applicationinsights_connection_string
        )
        azure_metric_reader = PeriodicExportingMetricReader(
            exporter=azure_metric_exporter,
            export_interval_millis=app_settings.otel_exporter_export_interval
        )
        otel_metric_readers.append(azure_metric_reader)

    otel_metrics.set_meter_provider(MeterProvider(metric_readers=otel_metric_readers, resource=resource))
    meter_provider = otel_metrics.get_meter_provider()

    LoggingInstrumentor().instrument(set_logging_format=True)

    return trace_provider, logger_provider, meter_provider
