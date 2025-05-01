import firebase_admin
from firebase_admin import storage
import datetime # Needed for getting a timestamp for the filename

# Initialize the Admin SDK.
# In a standard Cloud Functions environment, this often picks up credentials automatically.
# For local development or other environments, you might need to provide credentials explicitly.
if not firebase_admin._apps: # Check if app is already initialized
    firebase_admin.initialize_app()

# Get the default Storage bucket for the project
try:
    bucket = storage.bucket(name="amazingstocks-9829a.firebasestorage.app")
    print(f"Successfully connected to default bucket: {bucket.name}")
except Exception as e:
    print(f"Error connecting to storage bucket: {e}")
    bucket = None # Ensure bucket is None if connection fails


def save_file_from_python_function():
    """
    HTTP Cloud Function that saves a simple text file to Firebase Storage.
    """
    if bucket is None:
        print("Bucket is not initialized. Exiting function.")
        return

    # Generate a unique filename using a timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f'python_greeting_{timestamp}.txt'
    file_path = f'greetings_from_python/{file_name}' # Path within the bucket

    file_content = f"Hello from your Python Cloud Function! Current time: {datetime.datetime.now().isoformat()}"

    try:
        # Get a reference to the file (blob) in the bucket
        file_ref = bucket.blob(file_path)

        # Upload the string content to the file
        file_ref.upload_from_string(file_content, content_type='text/plain')

        print(f"Successfully saved file to gs://{bucket.name}/{file_path}")


    except Exception as e:
        print(f"Error saving file from Python function: {e}")

if __name__ == "__main__":
    # This block is for local testing. In a real Cloud Function, this would be triggered by an HTTP request.
    save_file_from_python_function()