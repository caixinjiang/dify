import json
from typing import Type

from langchain.llms import Xinference

from core.helper import encrypter
from core.model_providers.models.entity.model_params import KwargRule, ModelKwargsRules, ModelType
from core.model_providers.models.llm.xinference_model import XinferenceModel
from core.model_providers.providers.base import BaseModelProvider, CredentialsValidateFailedError

from core.model_providers.models.base import BaseProviderModel
from models.provider import ProviderType


class XinferenceProvider(BaseModelProvider):
    @property
    def provider_name(self):
        """
        Returns the name of a provider.
        """
        return 'xinference'

    def _get_fixed_model_list(self, model_type: ModelType) -> list[dict]:
        return []

    def get_model_class(self, model_type: ModelType) -> Type[BaseProviderModel]:
        """
        Returns the model class.

        :param model_type:
        :return:
        """
        if model_type == ModelType.TEXT_GENERATION:
            model_class = XinferenceModel
        else:
            raise NotImplementedError

        return model_class

    def get_model_parameter_rules(self, model_name: str, model_type: ModelType) -> ModelKwargsRules:
        """
        get model parameter rules.

        :param model_name:
        :param model_type:
        :return:
        """
        return ModelKwargsRules(
            temperature=KwargRule[float](min=0, max=2, default=1),
            top_p=KwargRule[float](min=0, max=1, default=0.7),
            presence_penalty=KwargRule[float](min=-2, max=2, default=0),
            frequency_penalty=KwargRule[float](min=-2, max=2, default=0),
            max_tokens=KwargRule[int](min=10, max=4000, default=256),
        )

    @classmethod
    def is_model_credentials_valid_or_raise(cls, model_name: str, model_type: ModelType, credentials: dict):
        """
        check model credentials valid.

        :param model_name:
        :param model_type:
        :param credentials:
        """
        if 'server_url' not in credentials:
            raise CredentialsValidateFailedError('Xinference Server URL must be provided.')

        if 'model_uid' not in credentials:
            raise CredentialsValidateFailedError('Xinference Model UID must be provided.')

        try:
            credential_kwargs = {
                'server_url': credentials['server_url'],
                'model_uid': credentials['model_uid'],
            }

            llm = Xinference(
                **credential_kwargs
            )

            llm("ping", generate_config={'max_tokens': 10})
        except Exception as ex:
            raise CredentialsValidateFailedError(str(ex))

    @classmethod
    def encrypt_model_credentials(cls, tenant_id: str, model_name: str, model_type: ModelType,
                                  credentials: dict) -> dict:
        """
        encrypt model credentials for save.

        :param tenant_id:
        :param model_name:
        :param model_type:
        :param credentials:
        :return:
        """
        credentials['server_url'] = encrypter.encrypt_token(tenant_id, credentials['server_url'])
        return credentials

    def get_model_credentials(self, model_name: str, model_type: ModelType, obfuscated: bool = False) -> dict:
        """
        get credentials for llm use.

        :param model_name:
        :param model_type:
        :param obfuscated:
        :return:
        """
        if self.provider.provider_type != ProviderType.CUSTOM.value:
            raise NotImplementedError

        provider_model = self._get_provider_model(model_name, model_type)

        if not provider_model.encrypted_config:
            return {
                'server_url': None,
                'model_uid': None,
            }

        credentials = json.loads(provider_model.encrypted_config)
        if credentials['server_url']:
            credentials['server_url'] = encrypter.decrypt_token(
                self.provider.tenant_id,
                credentials['server_url']
            )

            if obfuscated:
                credentials['server_url'] = encrypter.obfuscated_token(credentials['server_url'])

        return credentials

    @classmethod
    def is_provider_credentials_valid_or_raise(cls, credentials: dict):
        return

    @classmethod
    def encrypt_provider_credentials(cls, tenant_id: str, credentials: dict) -> dict:
        return {}

    def get_provider_credentials(self, obfuscated: bool = False) -> dict:
        return {}
