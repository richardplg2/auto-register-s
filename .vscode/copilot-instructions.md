# VS Code Copilot Instructions for Dahua Camera System

## Project Context

This is a Dahua camera auto-register system with the following components:

- Auto Register Service (NetSDK integration)
- Device Management Service (FastAPI REST API)
- Event Accession Service (Redis Stream consumer)
- Webhook Dispatcher (HTTP client with retry logic)

## Code Style Guidelines

### Python General Rules

- Use Python 3.12+ features
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return types
- Use `async`/`await` for all I/O operations
- Use `dataclasses` or `pydantic` models for data structures
- Use `pathlib` instead of `os.path`
- Use f-strings for string formatting
- Use `logging` module instead of print statements
- Use `pytest` for testing

### Naming Conventions

- Use `snake_case` for functions, variables, and module names
- Use `PascalCase` for classes
- Use `UPPER_SNAKE_CASE` for constants
- Use descriptive names that explain the purpose
- Prefix private methods with underscore `_`
- Use `async` prefix for async functions when clarity is needed

### Class Structure

- Use `pydantic.BaseModel` for data models
- Use `enum.Enum` for constants and choices
- Use `@dataclass` for simple data containers
- Use `@property` for computed attributes
- Group class methods logically: `__init__`, public methods, private methods
- Use dependency injection patterns

### Async/Await Patterns

- Always use `async def` for functions that perform I/O
- Use `await` for all async operations
- Use `asyncio.gather()` for concurrent operations
- Use `async with` for context managers
- Use `asyncio.create_task()` for fire-and-forget operations
- Handle exceptions properly in async contexts

### Error Handling

- Use specific exception types instead of generic `Exception`
- Create custom exception classes for business logic errors
- Use `try`/`except`/`finally` blocks appropriately
- Log errors with appropriate levels (ERROR, WARNING, INFO)
- Use structured logging with context information
- Implement retry logic with exponential backoff

### API Development (FastAPI)

- Use dependency injection for common dependencies
- Use Pydantic models for request/response validation
- Use proper HTTP status codes
- Implement proper error handling with custom exception handlers
- Use async route handlers
- Add comprehensive OpenAPI documentation
- Use middleware for cross-cutting concerns

### Database Operations

- Use async database drivers (asyncpg, aiomysql)
- Use connection pooling
- Use prepared statements to prevent SQL injection
- Use database migrations for schema changes
- Use repository pattern for data access
- Use transactions for multi-step operations

### Configuration Management

- Use environment variables for configuration
- Use `pydantic.BaseSettings` for configuration models
- Validate configuration at startup
- Use different configurations for different environments
- Keep secrets secure and separate from code

### Testing

- Write unit tests for all business logic
- Use async test functions for testing async code
- Use fixtures for common test data
- Mock external dependencies
- Use `pytest.mark.asyncio` for async tests
- Test error conditions and edge cases

### Logging and Monitoring

- Use structured logging with JSON format
- Include correlation IDs for tracing
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Use metrics for monitoring (Prometheus format)
- Include performance metrics (timing, counts)
- Log sensitive data appropriately (mask or exclude)

### Code Organization

- Use clear module structure with `__init__.py` files
- Group related functionality in packages
- Use service layer for business logic
- Use repository layer for data access
- Keep controllers thin, services fat
- Use dependency injection containers

### Security

- Validate all input data
- Use parameterized queries
- Implement proper authentication and authorization
- Use HTTPS for all external communications
- Hash sensitive data appropriately
- Follow principle of least privilege

### Performance

- Use async I/O for concurrent operations
- Implement caching where appropriate
- Use connection pooling for databases
- Optimize database queries
- Use pagination for large result sets
- Implement proper resource cleanup

## Service-Specific Guidelines

### Auto Register Service

- Use ctypes properly for NetSDK integration
- Implement proper callback function signatures
- Handle SDK initialization and cleanup
- Use thread-safe operations for callbacks
- Implement proper session management

### Device Management Service

- Use FastAPI dependency injection
- Implement proper API versioning
- Use proper HTTP methods (GET, POST, PUT, DELETE)
- Implement pagination for list endpoints
- Use proper authentication middleware

### Event Accession Service

- Use Redis Streams for event processing
- Implement proper consumer group management
- Use batch processing for efficiency
- Implement proper error handling and retry logic
- Use circuit breaker pattern for external services

### Webhook Dispatcher

- Implement proper HTTP client with timeout
- Use exponential backoff for retries
- Implement circuit breaker pattern
- Use proper rate limiting
- Handle webhook failures gracefully

## Example Code Patterns

### Async Service Class

```python
class CameraService:
    def __init__(self, sdk_client: NetSDKClient, redis_client: Redis):
        self.sdk_client = sdk_client
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)

    async def register_camera(self, config: CameraConfig) -> SessionResult:
        try:
            session = await self.sdk_client.login(config.ip, config.username, config.password)
            await self.redis_client.hset(f"session:{config.id}", mapping=session.dict())
            self.logger.info("Camera registered successfully", extra={"camera_id": config.id})
            return SessionResult(success=True, session_id=session.id)
        except SDKError as e:
            self.logger.error("Failed to register camera", extra={"camera_id": config.id, "error": str(e)})
            raise CameraRegistrationError(f"Failed to register camera {config.id}") from e
```

### Pydantic Model

```python
class CameraConfig(BaseModel):
    id: str = Field(..., description="Unique camera identifier")
    name: str = Field(..., description="Camera display name")
    ip: str = Field(..., description="Camera IP address")
    port: int = Field(default=37777, description="Camera port")
    username: str = Field(..., description="Camera username")
    password: str = Field(..., description="Camera password")
    location: Optional[str] = Field(None, description="Camera location")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "cam_001",
                "name": "Front Door Camera",
                "ip": "192.168.1.100",
                "port": 37777,
                "username": "admin",
                "password": "password123",
                "location": "Building A"
            }
        }
```

### Error Handling

```python
class CameraError(Exception):
    """Base exception for camera operations"""
    pass

class CameraRegistrationError(CameraError):
    """Exception raised when camera registration fails"""
    pass

async def handle_camera_operation():
    try:
        result = await camera_service.register_camera(config)
        return result
    except CameraRegistrationError as e:
        logger.error("Camera registration failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Camera registration failed")
    except Exception as e:
        logger.error("Unexpected error", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Code Review Checklist

- [ ] All functions have proper type hints
- [ ] Async functions are used for I/O operations
- [ ] Error handling is implemented properly
- [ ] Logging includes appropriate context
- [ ] Configuration is externalized
- [ ] Tests are written for new functionality
- [ ] Documentation is updated
- [ ] Security best practices are followed
- [ ] Performance considerations are addressed
- [ ] Code follows project conventions

Remember to:

- Keep functions small and focused
- Use meaningful variable names
- Write self-documenting code
- Add comments for complex business logic
- Follow the Single Responsibility Principle
- Use composition over inheritance
- Implement proper separation of concerns
