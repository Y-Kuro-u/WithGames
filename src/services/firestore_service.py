"""
Firestore service for WithGames Discord Bot.
Handles all Firestore database operations with error handling and retry logic.
"""
import logging
from typing import Optional, List, Dict, Any
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from google.api_core import retry, exceptions
from src.config import config

logger = logging.getLogger(__name__)


class FirestoreService:
    """Service class for Firestore operations."""

    def __init__(self):
        """Initialize Firestore client."""
        try:
            if config.use_firestore_emulator:
                logger.info(
                    f"Connecting to Firestore Emulator at {config.firestore_emulator_host}"
                )
                self.db = firestore.Client(project=config.gcp_project_id)
            else:
                logger.info(
                    f"Connecting to Firestore in project: {config.gcp_project_id}"
                )
                self.db = firestore.Client(project=config.gcp_project_id)

            logger.info("Firestore client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise

    # Collection references
    @property
    def events_collection(self):
        """Get events collection reference."""
        return self.db.collection("events")

    @property
    def participants_collection(self):
        """Get participants collection reference."""
        return self.db.collection("participants")

    @property
    def game_types_collection(self):
        """Get game_types collection reference."""
        return self.db.collection("game_types")

    # CRUD Operations
    @retry.Retry(predicate=retry.if_exception_type(exceptions.ServiceUnavailable))
    def create_document(
        self, collection_name: str, data: Dict[str, Any], doc_id: Optional[str] = None
    ) -> str:
        """Create a new document in a collection.

        Args:
            collection_name: Name of the collection
            data: Document data
            doc_id: Optional document ID (auto-generated if not provided)

        Returns:
            Document ID

        Raises:
            Exception: If document creation fails
        """
        try:
            collection_ref = self.db.collection(collection_name)

            if doc_id:
                doc_ref = collection_ref.document(doc_id)
                doc_ref.set(data)
                logger.info(f"Created document {doc_id} in {collection_name}")
                return doc_id
            else:
                _, doc_ref = collection_ref.add(data)
                logger.info(f"Created document {doc_ref.id} in {collection_name}")
                return doc_ref.id

        except Exception as e:
            logger.error(f"Failed to create document in {collection_name}: {e}")
            raise

    @retry.Retry(predicate=retry.if_exception_type(exceptions.ServiceUnavailable))
    def get_document(
        self, collection_name: str, doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a document by ID.

        Args:
            collection_name: Name of the collection
            doc_id: Document ID

        Returns:
            Document data or None if not found
        """
        try:
            doc_ref = self.db.collection(collection_name).document(doc_id)
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                data["id"] = doc.id
                return data
            else:
                logger.warning(
                    f"Document {doc_id} not found in {collection_name}"
                )
                return None

        except Exception as e:
            logger.error(
                f"Failed to get document {doc_id} from {collection_name}: {e}"
            )
            raise

    @retry.Retry(predicate=retry.if_exception_type(exceptions.ServiceUnavailable))
    def update_document(
        self, collection_name: str, doc_id: str, data: Dict[str, Any]
    ):
        """Update a document.

        Args:
            collection_name: Name of the collection
            doc_id: Document ID
            data: Data to update

        Raises:
            Exception: If document update fails
        """
        try:
            doc_ref = self.db.collection(collection_name).document(doc_id)
            doc_ref.update(data)
            logger.info(f"Updated document {doc_id} in {collection_name}")

        except Exception as e:
            logger.error(
                f"Failed to update document {doc_id} in {collection_name}: {e}"
            )
            raise

    @retry.Retry(predicate=retry.if_exception_type(exceptions.ServiceUnavailable))
    def delete_document(self, collection_name: str, doc_id: str):
        """Delete a document.

        Args:
            collection_name: Name of the collection
            doc_id: Document ID

        Raises:
            Exception: If document deletion fails
        """
        try:
            doc_ref = self.db.collection(collection_name).document(doc_id)
            doc_ref.delete()
            logger.info(f"Deleted document {doc_id} from {collection_name}")

        except Exception as e:
            logger.error(
                f"Failed to delete document {doc_id} from {collection_name}: {e}"
            )
            raise

    @retry.Retry(predicate=retry.if_exception_type(exceptions.ServiceUnavailable))
    def query_documents(
        self,
        collection_name: str,
        filters: Optional[List[tuple]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query documents from a collection.

        Args:
            collection_name: Name of the collection
            filters: List of filter tuples (field, operator, value)
            order_by: Field to order by
            limit: Maximum number of results

        Returns:
            List of documents
        """
        try:
            query = self.db.collection(collection_name)

            if filters:
                for field, operator, value in filters:
                    query = query.where(filter=FieldFilter(field, operator, value))

            if order_by:
                query = query.order_by(order_by)

            if limit:
                query = query.limit(limit)

            docs = query.stream()

            results = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)

            logger.info(
                f"Queried {len(results)} documents from {collection_name}"
            )
            return results

        except Exception as e:
            logger.error(f"Failed to query documents from {collection_name}: {e}")
            raise

    @firestore.transactional
    def transaction_update(
        self, transaction, collection_name: str, doc_id: str, data: Dict[str, Any]
    ):
        """Update a document within a transaction.

        Args:
            transaction: Firestore transaction
            collection_name: Name of the collection
            doc_id: Document ID
            data: Data to update
        """
        doc_ref = self.db.collection(collection_name).document(doc_id)
        transaction.update(doc_ref, data)

    def run_transaction(self, callback):
        """Run a Firestore transaction.

        Args:
            callback: Transaction callback function

        Returns:
            Transaction result
        """
        try:
            transaction = self.db.transaction()
            result = callback(transaction)
            logger.info("Transaction completed successfully")
            return result

        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise

    def test_connection(self) -> bool:
        """Test Firestore connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to list collections (lightweight operation)
            collections = list(self.db.collections())
            logger.info("Firestore connection test successful")
            return True
        except Exception as e:
            logger.error(f"Firestore connection test failed: {e}")
            return False


# Global service instance
firestore_service = FirestoreService()
