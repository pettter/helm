from typing import Optional

from helm.benchmark.model_deployment_registry import ModelDeployment, WindowServiceSpec, get_model_deployment
from helm.benchmark.window_services.remote_window_service import get_remote_window_service
from helm.benchmark.window_services.window_service import WindowService
from helm.benchmark.window_services.tokenizer_service import TokenizerService
from helm.proxy.clients.remote_model_registry import get_remote_deployment
from helm.common.object_spec import create_object, inject_object_spec_args


class WindowServiceFactory:
    @staticmethod
    def get_window_service(model_deployment_name: str, service: TokenizerService) -> WindowService:
        """
        Returns a `WindowService` given the name of the model.
        Make sure this function returns instantaneously on repeated calls.
        """
        model_deployment: Optional[ModelDeployment] = get_model_deployment(model_deployment_name)
        if model_deployment:
            # If the model deployment specifies a WindowServiceSpec, instantiate it.
            window_service_spec: WindowServiceSpec
            if model_deployment.window_service_spec:
                window_service_spec = model_deployment.window_service_spec
            else:
                window_service_spec = WindowServiceSpec(
                    class_name="helm.benchmark.window_services.default_window_service.DefaultWindowService", args={}
                )
            # Perform dependency injection to fill in remaining arguments.
            # Dependency injection is needed here for these reasons:
            #
            # 1. Different window services have different parameters. Dependency injection provides arguments
            #    that match the parameters of the window services.
            # 2. Some arguments, such as the tokenizer service, are not static data objects that can be
            #    in the users configuration file. Instead, they have to be constructed dynamically at runtime.
            window_service_spec = inject_object_spec_args(
                window_service_spec,
                {
                    "service": service,
                    "tokenizer_name": model_deployment.tokenizer_name,
                    "max_sequence_length": model_deployment.max_sequence_length,
                    "max_request_length": model_deployment.max_request_length,
                },
            )
            return create_object(window_service_spec)
        elif get_remote_deployment(model_deployment_name):
            return get_remote_window_service(service, model_deployment_name)

        raise ValueError(f"Unhandled model deployment name: {model_deployment_name}")
