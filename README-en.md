# CABM - Code Afflatus & Beyond Matter
## [Meaning and Imagination](docs/meaning.md)
"When spirituality is infused into a vessel, it breaks free from its material shell and reaches a transcendent realm."

~~(Isn't it just a Galgame?)~~

---
> ⚠️This document may not be up to date. Please refer to the [Chinese version](README.md) for the latest information.
---
> ### **⚠️ Note: This project is currently under development. Core features are implemented (maybe?), and other functionalities and optimizations are in progress. Contributions and suggestions are welcome.**

## Development Status
**Bugs to be fixed:**
- (Important) Custom character avatars are blurry
- (Feature) Viewing history mid-sentence displays the complete dialogue
- (Feature) BGM forbidden duet
- (Feature) Story mode does not display previous dialogue upon re-entry
- (Feature) The last sentence waits for options to finish generating before playing
- (Feature) Character files fail to load when loading characters (browser security restrictions)
- (Feature) On Electron, the close logo option is ineffective

**Completed features:**
- Basic AI dialogue functionality, including recent history
- Frontend main page (now sci-fi style)
- Character system (can switch between different characters)
- Segmented streaming output (the soul of the project~)
- Memory system (uses vector database for long-term memory storage)
- AI-generated options
- Simple character actions (breathing)
- Character expressions (might be replaced with 3D models later)
- Custom characters (currently can only add, not edit or delete)
- Story mode (advances the story based on an outline)
- Character knowledge base (backstory, character details, etc.)
- ~~Voice input~~ (currently almost unusable)
- Lots of bugs

**In development:**
- Scene switching (allowing AI to switch scenes or generate new ones)
- Multi-character support in story mode
- Multiple reference audio (using corresponding audio for different moods)
- More preset characters
- Better voice input
- MCP calls
- Improved memory system
- More bugs

## Project Introduction
CABM (Code Afflatus & Beyond Matter) is an immersive dialogue application that integrates advanced AI technologies, allowing users to engage in deep interactions with AI characters and experience emotional storytelling similar to visual novels (Galgame). The project combines large language models, retrieval-augmented generation, voice synthesis, and other technologies to provide:

- **Intelligent Character System**: Each character has a unique personality, backstory, and emotional expression.
- **Dynamic Narrative Experience**: Story mode advances the plot based on user choices.
- **Emotion-Driven Interaction**: Each character has multiple illustrations that adjust in real-time based on emotions.
- **Multimodal Output**: Supports synchronized presentation of text, voice, and expressive illustrations.
- **Long-Term Memory System**: Vector database stores dialogue history, allowing characters to always remember your story.
- **Highly Customizable**: Users can create custom characters.

## Disclaimer
- This project is a personal non-profit interest project with no intention of, and does not participate in, any form of competition within the same industry.
- This project uses the GNU General Public License (GPL) open-source license. Closed-source commercial modifications are prohibited. For details, see [GNU General Public License v3.0](LICENSE).
- Users are responsible for any API costs incurred from calling third-party AI services. Such costs are unrelated to the project author.
- This project involves AI-generated content. The author is not responsible for the accuracy, legality, or any consequences arising from AI-generated content.
- Constructive suggestions and Pull Requests are welcome, but the author reserves the final right to decide whether to adopt them. It is recommended to contact the author in advance.
- The author reserves the final right to interpret and modify the terms of this disclaimer.

## Features

- Natural dialogue with AI models, with streaming output
- Multi-character system, allowing switching between different AI characters
- Dynamically generated background images for an immersive experience
- Dynamic display of character illustrations to enhance visual effects
- Voice synthesis, multimodal output
- Dialogue history viewing
- Responsive design, adaptable to different devices
<a id="install"></a>
## Installation Instructions

### 🎮Method 1: Simple Installation (Windows only)
1. [Click to download the installation package](https://github.com/leletxh/CABM-run/releases/download/v1.1.0/-v1.1.0-win-x64.zip)
2. Extract
3. Double-click "启动器.exe"
4. Go to the [SiliconFlow platform](https://cloud.siliconflow.cn/i/mVqMyTZk) to apply for your API key
5. Fill in your API key in the appearing window (5 places in total)
6. Click confirm
7. Double-click "启动器.exe" again

> Detailed steps for step **4**:
>1.  [Click here](https://cloud.siliconflow.cn/i/mVqMyTZk), then register an account
>2. Click "API Keys" at the bottom left
>3. Click "New API Key" at the top left
>4. Write any description, then click "Create Key"
>5. Click the key to copy it

### 🐳Method 2: Docker Quick Deployment

#### 🚀 Directly Pull Image Deployment (Simplest)

No need to clone the code, use the pre-built image directly:

```bash
# Linux/macOS one-click deployment
curl -o deploy.sh https://raw.githubusercontent.com/leletxh/CABM/main/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

```powershell
# Windows PowerShell one-click deployment
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/leletxh/CABM/main/deploy.ps1" -OutFile "deploy.ps1"
PowerShell -ExecutionPolicy Bypass -File deploy.ps1
```

**[📖 Docker Image Direct Pull Deployment Guide](/docs/DOCKER_PULL_GUIDE.md)**

#### Source Code Build Deployment

```bash
# Clone the project
git clone https://github.com/leletxh/CABM.git
cd CABM
```
> Edit the .env.docker file. You need to apply for your API Key at the [SiliconFlow platform](https://cloud.siliconflow.cn/i/mVqMyTZk)
```bash
# One-click deployment
./deploy-docker.sh deploy
```

#### Manual Deployment

```bash
# 1. Configure environment variables
cp .env.docker .env.docker
```
> Edit the .env.docker file. You need to apply for your API Key at the [SiliconFlow platform](https://cloud.siliconflow.cn/i/mVqMyTZk)
```bash
# 2. Build image
./deploy-docker.sh build

# 3. Run container
./deploy-docker.sh run

# 4. Access the application
# http://localhost:5000
```

**More deployment options:**
- [📖 Docker Image Direct Pull Deployment Guide](/docs/DOCKER_PULL_GUIDE.md)
- [Detailed Deployment Guide](/docs/DOCKER_DEPLOYMENT.md)
- [Issue Solutions](/docs/DOCKER_SOLUTION.md)

#### Docker Management Commands

```bash
./docker-start.sh start      # Start service
./docker-start.sh stop       # Stop service
./docker-start.sh restart    # Restart service
./docker-start.sh logs       # View logs
./docker-start.sh status     # Check status
./docker-start.sh package    # Package image
./docker-start.sh cleanup    # Cleanup resources
```

### 📦Method 3: Traditional Installation (Suitable for Developers)

#### 1. Install Dependencies

Use pip to install project dependencies:

```bash
pip install -r requirements.txt
```

#### 2. Configure Environment Variables

Copy the `.env.example` file to `.env` and fill in the API keys and URLs:

```bash
cp .env.example .env
```
Edit the `.env` file, fill in API_KEY (replace all `your_api_key_here` with your API key).

You need to apply for your API Key at the [SiliconFlow platform](https://cloud.siliconflow.cn/i/mVqMyTZk);
If using other platforms or models, you need to replace the corresponding API_BASE_URL and MODEL.

#### If you have a dedicated GPU, it is recommended to [use GPT-SoVITS for voice synthesis](docs/TTS_GPTSoVITS.md)

### 🚀 Docker Advantages

- **One-click deployment**: No need to manually install dependencies, environment is automatically configured
- **Environment isolation**: Avoids conflicts with other applications
- **Cross-platform**: Supports Linux, Windows, macOS
- **Easy management**: Unified start, stop, restart commands
- **Production-ready**: Includes health checks and automatic restart
- **Resource limits**: Can control memory and CPU usage

### 📋 Environment Requirements

#### Docker Environment
- Docker 20.10+
- Docker Compose 2.0+
- 2GB+ available memory
- 1GB+ available storage space

#### Traditional Environment
- Python 3.8+
- 500MB+ available storage space

## Usage Instructions

### Starting the Application

#### Windows

Double-click the `start.bat` file or run in the command line:
```bash
./start.bat
```

## Node.js Installation and Startup (with UI)

### 1. Install Node.js Dependencies

Please ensure Node.js is installed (recommended 18.x or above), then run in the project root directory:

```bash
npm install
```

### 2. Start the Electron App with UI

Run in the command line:

```bash
npm run electron:start
```

Or run the Electron main program directly:

```bash
node electron/main.js
```

After starting, the main UI will automatically pop up, and the backend service will automatically start and provide APIs at http://localhost:5000.

> If port 5000 is occupied, Electron will automatically connect to the already running service.

### 3. Close the Application

When all windows are closed, the system will automatically notify the backend to exit and close the service.

---
```cmd
start.bat
```

#### Linux/macOS

Ensure the script has execution permissions:

```bash
chmod +x start.sh
```

Then run:

```bash
./start.sh
```

#### Advanced Options

You can also start the script directly with Python and pass additional parameters:

```bash
python start.py --host 127.0.0.1 --port 8080 --debug --no-browser
```

Available parameters:
- `--host`: Specify host address (defaults to value in config file)
- `--port`: Specify port number (defaults to value in config file)
- `--debug`: Enable debug mode
- `--no-browser`: Do not automatically open browser

After starting, the application will automatically open in the browser. The program will intelligently select the most suitable local IP address (preferring addresses starting with 192.168) to ensure normal access in various browsers.

You can also manually access the following addresses:
- Local access: `http://localhost:5000` or `http://127.0.0.1:5000`
- LAN access: `http://[your local IP]:5000` (the specific address will be displayed at startup)

### Basic Operations

- **Send message**: Enter a message in the input box at the top right, click the "Send" button or press Enter to send
- **View history**: Click the "History" button to view the complete dialogue history
- **Play voice**: Click the "Play Voice" button to play the voice again
- **Change background**: Click the "Change Background" button to select a background or generate a new background image

## Notes

- Mobile access is possible, but the layout may have issues

## Custom Characters
You can now customize characters in the frontend UI. You need to prepare:
- The character's **background-free** illustration (if there are multiple, try to keep the character size consistent)
- The character's introduction (including one for humans and one for AI)
- A line of the character's voice and its text, 3-10 seconds (to use the voice feature)
- The character's detailed information, backstory, etc., needs to be organized as required (optional)

## Contribution
> Note: Not being paid weekly doesn't mean there isn't any

[![Contributors](https://img.shields.io/github/contributors/xhc2008/CABM?color=blue)](https://github.com/xhc2008/CABM/graphs/contributors)

![Contributors](https://contrib.rocks/image?repo=xhc2008/CABM)

Welcome to submit Pull Requests or Issues! ~~(but not necessarily acted upon)~~

For specific contribution process, please refer to [CONTRIBUTING.md](CONTRIBUTING.md)

## 📚 Documentation Index

### Deployment Documentation
- [📖 Docker Image Direct Pull Deployment Guide](docs/DOCKER_PULL_GUIDE.md) - **Recommended: No source code needed, directly pull image for deployment**
- [Docker Deployment Guide](docs/DOCKER_DEPLOY_GUIDE.md) - Complete Docker deployment guide
- [Docker Deployment Plan](docs/DOCKER_DEPLOYMENT.md) - Detailed Docker deployment instructions
- [Windows Deployment Guide](docs/WINDOWS_DEPLOY_GUIDE.md) - Windows environment deployment
- [Docker Issue Solutions](docs/DOCKER_SOLUTION.md) - Common issues and solutions

### Functional Documentation
- [TTS GPT-SoVITS Configuration](docs/TTS_GPTSoVITS.md) - Voice synthesis service configuration

### Development Documentation
- [Contribution Guide](CONTRIBUTING.md) - How to participate in project development

## License

[GNU General Public License v3.0](LICENSE)

<br />
<br />
<br />
<br />

# Congratulations on reading the entire README! Here's your Easter egg.
[Easter egg](https://genshin.hoyoverse.com/en/)