> ## Documentation Index
> Fetch the complete documentation index at: https://docs.fish.audio/llms.txt
> Use this file to discover all available pages before exploring further.

# Exceptions

<a id="fishaudio.exceptions" />

# fishaudio.exceptions

Custom exceptions for the Fish Audio SDK.

<a id="fishaudio.exceptions.FishAudioError" />

## FishAudioError Objects

```python theme={null}
class FishAudioError(Exception)
```

Base exception for all Fish Audio SDK errors.

<a id="fishaudio.exceptions.APIError" />

## APIError Objects

```python theme={null}
class APIError(FishAudioError)
```

Raised when the API returns an error response.

<a id="fishaudio.exceptions.AuthenticationError" />

## AuthenticationError Objects

```python theme={null}
class AuthenticationError(APIError)
```

Raised when authentication fails (401).

<a id="fishaudio.exceptions.PermissionError" />

## PermissionError Objects

```python theme={null}
class PermissionError(APIError)
```

Raised when permission is denied (403).

<a id="fishaudio.exceptions.NotFoundError" />

## NotFoundError Objects

```python theme={null}
class NotFoundError(APIError)
```

Raised when a resource is not found (404).

<a id="fishaudio.exceptions.RateLimitError" />

## RateLimitError Objects

```python theme={null}
class RateLimitError(APIError)
```

Raised when rate limit is exceeded (429).

<a id="fishaudio.exceptions.ServerError" />

## ServerError Objects

```python theme={null}
class ServerError(APIError)
```

Raised when the server encounters an error (5xx).

<a id="fishaudio.exceptions.WebSocketError" />

## WebSocketError Objects

```python theme={null}
class WebSocketError(FishAudioError)
```

Raised when WebSocket connection or streaming fails.

<a id="fishaudio.exceptions.ValidationError" />

## ValidationError Objects

```python theme={null}
class ValidationError(FishAudioError)
```

Raised when request validation fails.

<a id="fishaudio.exceptions.DependencyError" />

## DependencyError Objects

```python theme={null}
class DependencyError(FishAudioError)
```

Raised when a required dependency is missing.
