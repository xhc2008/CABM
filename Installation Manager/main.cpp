#include <iostream>
#include <string>
#include <vector>
#include <Windows.h>
#include <direct.h>
#include <fstream>
#include <wininet.h>
#pragma comment(lib, "wininet.lib")

using namespace std;

void printHelp() {
    cout << "CABM Installation Manager" << endl;
    cout << "Usage:" << endl;
    cout << "  install [options]         - Install CABM environment" << endl;
    cout << "  use <command>            - Run command in CABM environment" << endl;
    cout << "Options:" << endl;
    cout << "  all                       - Install everything (default)" << endl;
    cout << "  --use-local-conda        - Skip Miniforge installation" << endl;
    cout << "  --use-local-python       - Use local Python, only install requirements" << endl;
    cout << endl;
    cout << "Examples:" << endl;
    cout << "  main.exe install" << endl;
    cout << "  main.exe use python run.py" << endl;
    cout << endl;
}

bool downloadFile(const string& url, const string& filePath) {
    HINTERNET hInternet = InternetOpen("CABM_Installer", INTERNET_OPEN_TYPE_DIRECT, NULL, NULL, 0);
    if (!hInternet) return false;

    HINTERNET hConnect = InternetOpenUrl(hInternet, url.c_str(), NULL, 0, INTERNET_FLAG_RELOAD, 0);
    if (!hConnect) {
        InternetCloseHandle(hInternet);
        return false;
    }

    FILE* file = fopen(filePath.c_str(), "wb");
    if (!file) {
        InternetCloseHandle(hConnect);
        InternetCloseHandle(hInternet);
        return false;
    }

    char buffer[1024];
    DWORD bytesRead;
    
    while (InternetReadFile(hConnect, buffer, sizeof(buffer), &bytesRead) && bytesRead > 0) {
        fwrite(buffer, 1, bytesRead, file);
    }

    fclose(file);
    InternetCloseHandle(hConnect);
    InternetCloseHandle(hInternet);
    return true;
}

bool executeCommand(const string& command) {
    STARTUPINFO si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    ZeroMemory(&pi, sizeof(pi));
    si.cb = sizeof(si);

    char cmdLine[1024];
    strncpy(cmdLine, command.c_str(), sizeof(cmdLine) - 1);
    cmdLine[sizeof(cmdLine) - 1] = '\0';

    if (!CreateProcess(NULL, cmdLine, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
        return false;
    }

    WaitForSingleObject(pi.hProcess, INFINITE);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    return true;
}

void install(bool skipConda = false, bool useLocalPython = false) {
    string miniforgeUrl = "https://mirror.nju.edu.cn/github-release/conda-forge/miniforge/LatestRelease/Miniforge3-25.3.1-0-Windows-x86_64.exe";
    string installerPath = "miniforge_installer.exe";
    
    if (!skipConda && !useLocalPython) {
        cout << "Downloading Miniforge..." << endl;
        if (!downloadFile(miniforgeUrl, installerPath)) {
            cout << "Failed to download Miniforge" << endl;
            return;
        }

        cout << "Installing Miniforge..." << endl;
        string installCommand = installerPath + " /S /RegisterPython=0 /AddToPath=0 /InstallationType=JustMe";
        if (!executeCommand(installCommand)) {
            cout << "Failed to install Miniforge" << endl;
            return;
        }
    }

    if (!useLocalPython) {
        cout << "Creating Python 3.10 environment..." << endl;
        char* userProfile = getenv("USERPROFILE");
        string condaPath = userProfile ? string(userProfile) + "\\.conda" : ".conda";
        string createEnvCommand = "conda create -n cabm python=3.10 -y";
        if (!executeCommand(createEnvCommand.c_str())) {
            cout << "Failed to create Python environment" << endl;
            return;
        }

        cout << "Installing requirements..." << endl;
        string installReqCommand = "cmd /C \"conda activate cabm && pip install -r requirements.txt\"";
        if (!executeCommand(installReqCommand.c_str())) {
            cout << "Failed to install requirements" << endl;
            return;
        }
    } else {
        cout << "Installing requirements using local Python..." << endl;
        if (!executeCommand("pip install -r requirements.txt")) {
            cout << "Failed to install requirements" << endl;
            return;
        }
    }

    cout << "Installation completed successfully!" << endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printHelp();
        return 0;
    }

    string command = argv[1];
    
    if (command == "install") {
        bool skipConda = false;
        bool useLocalPython = false;
        
        for (int i = 2; i < argc; i++) {
            string arg = argv[i];
            if (arg == "--use-local-conda") skipConda = true;
            if (arg == "--use-local-python") useLocalPython = true;
        }

        install(skipConda, useLocalPython);
    } else if (command == "use" && argc > 2) {
        // 拼接后续命令
        string userCmd;
        for (int i = 2; i < argc; i++) {
            if (i > 2) userCmd += " ";
            userCmd += argv[i];
        }
        // 激活conda环境并执行
        string fullCmd = "cmd /C \"conda activate cabm && " + userCmd + "\"";
        cout << "[CABM] 执行: " << userCmd << endl;
        if (!executeCommand(fullCmd)) {
            cout << "命令执行失败。" << endl;
        }
    } else {
        printHelp();
    }

    return 0;
}