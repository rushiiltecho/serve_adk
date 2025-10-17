"""Authentication service for Google Cloud."""
import logging
from typing import Optional
from google.auth import default
from google.auth.credentials import Credentials
from google.oauth2 import service_account
from core.errors import AuthenticationError

logger = logging.getLogger(__name__)


class AuthService:
    """Handle Google Cloud authentication."""
    
    def __init__(
            self,
            credential: Optional[Credentials] = None
        ):
        self._credentials: Optional[Credentials] = credential
    
    def get_credentials(self) -> Credentials:
        """
        Get Google Cloud credentials.
        
        Priority:
        1. Service account file from GOOGLE_APPLICATION_CREDENTIALS
        2. Default credentials (from environment)
        3. API key for Express Mode
        """
        if self._credentials:
            return self._credentials
        
        try:

            
            # Alternate: Default credentials
            logger.info("Using default credentials")
            credentials, project_id = default(
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            self._credentials = credentials
            return self._credentials
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(f"Failed to authenticate: {str(e)}")
    
    def verify_project_access(self) -> bool:
        """Verify access to the configured project."""
        try:
            credentials = self.get_credentials()
            # Attempt to refresh credentials
            if hasattr(credentials, 'refresh'):
                import google.auth.transport.requests
                request = google.auth.transport.requests.Request()
                credentials.refresh(request)
            return True
        except Exception as e:
            logger.error(f"Project access verification failed: {e}")
            return False


# Global auth service instance
auth_service = AuthService()