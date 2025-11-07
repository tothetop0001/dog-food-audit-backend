#!/usr/bin/env python3
"""Run scraping job manually."""

import asyncio
import os
import sys
import warnings
from pathlib import Path

# Set Windows-specific event loop policy to reduce overlapped warnings
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    # Suppress Windows asyncio overlapped I/O warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="asyncio")
    # Suppress the specific overlapped I/O RuntimeError warnings
    import logging
    logging.getLogger('asyncio').setLevel(logging.CRITICAL)

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal, init_db
from app.core.logging import configure_logging, get_logger
from app.services.scraping_service import ScrapingService
from app.services.services_openai import OpenAIService
from app.services.processing_detection_service import infer_processing_method

configure_logging()
logger = get_logger(__name__)


async def run_scraping():
    """Run the scraping job."""
    async with AsyncSessionLocal() as db:
        await init_db()
        service = ScrapingService(db)
        logger.info("Starting manual scraping job...")
        results = await service.run_scraping_job()
        
        # await openai_service.analyze_results(results)
        openai_service = OpenAIService()
        # await openai_service.get_result()
        return results


async def main():
    """Main function."""
    try:
        results = await run_scraping()
        logger.info("Scraping completed successfully", total_items=len(results))
        
        # Give a moment for any pending operations to complete
        await asyncio.sleep(0.5)
        
        # Force cleanup of any remaining tasks
        try:
            pending = asyncio.all_tasks()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
        except Exception:
            pass
        
        # Additional cleanup for Windows
        if sys.platform == "win32":
            try:
                # Cancel any remaining tasks
                for task in asyncio.all_tasks():
                    if not task.done():
                        task.cancel()
                # Wait a bit for cancellation to complete
                await asyncio.sleep(0.1)
            except Exception:
                pass
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        # Suppress Windows asyncio overlapped I/O warnings by redirecting stderr
        if sys.platform == "win32":
            import contextlib
            import io
            
            @contextlib.contextmanager
            def suppress_stderr():
                with open(os.devnull, "w") as devnull:
                    old_stderr = sys.stderr
                    sys.stderr = devnull
                    try:
                        yield
                    finally:
                        sys.stderr = old_stderr
            
            with suppress_stderr():
                # Use a more controlled event loop shutdown
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(main())
                finally:
                    # Properly close the loop
                    try:
                        loop.close()
                    except Exception:
                        pass
        else:
            asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
