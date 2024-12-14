import flask
import os
from functools import wraps

# simple_trace example
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SpanExporter, BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from lib.common.logger import getLogger
logger = getLogger(__file__)


class DMDataAnalyticsTracerProviderSingleton():
    '''
    singleton-like TracerProvider wrapper class.
    Current TracerProvider shouldn't be overriden (otherwise tracing api will output warning log).
    '''
    instance = None
    provider = None
    resource = Resource.create({SERVICE_NAME: 'DataAnalyticsService'})

    def __new__(cls):
        if not isinstance(cls.instance, cls):
            cls.instance = object.__new__(cls)
            cls.provider = TracerProvider(resource=cls.resource)
            trace.set_tracer_provider(cls.provider)
        return cls.instance


def wrap_flask(app: flask.Flask):

    def _wrap_flask(func):

        @wraps(func)
        def __wrapper(*args, **kwargs):
            FlaskInstrumentor().instrument_app(app)
            RequestsInstrumentor().instrument()
            func(*args, **kwargs)
        return __wrapper

    return _wrap_flask


# name って本当に要る？
def tracing(
    name: str,
    enable_jaeger_tracing: bool = False,
    enable_azure_monitor_tracing: bool = False,
    disable_output_to_console: bool = False):

    provider = DMDataAnalyticsTracerProviderSingleton().provider

    def _tracing(func):

        @wraps(func)
        def __wrapper(*args, **kwargs):

            if disable_output_to_console:
                # do nothing (should be easier to understand than 'if not ...')
                pass 
            else:
                __add_span_processor(provider, ConsoleSpanExporter())

            if enable_jaeger_tracing:
                __add_span_processor(provider, __gen_jaeger_exporter())
                logger.info('jaeger tracing is enabled')
            if enable_azure_monitor_tracing:
                logger.info('azure monitor tracing is enabled')
                __add_span_processor(provider, __gen_azure_monitor_exporter())

            # trace.set_tracer_provider(provider)
            with trace.get_tracer(name).start_as_current_span(func.__name__):
                func(*args, **kwargs)
        return __wrapper

    return _tracing


def __add_span_processor(provider: TracerProvider, exporter: SpanExporter):
    provider.add_span_processor(BatchSpanProcessor(exporter))


def __gen_jaeger_exporter():
    return JaegerExporter(
        agent_host_name="jaeger-agent.jaeger2.svc.cluster.local",
        agent_port=6831
    )


def __gen_azure_monitor_exporter():
    conn_str = os.environ['APPLICATIONINSIGHTS_CONNECTION_STRING']
    return AzureMonitorTraceExporter.from_connection_string(
        conn_str=conn_str
    )


# TODO propagator の検証
@tracing("test_tracer", enable_jaeger_tracing=True)
def test_trace():
    from time import sleep

    while True:
        try:
            sleep(5)
            test_trace_inner()
        except KeyboardInterrupt as I:
            logger.info('KeyboardInterrupt. exit process')
            exit(0)


@tracing("test_tracer_inner")
def test_trace_inner():
    logger.info('test_trace_inner is called.')


if __name__ == '__main__':
    test_trace()
