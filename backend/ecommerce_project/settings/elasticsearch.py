"""
Elasticsearch settings for the ecommerce project.
"""
from decouple import config

# Elasticsearch Configuration
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': config('ELASTICSEARCH_HOSTS', default='localhost:9200'),
        'timeout': 60,
        'use_ssl': config('ELASTICSEARCH_USE_SSL', default=False, cast=bool),
        'verify_certs': config('ELASTICSEARCH_VERIFY_CERTS', default=False, cast=bool),
        'http_auth': (
            config('ELASTICSEARCH_USERNAME', default=''),
            config('ELASTICSEARCH_PASSWORD', default='')
        ) if config('ELASTICSEARCH_USERNAME', default='') else None,
    },
}

# Elasticsearch index prefix to avoid conflicts in shared environments
ELASTICSEARCH_INDEX_PREFIX = config('ELASTICSEARCH_INDEX_PREFIX', default='ecommerce')

# Elasticsearch index settings
ELASTICSEARCH_INDEX_SETTINGS = {
    'number_of_shards': config('ELASTICSEARCH_SHARDS', default=1, cast=int),
    'number_of_replicas': config('ELASTICSEARCH_REPLICAS', default=0, cast=int),
    'analysis': {
        'analyzer': {
            'ngram_analyzer': {
                'type': 'custom',
                'tokenizer': 'standard',
                'filter': ['lowercase', 'ngram_filter']
            },
            'edge_ngram_analyzer': {
                'type': 'custom',
                'tokenizer': 'standard',
                'filter': ['lowercase', 'edge_ngram_filter']
            }
        },
        'filter': {
            'ngram_filter': {
                'type': 'ngram',
                'min_gram': 3,
                'max_gram': 10,
            },
            'edge_ngram_filter': {
                'type': 'edge_ngram',
                'min_gram': 2,
                'max_gram': 20,
            }
        }
    }
}

# Elasticsearch DSL auto refresh
ELASTICSEARCH_DSL_AUTO_REFRESH = config('ELASTICSEARCH_DSL_AUTO_REFRESH', default=True, cast=bool)

# Elasticsearch DSL signal processor
ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'apps.search.signals.CelerySignalProcessor'

# Elasticsearch connection timeout
ELASTICSEARCH_TIMEOUT = config('ELASTICSEARCH_TIMEOUT', default=60, cast=int)

# Elasticsearch bulk indexing size
ELASTICSEARCH_BULK_SIZE = config('ELASTICSEARCH_BULK_SIZE', default=100, cast=int)

# Elasticsearch search result size limit
ELASTICSEARCH_MAX_RESULT_WINDOW = config('ELASTICSEARCH_MAX_RESULT_WINDOW', default=10000, cast=int)