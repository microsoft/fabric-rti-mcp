"""
Intelligent Eventstream service module for Microsoft Fabric RTI MCP
Provides high-level, natural language interface to Eventstream operations
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from fabric_rti_mcp.common import logger
from fabric_rti_mcp.eventstream import eventstream_service


@dataclass
class UserContext:
    """Stores user context and preferences"""
    default_workspace_id: Optional[str] = None
    default_auth_token: Optional[str] = None
    recent_workspaces: List[str] = field(default_factory=list)
    workspace_aliases: Dict[str, str] = field(default_factory=dict)


@dataclass
class ResolvedParameters:
    """Resolved parameters for eventstream operations"""
    workspace_id: str
    auth_token: str
    item_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    operation: Optional[str] = None


class IntelligentEventstreamResolver:
    """Resolves natural language prompts to eventstream operations"""
    
    def __init__(self):
        self.user_context = UserContext()
        self.workspace_patterns = {
            'data analytics': ['analytics', 'data', 'reporting'],
            'production': ['prod', 'production', 'live'],
            'development': ['dev', 'development', 'test', 'staging'],
            'customer': ['customer', 'client', 'user'],
            'sales': ['sales', 'revenue', 'commerce'],
            'marketing': ['marketing', 'campaign', 'promotion']
        }
    
    def parse_natural_language_request(self, prompt: str) -> ResolvedParameters:
        """
        Parse natural language prompt and resolve to eventstream parameters
        
        Examples:
        - "Show me eventstreams in my analytics workspace"
        - "List all eventstreams created this week"
        - "Find eventstreams related to customer data"
        """
        prompt_lower = prompt.lower()
        
        # Determine operation intent
        operation = self._determine_operation(prompt_lower)
        
        # Resolve workspace
        workspace_id, auth_token = self._resolve_workspace_and_auth(prompt_lower)
        
        # Extract filters
        filters = self._extract_filters(prompt_lower)
        
        # Extract specific item if mentioned
        item_id = self._extract_item_id(prompt_lower)
        
        return ResolvedParameters(
            workspace_id=workspace_id,
            auth_token=auth_token,
            item_id=item_id,
            filters=filters,
            operation=operation
        )
    
    def _determine_operation(self, prompt: str) -> str:
        """Determine what operation the user wants to perform"""
        if any(word in prompt for word in ['list', 'show', 'get all', 'find']):
            if 'definition' in prompt or 'details' in prompt or 'configuration' in prompt:
                return 'get_definition'
            return 'list'
        elif any(word in prompt for word in ['create', 'make', 'new']):
            return 'create'
        elif any(word in prompt for word in ['update', 'modify', 'change']):
            return 'update'
        elif any(word in prompt for word in ['delete', 'remove']):
            return 'delete'
        elif any(word in prompt for word in ['definition', 'details', 'configuration']):
            return 'get_definition'
        else:
            return 'list'  # Default to list
    
    def _resolve_workspace_and_auth(self, prompt: str) -> Tuple[str, str]:
        """Intelligently resolve workspace ID and authentication"""
        
        # Try to find workspace in prompt
        workspace_id = self._extract_workspace_from_prompt(prompt)
        
        if not workspace_id:
            # Use context-based resolution
            workspace_id = self._resolve_workspace_from_context(prompt)
        
        if not workspace_id:
            # Fallback to default or ask user
            workspace_id = self.user_context.default_workspace_id
            if not workspace_id:
                raise ValueError("🤔 I couldn't determine which workspace you want to use. Please specify a workspace or set a default.")
        
        # Resolve authentication
        auth_token = self._resolve_authentication()
        
        return workspace_id, auth_token
    
    def _extract_workspace_from_prompt(self, prompt: str) -> Optional[str]:
        """Extract workspace ID from prompt using various patterns"""
        
        # Look for UUID pattern (workspace IDs)
        uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
        uuid_match = re.search(uuid_pattern, prompt, re.IGNORECASE)
        if uuid_match:
            return uuid_match.group(0)
        
        # Look for workspace aliases
        for alias, workspace_id in self.user_context.workspace_aliases.items():
            if alias.lower() in prompt:
                return workspace_id
        
        return None
    
    def _resolve_workspace_from_context(self, prompt: str) -> Optional[str]:
        """Resolve workspace based on context clues in the prompt"""
        
        # Analyze prompt for workspace type hints
        for workspace_type, keywords in self.workspace_patterns.items():
            if any(keyword in prompt for keyword in keywords):
                # Try to find a workspace that matches this pattern
                # This would integrate with your workspace discovery logic
                logger.info(f"🔍 Detected workspace type: {workspace_type}")
                # For now, return the most recent workspace
                if self.user_context.recent_workspaces:
                    return self.user_context.recent_workspaces[0]
        
        return None
    
    def _resolve_authentication(self) -> str:
        """Resolve authentication token intelligently"""
        
        # Check if we have a cached token
        if self.user_context.default_auth_token:
            return self.user_context.default_auth_token
        
        # Try interactive authentication
        try:
            from tools.eventstream_client.auth import get_fabric_token
            token = get_fabric_token()
            if token:
                auth_token = f"Bearer {token}"
                # Cache for this session
                self.user_context.default_auth_token = auth_token
                return auth_token
        except ImportError:
            pass
        
        raise ValueError("🔐 I need authentication to access your Fabric workspace. Please provide a token or set up interactive authentication.")
    
    def _extract_filters(self, prompt: str) -> Dict[str, Any]:
        """Extract filtering criteria from the prompt"""
        filters: Dict[str, Any] = {}
        
        # Time-based filters
        if 'today' in prompt:
            filters['created_after'] = datetime.now().replace(hour=0, minute=0, second=0)
        elif 'this week' in prompt:
            filters['created_after'] = datetime.now() - timedelta(days=7)
        elif 'this month' in prompt:
            filters['created_after'] = datetime.now() - timedelta(days=30)
        elif 'recent' in prompt or 'recently' in prompt:
            filters['created_after'] = datetime.now() - timedelta(days=7)
        
        # Name-based filters
        name_patterns = [
            r'named? ["\']([^"\']+)["\']',
            r'called ["\']([^"\']+)["\']',
            r'with.*name.*["\']([^"\']+)["\']'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                filters['name_contains'] = match.group(1)
                break
        
        # Type/category filters
        if 'customer' in prompt:
            filters['category'] = 'customer'
        elif 'sales' in prompt:
            filters['category'] = 'sales'
        elif 'marketing' in prompt:
            filters['category'] = 'marketing'
        
        return filters
    
    def _extract_item_id(self, prompt: str) -> Optional[str]:
        """Extract specific item ID if mentioned"""
        
        # Look for item ID patterns
        item_patterns = [
            r'item\s+([a-f0-9\-]{36})',
            r'eventstream\s+([a-f0-9\-]{36})',
            r'id\s+([a-f0-9\-]{36})'
        ]
        
        for pattern in item_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def apply_filters(self, results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply intelligent filters to eventstream results"""
        
        if not filters:
            return results
        
        filtered_results = results
        
        # Apply name filter
        if 'name_contains' in filters:
            name_filter = filters['name_contains'].lower()
            filtered_results = [
                item for item in filtered_results
                if name_filter in item.get('displayName', '').lower()
            ]
        
        # Apply time filters (would need creation date in API response)
        if 'created_after' in filters:
            # This would require the API to return creation timestamps
            logger.info(f"🕒 Time filter requested: after {filters['created_after']}")
        
        # Apply category filters
        if 'category' in filters:
            category = filters['category'].lower()
            filtered_results = [
                item for item in filtered_results
                if category in item.get('displayName', '').lower() or
                   category in item.get('description', '').lower()
            ]
        
        return filtered_results


# Global resolver instance
_resolver = IntelligentEventstreamResolver()


def smart_eventstream_operation(prompt: str) -> List[Dict[str, Any]]:
    """
    Main entry point for intelligent eventstream operations
    
    Args:
        prompt: Natural language description of what the user wants to do
        
    Returns:
        Results of the eventstream operation
        
    Examples:
        smart_eventstream_operation("Show me all eventstreams in my analytics workspace")
        smart_eventstream_operation("Find eventstreams created this week")
        smart_eventstream_operation("Get details for the customer data eventstream")
    """
    try:
        # Parse the natural language request
        params = _resolver.parse_natural_language_request(prompt)
        
        logger.info(f"🧠 Resolved operation: {params.operation}")
        logger.info(f"📁 Using workspace: {params.workspace_id}")
        
        # Execute the appropriate operation
        if params.operation == 'list':
            results = eventstream_service.eventstream_list(
                params.workspace_id, 
                params.auth_token
            )
            
            # Apply intelligent filters
            if params.filters:
                results = _resolver.apply_filters(results, params.filters)
                logger.info(f"🔍 Applied filters, {len(results)} results remaining")
            
            return results
            
        elif params.operation == 'get_definition':
            if not params.item_id:
                # If no specific item, try to find it by name or other criteria
                all_items = eventstream_service.eventstream_list(
                    params.workspace_id, 
                    params.auth_token
                )
                
                if params.filters:
                    filtered_items = _resolver.apply_filters(all_items, params.filters)
                    if len(filtered_items) == 1:
                        params.item_id = filtered_items[0]['id']
                    elif len(filtered_items) > 1:
                        return [{
                            "message": f"Found {len(filtered_items)} matching eventstreams. Please be more specific:",
                            "matches": [{"id": item['id'], "name": item.get('displayName', 'Unknown')} for item in filtered_items]
                        }]
                    else:
                        return [{"message": "No eventstreams found matching your criteria"}]
            
            if params.item_id:
                return eventstream_service.eventstream_get_definition(
                    params.workspace_id,
                    params.item_id,
                    params.auth_token
                )
            else:
                return [{"message": "Could not determine which eventstream you want details for. Please specify an item ID or be more specific."}]
        
        else:
            return [{"message": f"Operation '{params.operation}' not yet implemented in smart mode"}]
            
    except Exception as e:
        logger.error(f"❌ Smart eventstream operation failed: {e}")
        return [{"error": str(e), "suggestion": "Try being more specific or use the manual tools"}]


def set_user_context(
    default_workspace_id: Optional[str] = None,
    default_auth_token: Optional[str] = None,
    workspace_aliases: Optional[Dict[str, str]] = None
) -> str:
    """
    Set user context for intelligent operations
    
    Args:
        default_workspace_id: Default workspace to use when not specified
        default_auth_token: Default auth token to use
        workspace_aliases: Map of friendly names to workspace IDs
        
    Returns:
        Confirmation message
    """
    if default_workspace_id:
        _resolver.user_context.default_workspace_id = default_workspace_id
        logger.info(f"🏠 Set default workspace: {default_workspace_id}")
    
    if default_auth_token:
        _resolver.user_context.default_auth_token = default_auth_token
        logger.info("🔐 Set default authentication token")
    
    if workspace_aliases:
        _resolver.user_context.workspace_aliases.update(workspace_aliases)
        logger.info(f"🏷️ Added workspace aliases: {list(workspace_aliases.keys())}")
    
    return "✅ User context updated successfully"


def get_user_context() -> Dict[str, Any]:
    """Get current user context"""
    return {
        "default_workspace_id": _resolver.user_context.default_workspace_id,
        "has_auth_token": bool(_resolver.user_context.default_auth_token),
        "workspace_aliases": _resolver.user_context.workspace_aliases,
        "recent_workspaces": _resolver.user_context.recent_workspaces
    }
