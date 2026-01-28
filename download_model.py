from llama_cpp import Llama

print("Downloading Moondream2 model...")
# Attempt to download the text model
model_path = Llama.from_pretrained(
    repo_id="moondream/moondream2-gguf",
    filename="*text-model-Q4_K_M.gguf",
    local_dir="models"
)
print(f"Model downloaded to: {model_path}")

print("Downloading Moondream2 projector...")
# Attempt to download the mmproj file (vision adapter)
mmproj_path = Llama.from_pretrained(
    repo_id="moondream/moondream2-gguf",
    filename="*mmproj-f16.gguf",
    local_dir="models"
)
print(f"Projector downloaded to: {mmproj_path}")
