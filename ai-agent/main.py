"""
AI Agent Application Entry
"""
import asyncio
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Import unified API routes
from api.routes import api_v1_router, api_v2_router
from api.middleware.error_handler import add_error_handlers
from api.middleware.logging import add_logging_middleware

# Data layer
from data import initialize_data_layer, cleanup_data_layer
from core import AcademicAgent

# Configuration and utilities
from configs.settings import settings
from utils.logger import setup_logging, get_logger


setup_logging()
logger = get_logger(__name__)

# Global Agent instance
agent_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    global agent_instance
    
    # Initialize on startup
    logger.info("Starting AI Agent application")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"Log Level: {settings.log_level}")
    try:
        # 1. Initialize data layer
        logger.info("Initializing data layer...")
        data_success = await initialize_data_layer()
        if not data_success:
            raise Exception("Failed to initialize data layer")
        logger.info("Data layer initialized successfully")
        
        # 2. Initialize Agent
        logger.info("Initializing AI Agent...")
        agent_instance = AcademicAgent()
        await agent_instance.initialize()
        app.state.agent = agent_instance
        logger.info("AI Agent initialized successfully")
        
        # 3. Application ready
        logger.info("AI Agent application started successfully")
        yield
        
    except Exception as e:
        logger.error("Failed to initialize AI Agent application", error=str(e))
        raise
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down AI Agent application...")
        
        # Cleanup Agent
        if agent_instance:
            try:
                await agent_instance.cleanup()
                logger.info("AI Agent cleanup completed")
            except Exception as e:
                logger.error("Error during agent cleanup", error=str(e))
        
        # Cleanup data layer
        try:
            await cleanup_data_layer()
            logger.info("Data layer cleanup completed")
        except Exception as e:
            logger.error("Error during data layer cleanup", error=str(e))
        
        logger.info("AI Agent application shutdown completed")

def create_app() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI Agent for Academic Research - MVP Version",
        debug=settings.debug,
        lifespan=lifespan,
        # API documentation configuration
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Add middleware (order is important)
    add_error_handlers(app)
    add_logging_middleware(app)
    
    # Register API routes - now just one line!
    app.include_router(api_v1_router, prefix="/api/v1")
    app.include_router(api_v2_router, prefix="/api/v2")
    
    # Debug: print all routes
    if settings.debug:
        logger.info("=== Registered Routes ===")
        for route in app.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = list(route.methods)
                logger.info(f"  {methods} -> {route.path}")
        logger.info("========================")

    # Add root path handler
    @app.get("/", tags=["root"])
    async def root():
        """Root path - Service information"""
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs_url": "/docs" if settings.debug else "disabled",
            "api_versions": ["v1", "v2"],
            "api_prefixes": ["/api/v1", "/api/v2"]
        }
    
    # Add API information path
    @app.get("/api", tags=["root"])
    async def api_info():
        """API information"""
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "supported_versions": ["v1", "v2"],
            "endpoints": {
                "v1": {
                    "health": "/api/v1/health",
                    "chat": "/api/v1/chat", 
                    "conversations": "/api/v1/conversations"
                },
                "v2": {
                    "health": "/api/v2/health",
                    "chat": "/api/v2/chat", 
                    "conversations": "/api/v2/conversations"
                }
            }
        }
    
    @app.get("/api/v2", tags=["v2"])
    async def api_v2_info():
        """API V2 information"""
        return {
            "version": "v2",
            "status": "beta",
            "endpoints": {
                "health": "/api/v2/health",
                "chat": "/api/v2/chat", 
                "conversations": "/api/v2/conversations"
            }
        }
    
    return app

# Create application instance
app = create_app()

if __name__ == "__main__":
    # Development environment running configuration
    uvicorn_config = {
        "app": "main:app",
        "host": settings.host,
        "port": settings.port,
        "reload": settings.debug,
        "log_level": settings.log_level.lower(),
        "access_log": True,
        "use_colors": True,
    }
    
    # If in production environment, add additional configuration
    if not settings.debug:
        uvicorn_config.update({
            "workers": 1,  # Single process for MVP version
            "reload": False,
            "access_log": False,
        })
    
    logger.info("Starting AI Agent server...")
    logger.info(f"Server will be available at: http://{settings.host}:{settings.port}")
    logger.info(f"API documentation: http://{settings.host}:{settings.port}/docs")
    
    uvicorn.run(**uvicorn_config)
