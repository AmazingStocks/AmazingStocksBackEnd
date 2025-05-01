
from firebase_admin import credentials, firestore



# Initialize Firestore client
firestore_client = firestore.Client()

def create_document(collection_name, document_id, data):
    """
    Create a Firestore document with the provided data and cleanup after creation.
    """
    try:
        doc_ref = firestore_client.collection(collection_name).document(document_id)
        doc_ref.set(data)
        print(f"Document {document_id} created successfully in collection {collection_name}.")
    except Exception as e:
        print(f"Error creating document {document_id} in collection {collection_name}: {e}")
    finally:
        # Cleanup: no explicit close is required for Firestore documents,
        # but we reset the reference as part of the operation.
        doc_ref = None
    


def update_document(collection_name, document_id, data):
    """
    Update a Firestore collection with the provided data.
    """
    try:
        doc_ref = firestore_client.collection(collection_name).document(document_id)
        doc_ref.set(data, merge=True)
    except Exception as e:
        print(f"Error updating document {document_id} in collection {collection_name}: {e}")
    finally:
        # Cleanup: no explicit close is required for Firestore documents,
        # but we reset the reference as part of the operation.
        doc_ref = None
        

def get_collection(collection_name):
    """
    Retrieve all documents from a Firestore collection.
    """
    try:
        collection_ref = firestore_client.collection(collection_name)
        docs = collection_ref.stream()
        return {doc.id: doc.to_dict() for doc in docs}
    except Exception as e:
        print(f"Error retrieving collection {collection_name}: {e}")
        return {}
    
def get_document(collection_name, document_id): 
    """
    Retrieve a specific document from a Firestore collection.
    """
    try:
        doc_ref = firestore_client.collection(collection_name).document(document_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            print(f"Document {document_id} does not exist in collection {collection_name}.")
            return None
    except Exception as e:
        print(f"Error retrieving document {document_id} from collection {collection_name}: {e}")
        return None
    
def delete_document(collection_name, document_id):      
    """
    Delete a specific document from a Firestore collection.
    """
    try:
        doc_ref = firestore_client.collection(collection_name).document(document_id)
        doc_ref.delete()
        print(f"Document {document_id} deleted successfully from collection {collection_name}.")
    except Exception as e:
        print(f"Error deleting document {document_id} from collection {collection_name}: {e}")
        return False
    return True

def delete_collection(collection_name):
    """
    Delete all documents in a Firestore collection.
    """ 
    try:
        collection_ref = firestore_client.collection(collection_name)
        docs = collection_ref.stream()
        for doc in docs:
            doc.reference.delete()
        print(f"All documents deleted successfully from collection {collection_name}.")
    except Exception as e:
        print(f"Error deleting collection {collection_name}: {e}")
        return False
    return True