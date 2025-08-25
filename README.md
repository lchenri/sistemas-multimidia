# Alunos
Leonorico Eduardo de Paula Borges 202135032
Lucas Henrique de Araújo Cardoso 202135038
Pedro Andrade Pereira Leão 202035008

# Sistemas Multimídia

Um projeto Django que implementa funcionalidades de streaming de vídeo e processamento multimídia usando WebSockets.

## 📋 Descrição

Este projeto é uma aplicação web Django que utiliza Django Channels para comunicação em tempo real via WebSockets, permitindo streaming de vídeo e outras funcionalidades multimídia. O projeto inclui processamento de imagem com OpenCV e machine learning com TensorFlow/Keras.

## 🔧 Tecnologias Utilizadas

- **Django 4.1** - Framework web principal
- **Django Channels 4.0.0** - Para WebSockets e comunicação assíncrona
- **Daphne 2.5.0** - Servidor ASGI para suporte a WebSockets
- **OpenCV 4.5.3.56** - Processamento de imagem e vídeo
- **TensorFlow 2.7.2** - Machine learning
- **Keras 2.7.0** - API de alto nível para deep learning
- **NumPy** - Computação numérica
- **Pillow** - Manipulação de imagens
- **SQLite** - Banco de dados (padrão para desenvolvimento)

## 📹 Streaming de Webcam - Arquitetura Técnica

### Como Funciona o Streaming em Tempo Real

O projeto implementa um sistema de streaming de webcam usando uma arquitetura cliente-servidor baseada em **WebSockets** para comunicação bidirecional em tempo real. Aqui está o fluxo técnico completo:

#### 1. **Captura no Cliente (JavaScript)**
- O navegador acessa a webcam do usuário via **MediaDevices API** (`navigator.mediaDevices.getUserMedia`)
- Os frames de vídeo são capturados em um elemento `<canvas>` HTML5
- Cada frame é convertido para **Base64** usando `canvas.toDataURL()`
- Os dados são enviados via WebSocket para o servidor

#### 2. **Processamento no Servidor (Python)**
O `VideoStreamConsumer` (localizado em `server/views.py`) processa os frames:
```python 
class VideoStreamConsumer(AsyncWebsocketConsumer):
    async def receive(self, text_data): 
        # Recebe dados Base64 do cliente 
        # Decodifica para formato de imagem 
        # Processa com OpenCV (cv2) 
        # Pode aplicar filtros, detecção de objetos, etc. 
        # Envia frame processado de volta
``` 

#### 3. **Fluxo de Dados**
```
[Webcam] → [JavaScript] → [Base64] → [WebSocket] → [Django Channels] ↓ [VideoStreamConsumer] → [OpenCV Processing] → [Base64] → [WebSocket] → [Cliente] ↓ [Display no navegador]
``` 

#### 4. **Configuração ASGI**
O arquivo `asgi.py` configura o roteamento para WebSockets:
- **HTTP**: Requisições tradicionais Django
- **WebSocket**: Streaming de vídeo via `VideoStreamConsumer`
- **Autenticação**: Middleware para validação de origem

#### 5. **Vantagens da Arquitetura Escolhida**

**WebSockets vs HTTP tradicional:**
- ✅ **Baixa latência**: Conexão persistente sem overhead de headers
- ✅ **Bidirecional**: Servidor pode enviar dados sem requisição
- ✅ **Tempo real**: Ideal para streaming contínuo
- ✅ **Eficiência**: Menos bandwidth que requisições HTTP repetidas

**OpenCV Integration:**
- ✅ **Processamento em tempo real**: Filtros, detecção facial, etc.
- ✅ **Flexibilidade**: Qualquer algoritmo de visão computacional
- ✅ **Performance**: Processamento nativo em C++ via Python bindings

#### 6. **Considerações de Performance**
- **Compressão**: Frames são comprimidos em JPEG antes da transmissão
- **Buffer Management**: Django Channels gerencia automaticamente buffers
- **Async Processing**: `AsyncWebsocketConsumer` permite múltiplas conexões simultâneas
- **Memory Efficiency**: Frames são processados e descartados imediatamente

Quanto aos conceitos de **Sistemas Multimídia**, demonstra ideias fundamentais como:
- Captura e processamento de mídia em tempo real
- Protocolos de comunicação multimídia
- Compressão e transmissão de dados audiovisuais
- Integração de bibliotecas de visão computacional

## 🚀 Configuração e Instalação

### Pré-requisitos

- Python 3.9.23
- pyenv (gerenciador de pacotes Python configurado)

### Passos de Instalação

1. **Clone o repositório**
   ```bash
   git clone <url-do-repositorio>
   cd SistemasMultimidia
   ```

2. **Ative o ambiente virtual**
   ```bash
   source .venv/bin/activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute as migrações do banco de dados**
   ```bash
   python manage.py migrate
   ```


## 🎯 Como Executar

### Servidor de Desenvolvimento

**⚠️ IMPORTANTE: Este projeto deve ser executado com Daphne (não com o servidor padrão do Django)**
```
bash daphne SistemasMultimidia.asgi:application --port 8000 --bind 127.0.0.1
``` 

### Por que usar Daphne?

O Daphne é necessário porque este projeto utiliza:
- **Django Channels** para WebSockets
- **Comunicação assíncrona** em tempo real
- **Streaming de vídeo** via WebSocket (`VideoStreamConsumer`)

O servidor padrão do Django (`python manage.py runserver`) não suporta protocolos ASGI, apenas WSGI, por isso é necessário usar um servidor ASGI como o Daphne.

### Acessando a Aplicação

Após executar o comando acima, acesse:
- **URL principal**: http://127.0.0.1:8000
- **Admin Django**: http://127.0.0.1:8000/admin

## 📁 Estrutura do Projeto
```
SistemasMultimidia/ 
├── SistemasMultimidia/ # Configurações do projeto 
│ ├── settings.py # Configurações Django 
│ ├── asgi.py # Configuração ASGI para WebSockets 
│ └── urls.py # URLs principais 
├── server/ # App principal 
│ ├── views.py # Views e VideoStreamConsumer 
│ ├── urls.py # URLs do app 
│ ├── models.py # Modelos do banco de dados 
│ └── templates/ # Templates HTML 
├── templates/ # Templates globais 
├── requirements.txt # Dependências Python 
├── manage.py # Utilitário Django 
└── db.sqlite3 # Banco de dados SQLite
``` 

## 🔌 Funcionalidades Principais

- **Streaming de Vídeo**: Implementado via WebSocket com `VideoStreamConsumer`
- **Processamento de Imagem**: Usando OpenCV para manipulação de vídeo
- **Machine Learning**: Integração com TensorFlow/Keras
- **Interface Web**: Templates responsivos
- **Comunicação em Tempo Real**: Via Django Channels

## 🛠️ Comandos Úteis
```
bash
# Criar superusuário
python manage.py createsuperuser
# Executar testes
python manage.py test
# Executar shell Django
python manage.py shell
# Verificar configuração
python manage.py check
```
