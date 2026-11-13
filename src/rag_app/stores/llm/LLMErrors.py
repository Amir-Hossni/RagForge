class LLMProviderError(Exception):
    # the provider call failed or came back without usable output
    pass


class EmbeddingError(LLMProviderError):
    # embedding failed, or returned the wrong number / size of vectors
    pass


class UnsupportedProviderError(Exception):
    # unknown provider name, or its API key is not set
    pass
