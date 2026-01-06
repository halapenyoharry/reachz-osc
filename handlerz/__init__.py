"""
Reachz Handlerz - Modular OSC Handlers

Each handler module:
1. Has a docstring describing input/output/use cases
2. Defines ADDRESSES list of OSC paths it handles
3. Provides a register(dispatcher) function
"""

import importlib
import pkgutil
from pathlib import Path


def discover_handlers():
    """Auto-discover all handler modules in this package."""
    handlers = []
    package_dir = Path(__file__).parent
    
    for module_info in pkgutil.iter_modules([str(package_dir)]):
        if module_info.name.startswith('_'):
            continue
        try:
            module = importlib.import_module(f'.{module_info.name}', package=__name__)
            if hasattr(module, 'register'):
                handlers.append(module)
        except Exception as e:
            print(f"Warning: Failed to load handler '{module_info.name}': {e}")
    
    return handlers


def register_all(dispatcher):
    """Register all discovered handlers with the dispatcher."""
    handlers = discover_handlers()
    all_addresses = []
    
    for handler in handlers:
        handler.register(dispatcher)
        if hasattr(handler, 'ADDRESSES'):
            all_addresses.extend(handler.ADDRESSES)
        handler_name = handler.__name__.split('.')[-1]
        print(f"  ✓ {handler_name}")
    
    return all_addresses
