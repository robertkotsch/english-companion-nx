import sys
import os

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

try:
    import notion_client
    print(f"\nnotion_client file: {notion_client.__file__}")
    try:
        print(f"notion_client version: {notion_client.__version__}")
    except AttributeError:
        print("notion_client has no __version__ attribute")

    from notion_client import Client
    client = Client(auth="secret_dummy")
    print(f"\nclient.databases type: {type(client.databases)}")
    print(f"client.databases dir: {dir(client.databases)}")
    
    if hasattr(client.databases, 'query'):
        print("\n✅ client.databases.query exists")
    else:
        print("\n❌ client.databases.query MISSING")

except ImportError:
    print("\n❌ notion-client not installed")
except Exception as e:
    print(f"\n❌ Error: {e}")
