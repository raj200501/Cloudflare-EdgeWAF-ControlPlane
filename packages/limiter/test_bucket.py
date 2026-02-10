from packages.limiter.bucket import InMemoryTokenBucket, TokenBucketConfig


def test_token_bucket_allows_and_blocks():
    now = 0.0

    def time_fn():
        return now

    bucket = InMemoryTokenBucket(TokenBucketConfig(rate_per_sec=1, burst=2), time_fn=time_fn)
    assert bucket.allow("ip") is True
    assert bucket.allow("ip") is True
    assert bucket.allow("ip") is False
    now += 1.0
    assert bucket.allow("ip") is True


def test_token_bucket_purges():
    now = 0.0

    def time_fn():
        return now

    bucket = InMemoryTokenBucket(
        TokenBucketConfig(rate_per_sec=1, burst=1, ttl_seconds=1),
        time_fn=time_fn,
    )
    assert bucket.allow("ip") is True
    now += 2
    bucket.purge_expired()
    assert bucket.allow("ip") is True
