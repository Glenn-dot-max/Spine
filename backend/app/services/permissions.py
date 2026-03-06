"""
Permission helpers for resource ownership verification. 
Reusable across all Spine CRM entities.
"""
from fastapi import HTTPException, status
from typing import Optional, Any

def verify_resource_ownership(
    resource: Optional[Any],
    user_id: int,
    resource_name: str = "Resource"
) -> Any:
    """
    Verify that a resource exists and belongs to the user. 

    Args: 
        resource: The database resource to verify. 
        user_id: The ID of the current user.
        resource_name: The name of the resource type (for error messages).
    
    Returns:
        The resource if ownership is verified.
    
    Raises:
        HTTPException: 404 if resource not found or doesn't belong to user
    
    Note:
        Returns 404 instead of 403 to avoid leaking resource existence.
    """

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} not found"
        )
    
    # Check ownership if resource has user_id attribute
    if hasattr(resource, 'user_id') and resource.user_id != user_id:
        # Return 404 instead of 403 to not leak existence
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} not found"
        )
    
    return resource

def verify_multiple_resources(
        resources: list,
        user_id: int,
        resource_name: str = "Resource"
) -> list:
    """
    Verify that multiple resources belong to the user.
    
    Args:
        resources: List of database resources
        user_id: The current user's ID
        resource_name: Name of the resource type
    
    Returns:
        List of valid resources
    
    Raises:
        HTTPException: 400 if any resource doesn't belong to user
    """

    for resource in resources:
        if hasattr(resource, 'user_id') and resource.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {resource_name} ID: {resource.id}"
            )
        
    return resources