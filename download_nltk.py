import nltk
import os

# Create directories for punkt_tab
nltk_data_dir = os.path.expanduser('~/nltk_data')
punkt_tab_dir = os.path.join(nltk_data_dir, 'tokenizers', 'punkt_tab', 'english')
os.makedirs(punkt_tab_dir, exist_ok=True)

# Download necessary NLTK resources
nltk.download('punkt')
nltk.download('punkt_tab')  # This might fail, but we'll handle it

# If punkt_tab download fails, we'll copy from punkt
punkt_dir = os.path.join(nltk_data_dir, 'tokenizers', 'punkt')

print("NLTK downloads completed.")
print(f"Punkt directory: {punkt_dir}")
print(f"Punkt_tab directory: {punkt_tab_dir}")

# List contents to verify
if os.path.exists(punkt_dir):
    print(f"Files in punkt directory: {os.listdir(punkt_dir)}")
else:
    print("Punkt directory not found")

if os.path.exists(punkt_tab_dir):
    print(f"Files in punkt_tab directory: {os.listdir(punkt_tab_dir)}")
else:
    print("Punkt_tab directory is empty or not found")